"""Keep a completed dash without spending the walking reserve on its next step."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
from zipfile import ZipFile

from bounded_verdict import apply
from large_roster_stress import DENSE_OUT as DENSE, HERE, OUT as STRESS, bench, native_fuel, read
from pg_camp_reserve import prepare as prepare_reserve
from trace_post_cast import CASES


def prepare(src, enabled, escape_only=False):
    prepare_reserve(src, enabled)
    header = src / "common.h"
    data = header.read_bytes()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    header.write_bytes(f"#define CODEX_PG_DASH_FOLLOWUP {int(enabled)}".encode() + nl + data)
    if not escape_only:
        apply(src / "bot.cpp", (("    if (allow_dash) try_dash(field, blocked);", """#if CODEX_PG_DASH_FOLLOWUP
    if (allow_dash && try_dash(field, blocked) && !rb::fits(0, X1_WALK_RESERVE)) return true;
#else
    if (allow_dash) try_dash(field, blocked);
#endif"""),
        ))
    apply(src / "bot.cpp", (
        ('        mode = "flee-dash";\n        heading_home = hp < max_hp * 0.5f;\n        retreat_from(nearest->pos);',
         '''        mode = "flee-dash";
        heading_home = hp < max_hp * 0.5f;
#if CODEX_PG_DASH_FOLLOWUP
        if (!rb::fits(0, X1_WALK_RESERVE)) return true;
#endif
        retreat_from(nearest->pos);'''),
    ))


def read_turn(directory, round_number, side, actor):
    replay = directory / "raw.repl26a"
    output = directory / "turn.json"
    with ZipFile(next(directory.glob("*.repl26a"))) as bundle:
        replay.write_bytes(bundle.read("replay.repl26a"))
    with (directory / "turn.log").open("wb") as log:
        proc = subprocess.run(["node", HERE / "trace_turn.mjs", replay, str(round_number), str("AB".index(side)),
                               str(actor), output], cwd=bench.ROOT, stdout=log, stderr=subprocess.STDOUT,
                              env={**os.environ, "NFS_REPLAY_ENGINE": "2.0.0"})
    if proc.returncode:
        return None
    state = read(output)
    state["observation"].pop("input")
    return state


def verify(wasm, escape_only=False, *, heart_attack=False, travel_tail=False, name=None):
    exact = bench.ROOT / "bots/codex-pg-camp-reserve/bot.wasm"
    assert bench.digest(exact) == read(HERE / "PG_CAMP_RESERVE_BUILDS.json")["primary"]
    if name is None:
        name = ("pg-travel-tail" if travel_tail else "pg-heart-attack" if heart_attack else
                "pg-escape-followup" if escape_only else "pg-dash-followup")
    bench.OUT = bench.CACHE / f"{name}-stress"
    (bench.OUT / "games").mkdir(parents=True)
    jobs = []
    for directory, manifest_name, profile in ((STRESS, "LARGE_ROSTER_MAPS.json", "LARGE_ROSTER_COARSE.json"),
                                               (DENSE, "DENSE_ROSTER_MAPS.json", "DENSE_ROSTER_PROFILE.json")):
        manifest = read(HERE / manifest_name)["maps"]
        for r in read(HERE / profile)["rows"]:
            mp = directory / "maps" / f"{r['map']}.map26a"
            assert bench.digest(mp) == manifest[mp.name]
            file, digest = bench.OPPS[r["opponent"]]
            assert bench.digest(bench.CACHE / file) == digest
            jobs.extend((arm, 0, r["opponent"], mp, r["side"], binary)
                        for arm, binary in (("base", exact), ("candidate", wasm)))
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(bench.one, jobs))
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    for b, c in pairs:
        assert all(b[k] == c[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
    checked = []
    targets = CASES[1:2] if escape_only else CASES[1:]
    if heart_attack:
        targets = CASES[:2]
    if travel_tail:
        targets = CASES
    for _, mp, opponent, side, round_number, actor, champion, _ in targets:
        b, c = next((b, c) for b, c in pairs if (b["map"], b["opponent"], b["side"]) == (mp, opponent, side))
        old, new = (read_turn(bench.OUT / "games" / f"{r['arm']}-0-{opponent}-{mp}-{side}", round_number, side, actor)
                    for r in (b, c))
        old_event, new_event = (any(e["owner"]["name"] == champion and e["timestamp"]["round"] == round_number
                                    for e in native_fuel(r, bench.OUT)) for r in (b, c))
        actions = 2 if champion == "Heart of Ruin" else 1
        checked.append({"map": mp, "champion": champion, "round": round_number, "old_event": old_event, "new_event": new_event,
                        "same_input_and_dash": bool(old and new and old["observation"] == new["observation"] and
                                                    old["executed_actions"][:actions] == new["executed_actions"][:actions])})
    fuel = [sum(r["fuel_outs"] for r in rows if r["arm"] == a) for a in ("base", "candidate")]
    increased = sum(c["fuel_outs"] > b["fuel_outs"] for b, c in pairs)
    errors = sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows)
    passed = (len(pairs) == 39 and fuel[1] < fuel[0] and not increased and not errors and
              all(r["old_event"] and not r["new_event"] and r["same_input_and_dash"] for r in checked))
    result = {"engine": bench.ENGINE, "sha256": bench.digest(wasm), "n": len(pairs), "fuel": fuel, "increased": increased,
              "error_cells": errors, "checked": checked, "pass": passed}
    with (HERE / f"{name.upper()}_EXACT_STRESS.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--src", type=Path)
    target.add_argument("--verify", type=Path)
    parser.add_argument("--off", action="store_true")
    parser.add_argument("--escape-only", action="store_true")
    args = parser.parse_args()
    if args.src:
        prepare(args.src, not args.off, args.escape_only)
    else:
        verify(args.verify, args.escape_only)
