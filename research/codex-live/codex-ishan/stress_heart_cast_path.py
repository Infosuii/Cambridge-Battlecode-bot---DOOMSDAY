"""Find native suspensions for the exact cast-path source under a fresh seed."""
from concurrent.futures import ThreadPoolExecutor
import json

from large_roster_stress import HERE, OUT as STRESS, bench, native_fuel, read
from qualify_local import DEV, build
from stress_greedy_pair import play

OUT = bench.CACHE / "heart-cast-path-stress-14107"
SEED = 14107


def main():
    project = bench.ROOT / "bots/codex-cpg-heart-cast-path"
    release = bench.digest(project / "bot.wasm")
    assert release == read(HERE / "CPG_HEART_CAST_PATH_BUILDS.json")["primary"]
    exact = read(HERE / "CPG_HEART_CAST_PATH_EXACT.json")
    assert exact["pass"] and exact["sha256"] == release
    assert read(HERE / "CPG_HEART_CAST_PATH_FIXTURE.json")["pass"]
    maps = sorted((STRESS / "maps").glob("*.map26a"))
    manifest = read(HERE / "LARGE_ROSTER_MAPS.json")["maps"]
    assert len(maps) == 100 and {m.name: bench.digest(m) for m in maps} == manifest
    for opponent in DEV:
        file, expected = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / file) == expected
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    wasm = build(project / "src", OUT / "candidate", SEED)
    jobs = [("path", SEED, opponent, mp, side, wasm) for mp in maps for opponent in DEV for side in "AB"]
    rows, affected = [], []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for row in pool.map(play, jobs):
            rows.append(row)
            if row["fuel_outs"] or row["errors"]:
                events = native_fuel(row, OUT)
                assert len(events) == row["fuel_outs"]
                affected.append({**row, "events": events})
            if len(rows) % 160 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    report = {"engine": bench.ENGINE, "release": release, "wasm": bench.digest(wasm), "seed": SEED,
              "n": len(rows), "opponents": {o: bench.OPPS[o][1] for o in DEV},
              "fuel": sum(r["fuel_outs"] for r in rows), "round1": sum(r["round1_fuel_outs"] for r in rows),
              "error_cells": sum(r["errors"] for r in rows)}
    with (HERE / "CPG_HEART_CAST_PATH_STRESS.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**report, "affected": affected}, out, indent=2)
        out.write("\n")
    with (OUT / "rows.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(rows, out, indent=2)
        out.write("\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()
