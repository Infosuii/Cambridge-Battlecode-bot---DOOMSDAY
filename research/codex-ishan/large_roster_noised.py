"""Locate native suspensions under two fresh stress-only score-noise seeds."""
from concurrent.futures import ThreadPoolExecutor
import json

from large_roster_stress import HERE, OUT as STRESS, bench, native_fuel, read
from qualify_local import DEV, build

OUT = bench.CACHE / "large-roster-noise-5309-7013"
SEEDS = (5309, 7013)


def main():
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    project = bench.ROOT / "bots/codex-pg-siege-resume"
    release = bench.digest(project / "bot.wasm")
    assert release == read(HERE / "PG_SIEGE_RESUME_BUILDS.json")["primary"]
    manifest = read(HERE / "LARGE_ROSTER_MAPS.json")["maps"]
    maps = sorted((STRESS / "maps").glob("*.map26a"))
    assert len(maps) == 100 and {m.name: bench.digest(m) for m in maps} == manifest
    for o in DEV:
        file, digest = bench.OPPS[o]
        assert bench.digest(bench.CACHE / file) == digest
    with ThreadPoolExecutor(max_workers=2) as pool:
        builds = dict(zip(SEEDS, pool.map(lambda s: build(project / "src", OUT / f"seed-{s}", s), SEEDS), strict=True))
    jobs = [("stress", seed, o, m, s, builds[seed]) for m in maps for o in DEV for s in "AB" for seed in SEEDS]
    rows, affected = [], []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for row in pool.map(bench.one, jobs):
            rows.append(row)
            if row["fuel_outs"] or row["faults"] or row["diagnostic_codes"]:
                events = native_fuel(row, OUT)
                assert len(events) == row["fuel_outs"]
                affected.append({**row, "events": events})
            if len(rows) % 160 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    result = {"engine": bench.ENGINE, "parent_release": release, "binaries": {s: bench.digest(b) for s, b in builds.items()},
              "opponents": {o: bench.OPPS[o][1] for o in DEV}, "n": len(rows), "fuel": sum(r["fuel_outs"] for r in rows),
              "round1": sum(r["round1_fuel_outs"] for r in rows), "error_cells": sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows),
              "affected": affected}
    (OUT / "rows.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf8", newline="\n")
    with (HERE / "LARGE_ROSTER_NOISE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k: v for k, v in result.items() if k != "affected"}, flush=True)


if __name__ == "__main__":
    main()
