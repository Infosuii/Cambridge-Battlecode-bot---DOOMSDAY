"""Eliminate redundant foreign-camp lookups in the exact camp-strike search."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

from bounded_verdict import apply
from large_roster_stress import DENSE_OUT as STRESS, HERE, bench, native_fuel, read
from pg_siege_resume import prepare as prepare_resume


def prepare(src, enabled):
    prepare_resume(src, enabled)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_PG_CAMP_STRIKE {int(enabled)}".encode() + nl + data)
    apply(src / "bot.cpp", (
        ("        int best_hits = 0, best_home = kUnreach;",
         """#if CODEX_PG_CAMP_STRIKE
        std::vector<vec2> foreign_camps;
        bool foreign_camps_ready = false;
#endif
        int best_hits = 0, best_home = kUnreach;"""),
        ("""            bool extra_group = false;
            for (int x = -radius; x <= radius; ++x) for (int y = -radius; y <= radius; ++y) {
                const int other = w.group_of_camp_tile({q.x + x, q.y + y});
                if (other >= 0 && other != gi && w.groups[static_cast<std::size_t>(other)].state == GroupState::alive) extra_group = true;
            }
            if (extra_group) continue;""",
         """#if CODEX_PG_CAMP_STRIKE
            if (!foreign_camps_ready) {
                // Every landing is within radius of the target. A camp outside twice that radius cannot be hit.
                for (int x = -2 * radius; x <= 2 * radius; ++x) for (int y = -2 * radius; y <= 2 * radius; ++y) {
                    const vec2 p{target.pos.x + x, target.pos.y + y};
                    const int other = w.group_of_camp_tile(p);
                    if (other >= 0 && other != gi && w.groups[static_cast<std::size_t>(other)].state == GroupState::alive)
                        foreign_camps.push_back(p);
                }
                foreign_camps_ready = true;
            }
            if (std::any_of(foreign_camps.begin(), foreign_camps.end(), [&](vec2 p) { return cheb(p, q) <= radius; })) continue;
#else
            bool extra_group = false;
            for (int x = -radius; x <= radius; ++x) for (int y = -radius; y <= radius; ++y) {
                const int other = w.group_of_camp_tile({q.x + x, q.y + y});
                if (other >= 0 && other != gi && w.groups[static_cast<std::size_t>(other)].state == GroupState::alive) extra_group = true;
            }
            if (extra_group) continue;
#endif"""),
    ))


def verify(wasm):
    name = "pg-camp-strike"
    profile = read(HERE / "DENSE_ROSTER_PROFILE.json")
    key = lambda r: (r["map"], r["opponent"], r["side"])
    targets = {key(r): {tuple(v) for v in r["matched_native"]} for r in profile["matches"] if "camp_dash_done" in r["phases"]}
    assert len(targets) == 5 and len({m for m, _, _ in targets}) == 2
    stress = {key(r): r for r in read(STRESS / "rows.json")}
    baseline = [stress[key(r)] for r in profile["rows"]]
    manifest = read(HERE / "DENSE_ROSTER_MAPS.json")["maps"]
    maps = {p.stem: p for p in (STRESS / "maps").glob("*.map26a")}
    for r in baseline:
        assert bench.digest(maps[r["map"]]) == manifest[maps[r["map"]].name]
        file, expected = bench.OPPS[r["opponent"]]
        assert bench.digest(bench.CACHE / file) == expected
    bench.OUT = bench.CACHE / f"{name}-exact-stress"
    (bench.OUT / "games").mkdir(parents=True)
    jobs = [("exact", 0, r["opponent"], maps[r["map"]], r["side"], wasm) for r in baseline]
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(bench.one, jobs))
    unresolved = []
    for b, c in zip(baseline, rows, strict=True):
        assert all(b[k] == c[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
        for e in native_fuel(c, bench.OUT):
            event = e["owner"]["name"], e["timestamp"]["round"]
            if event in targets.get(key(c), ()):
                unresolved.append({"cell": key(c), "event": event})
    increased = [key(c) for b, c in zip(baseline, rows, strict=True) if c["fuel_outs"] > b["fuel_outs"]]
    errors = sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows)
    fuel = [sum(r["fuel_outs"] for r in group) for group in (baseline, rows)]
    result = {"engine": bench.ENGINE, "sha256": bench.digest(wasm), "n": len(rows), "fuel": fuel,
              "registered_events": [{"cell": cell, "events": sorted(v)} for cell, v in sorted(targets.items())],
              "unresolved": unresolved, "increased": increased, "error_cells": errors,
              "pass": not unresolved and not increased and not errors and fuel[1] < fuel[0]}
    with (HERE / "PG-CAMP-STRIKE_EXACT_STRESS.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "baseline": baseline, "candidate": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--src", type=Path)
    target.add_argument("--verify", type=Path)
    parser.add_argument("--off", action="store_true")
    args = parser.parse_args()
    if args.src:
        prepare(args.src, not args.off)
    else:
        verify(args.verify)
