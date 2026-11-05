"""Run the frozen standard-budget mixed-roster diagnostic on the post-ward source."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

from large_roster_stress import ENGINE_SHA, HERE, SOURCE, SOURCE_SHA, bench, native_fuel, read
from qualify_local import DEV, build, partition
from stress_greedy_pair import play

OUT = bench.CACHE / "post-ward-mixed-stress-802673"
MAP_SEED = 802673
COMPILED_SEED = 14821


def generate(output, map_seed, manifest_name, prior_manifests):
    generator = output / "mapmake6.js"
    generator.write_bytes(subprocess.check_output(["git", "show", SOURCE], cwd=bench.ROOT))
    assert bench.digest(generator) == SOURCE_SHA
    folder = Path.home() / "AppData/Local/cambc/assets"
    asset = next(p for p in folder.glob("*/visualiser/assets/v2_0_0-hWOQ1R8f.wasm") if bench.digest(p) == ENGINE_SHA)
    (output / "v2_0_0.wasm").write_bytes(asset.read_bytes())
    with (output / "generate.log").open("wb") as log:
        subprocess.run(["node", generator, output / "maps", "100", str(map_seed)], cwd=bench.ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    maps = sorted((output / "maps").glob("*.map26a"))
    hashes = {p.name: bench.digest(p) for p in maps}
    assert len(maps) == len(set(hashes.values())) == 100
    reserved = {line.split()[0] for line in (bench.ROOT / "docs/codex/FRESH_HOLDOUT.sha256").read_text().splitlines()}
    reserved.update(bench.digest(p) for p in partition("dev"))
    reserved.update(bench.digest(p) for p in (bench.ROOT / "maps/ladder-pool").glob("*.map26a"))
    for name in ("LARGE_ROSTER_MAPS.json", "DENSE_ROSTER_MAPS.json", *prior_manifests):
        reserved.update(read(HERE / name)["maps"].values())
    assert not reserved.intersection(hashes.values())
    manifest = {"seed": map_seed, "source": SOURCE, "source_sha": SOURCE_SHA, "engine_wasm": ENGINE_SHA, "maps": hashes}
    with (HERE / manifest_name).open("x", encoding="utf8", newline="\n") as out:
        json.dump(manifest, out, indent=2)
        out.write("\n")
    print("Froze", len(maps), "new mixed-roster maps", flush=True)
    return maps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retry", action="store_true")
    args = parser.parse_args()
    arm = "ward-retry" if args.retry else "post-ward"
    output = bench.CACHE / "ward-retry-mixed-stress-827399" if args.retry else OUT
    map_seed = 827399 if args.retry else MAP_SEED
    seeds = (17239, 18443) if args.retry else (COMPILED_SEED,)
    prefix = arm.upper().replace('-', '_')
    project = bench.ROOT / f"bots/codex-cpg-safe-tribute-{arm}"
    release = bench.digest(project / "bot.wasm")
    assert release == read(HERE / f"CPG_SAFE_TRIBUTE_{prefix}_BUILDS.json")["primary"]
    controls = ("EXACT", "FIXTURE", "HEART", "MIXED") if args.retry else ("EXACT", "FIXTURE", "HEART")
    assert all(read(HERE / f"CPG_SAFE_TRIBUTE_{prefix}_{kind}.json")["pass"] for kind in controls)
    for opponent in DEV:
        file, expected = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / file) == expected
    bench.OUT = output
    (output / "games").mkdir(parents=True)
    maps = generate(output, map_seed, f"{prefix}_MIXED_MAPS.json", ("POST_WARD_MIXED_MAPS.json",) if args.retry else ())
    bins = {seed: build(project / "src", output / f"candidate-{seed}", seed) for seed in seeds}
    jobs = [(arm, seed, opponent, mp, side, wasm) for mp in maps for opponent in DEV for side in "AB" for seed, wasm in bins.items()]
    rows, affected, slots_by_map = [], [], {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        for row in pool.map(play, jobs):
            slots = sum(p["team"] == "team" + row["side"] for p in row["draft"])
            assert 3 <= slots <= 5 and slots_by_map.setdefault(row["map"], slots) == slots
            rows.append({**row, "slots": slots})
            if row["fuel_outs"] or row["errors"]:
                events = native_fuel(row, output, slots=slots)
                assert len(events) == row["fuel_outs"]
                affected.append({**rows[-1], "events": events})
            if len(rows) % 160 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    builds = {"binaries": {seed: bench.digest(wasm) for seed, wasm in bins.items()}} if args.retry else {
        "wasm": bench.digest(bins[COMPILED_SEED]), "seed": COMPILED_SEED}
    report = {"engine": bench.ENGINE, "release": release, **builds,
              "map_seed": map_seed, "n": len(rows), "map_slots": dict(Counter(slots_by_map.values())),
              "opponents": {o: bench.OPPS[o][1] for o in DEV}, "fuel": sum(r["fuel_outs"] for r in rows),
              "round1": sum(r["round1_fuel_outs"] for r in rows), "error_cells": sum(r["errors"] for r in rows)}
    with (HERE / f"CPG_{prefix}_MIXED_STRESS.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**report, "affected": affected}, out, indent=2)
        out.write("\n")
    with (output / "rows.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(rows, out, indent=2)
        out.write("\n")
    print(report, flush=True)


if __name__ == "__main__":
    main()
