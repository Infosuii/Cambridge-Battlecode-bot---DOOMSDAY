"""Locate native suspensions under two fresh stress-only score-noise seeds."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json

from large_roster_stress import HERE, OUT as STRESS, bench, native_fuel, read
from qualify_local import DEV, build

OUT = bench.CACHE / "large-roster-noise-5309-7013"
SEEDS = (5309, 7013)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--travel-scan", action="store_true")
    travel_scan = parser.parse_args().travel_scan
    out = bench.CACHE / "travel-scan-roster-noise" if travel_scan else OUT
    bench.OUT = out
    (out / "games").mkdir(parents=True)
    name = "pg-travel-scan" if travel_scan else "pg-siege-resume"
    project = bench.ROOT / f"bots/codex-{name}"
    release = bench.digest(project / "bot.wasm")
    assert release == read(HERE / f"{name.upper().replace('-', '_')}_BUILDS.json")["primary"]
    manifest = read(HERE / "LARGE_ROSTER_MAPS.json")["maps"]
    maps = sorted((STRESS / "maps").glob("*.map26a"))
    assert len(maps) == 100 and {m.name: bench.digest(m) for m in maps} == manifest
    for o in DEV:
        file, digest = bench.OPPS[o]
        assert bench.digest(bench.CACHE / file) == digest
    with ThreadPoolExecutor(max_workers=2) as pool:
        builds = dict(zip(SEEDS, pool.map(lambda s: build(project / "src", out / f"seed-{s}", s), SEEDS), strict=True))
    jobs = [("stress", seed, o, m, s, builds[seed]) for m in maps for o in DEV for s in "AB" for seed in SEEDS]
    rows, affected = [], []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for row in pool.map(bench.one, jobs):
            rows.append(row)
            if row["fuel_outs"] or row["faults"] or row["diagnostic_codes"]:
                events = native_fuel(row, out)
                assert len(events) == row["fuel_outs"]
                affected.append({**row, "events": events})
            if len(rows) % 160 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    result = {"engine": bench.ENGINE, "parent_release": release, "binaries": {s: bench.digest(b) for s, b in builds.items()},
              "opponents": {o: bench.OPPS[o][1] for o in DEV}, "n": len(rows), "fuel": sum(r["fuel_outs"] for r in rows),
              "round1": sum(r["round1_fuel_outs"] for r in rows), "error_cells": sum(bool(r["faults"] or r["diagnostic_codes"]) for r in rows),
              "affected": affected}
    if travel_scan:
        reference = read(OUT / "rows.json")
        pairs = list(zip(reference, rows, strict=True))
        assert all(all(b[k] == c[k] for k in ("noise_seed", "opponent", "map_hash", "engine_seed", "side")) for b, c in pairs)
        result["reference_release"] = read(HERE / "LARGE_ROSTER_NOISE.json")["parent_release"]
        result["paired_outcomes"] = bench.summary(pairs)
        result["increased"] = sum(c["fuel_outs"] > b["fuel_outs"] for b, c in pairs)
    (out / "rows.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf8", newline="\n")
    report = "TRAVEL_SCAN_ROSTER_NOISE.json" if travel_scan else "LARGE_ROSTER_NOISE.json"
    with (HERE / report).open("x", encoding="utf8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print({k: v for k, v in result.items() if k != "affected"}, flush=True)


if __name__ == "__main__":
    main()
