"""Apply the existing tail guard and verify the independent exact stress fixture."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re

from large_roster_stress import HERE, OUT as STRESS, bench, read
from pg_ambush_guard import prepare as prepare_ambush
from pg_tail_guard import add_guard


def verify(wasm, name, phases):
    profile = read(HERE / "LARGE_ROSTER_COARSE.json")
    key = lambda r: (r["map"], r["opponent"], r["side"])
    by_cell = {key(r): r for r in read(STRESS / "rows.json")}
    baseline = [by_cell[key(r)] for r in profile["rows"]]
    targets = {}
    for join in profile["joins"]:
        rounds = {int(re.search(r" R(\d+)", value).group(1)) for phase, value in join["examples"].items() if phase in phases}
        selected = {(champion, rnd) for champion, rnd in join["matched_native"] if rnd in rounds}
        if selected:
            targets[key(join)] = selected
    assert len({map_name for map_name, _, _ in targets}) >= 2
    maps = {p.stem: p for p in (STRESS / "maps").glob("*.map26a")}
    manifest = read(HERE / "LARGE_ROSTER_MAPS.json")["maps"]
    for r in baseline:
        mp = maps[r["map"]]
        assert bench.digest(mp) == manifest[mp.name]
        file, expected = bench.OPPS[r["opponent"]]
        assert bench.digest(bench.CACHE / file) == expected
    bench.OUT = bench.CACHE / f"{name}-exact-stress"
    (bench.OUT / "games").mkdir(parents=True)
    jobs = [("exact", 0, r["opponent"], maps[r["map"]], r["side"], wasm) for r in baseline]
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(bench.one, jobs))
    for b, c in zip(baseline, rows, strict=True):
        assert all(b[k] == c[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
    unresolved = []
    for r in rows:
        if key(r) not in targets:
            continue
        case = bench.OUT / "games" / f"exact-0-{r['opponent']}-{r['map']}-{r['side']}"
        native = read(case / "native.json")
        events = {(e["owner"]["name"], x["timestamp"]["round"]) for e in native["events"]
                  if e["kind"] == "fuelExhausted" and e["owner"]["team"] == "team" + r["side"] for x in e["entries"]}
        for event in sorted(events & targets[key(r)]):
            unresolved.append({"cell": key(r), "event": event})
    fuel = [sum(r["fuel_outs"] for r in group) for group in (baseline, rows)]
    increased = [key(c) for b, c in zip(baseline, rows, strict=True) if c["fuel_outs"] > b["fuel_outs"]]
    errors = sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows)
    result = {"engine": bench.ENGINE, "sha256": bench.digest(wasm), "n": len(rows), "fuel": fuel,
              "expected_events": [{"cell": cell, "events": sorted(v)} for cell, v in sorted(targets.items())],
              "unresolved": unresolved, "increased": increased, "error_cells": errors,
              "pass": not unresolved and not increased and not errors and fuel[1] < fuel[0]}
    with (HERE / f"{name.upper()}_EXACT_STRESS.json").open("x", encoding="utf8", newline="\n") as out:
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
        prepare_ambush(args.src, not args.off)
        add_guard(args.src, not args.off)
    else:
        verify(args.verify, "pg-stress-tail", {"tail"})
