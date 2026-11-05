"""Pre-registered single existing-guard comparisons on the exact new live source."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from shutil import copytree
import subprocess

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, read
from engine3_qualify import build, play
from freeze_engine3_discovery import write
from qualify_local import DEV, partition


def main():
    identity = read(HERE / "LIVE111_SOURCE_VERIFIED.json")
    source = SDK_ROOT / "bots/live111/src"
    assert bench.digest(CLI) == CLI_HASH
    assert all(bench.digest(source / n) == h for n, h in identity["source_file_hashes"].items())
    output = bench.CACHE / "engine3-live111-clfs-parts"
    output.mkdir()
    sources, releases = {}, {}
    for bits in (9, 11, 13):
        hashes = []
        for suffix in ("", "-rebuild") if bits != 9 else ("",):
            project = SDK_ROOT / "bots" / f"live111-clfs{bits}{suffix}"
            target = project / "src"
            copytree(source, target)
            header = target / "common.h"
            header.write_bytes(f"#define CLFS {bits}\n".encode() + header.read_bytes())
            with (project / "build.log").open("wb") as log:
                subprocess.run([CLI, "build", project, "--release", "--output", project / "bot.wasm"], cwd=SDK_ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
            hashes.append(bench.digest(project / "bot.wasm"))
            print(bits, suffix or "primary", hashes[-1], flush=True)
            if not suffix: sources[bits] = target
        assert len(set(hashes)) == 1
        releases[str(bits)] = hashes[0]
    assert releases["9"] == identity["wasm_sha256"]
    write(HERE / "LIVE111_CLFS_PARTS_BUILDS.json", {"source_archive": identity["archive_sha256"], "release_hashes": releases})
    categories = read(HERE / "ENGINE3_CATEGORIES_DEV.json")
    maps_by_name = {mp.name: mp for mp in partition("dev")}
    manifest = read(HERE / "LIVE109_STELLAR_DEV_MAPS.json")
    maps = [maps_by_name[name] for name in manifest]
    assert all(bench.digest(mp) == manifest[mp.name]["sha256"] == categories["maps"][mp.stem]["map_hash"] for mp in maps)
    opponents = {name: bench.CACHE / bench.OPPS[name][0] for name in DEV}
    assert all(bench.digest(wasm) == bench.OPPS[name][1] for name, wasm in opponents.items())
    opponents["live109"] = SDK_ROOT / "bots/live109/bot.wasm"
    assert bench.digest(opponents["live109"]) == read(HERE / "LIVE109_SOURCE_VERIFIED.json")["wasm_sha256"]
    seeds = (22447, 25111)
    binaries = {(bits, seed): build(src, SDK_ROOT / "bots" / f"live111-clfs{bits}-{seed}", seed) for bits, src in sources.items() for seed in seeds}
    for seed in seeds:
        for opponent in opponents: (output / f"{seed}-{opponent}").mkdir()
    jobs = [(str(bits), seed, opponent, mp, side, binaries[bits, seed], wasm, output / f"{seed}-{opponent}", categories["maps"][mp.stem]["category"])
            for mp in maps for opponent, wasm in opponents.items() for side in "AB" for seed in seeds for bits in sources]
    rows = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(play, jobs):
            rows.append(row)
            if len(rows) % 120 == 0: print(f"{len(rows)}/{len(jobs)}", flush=True)
    result = {"engine": ENGINE, "source_archive": identity["archive_sha256"], "releases": releases,
              "seeds": seeds, "n_games": len(rows), "results": {}}
    key = lambda r: tuple(r[k] for k in ("map_hash", "side", "opponent", "noise_seed", "engine_seed"))
    baseline = {key(r): r for r in rows if r["arm"] == "9"}
    for bits in (11, 13):
        pairs = [(baseline[key(r)], r) for r in rows if r["arm"] == str(bits)]
        strata = {}
        for field in ("opponent", "size", "category"):
            grouped = defaultdict(list)
            for a, b in pairs: grouped[a[field]].append((a, b))
            strata[field] = {name: bench.summary(p) for name, p in sorted(grouped.items())}
        overall = bench.summary(pairs)
        errors = sum(bool(r["faults"] or r["opponent_faults"] or r["diagnostic_codes"]) for pair in pairs for r in pair)
        win_pass = not errors and overall["map_cluster_ci_pp"][1] >= 0 and all(v["delta_pp"] >= -10 for group in strata.values() for v in group.values())
        result["results"][str(bits)] = {"overall": overall, "strata": strata, "error_cells": errors,
            "win_filter_pass": win_pass, "safety_pass": not errors and not overall["per_cell_fuel_regressions"]}
    write(output / "rows.json", rows)
    write(HERE / "LIVE111_CLFS_PARTS_DEV.json", result)
    print(json.dumps({bits: {k: v for k, v in data.items() if k != "strata"} for bits, data in result["results"].items()}, indent=2), flush=True)


if __name__ == "__main__":
    main()
