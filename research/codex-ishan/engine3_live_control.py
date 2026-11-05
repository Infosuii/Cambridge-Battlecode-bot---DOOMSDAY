"""Fresh paired development comparison with the exact active source archive."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, read
from engine3_qualify import build, play
from qualify_local import DEV, partition


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stellar", action="store_true")
    args = parser.parse_args()
    identity = read(HERE / "LIVE109_SOURCE_VERIFIED.json")
    safety = read(HERE / "ENGINE3_REBASELINE_POOL.json")
    assert safety["pass"] and bench.digest(CLI) == CLI_HASH
    source = SDK_ROOT / "bots/live109/src"
    reference = SDK_ROOT / "bots/live109/bot.wasm"
    candidate_name = "live109-stellar" if args.stellar else "retry-e3"
    candidate_source = SDK_ROOT / "bots" / candidate_name / "src"
    candidate_wasm = SDK_ROOT / "bots" / candidate_name / "bot.wasm"
    assert bench.digest(reference) == identity["wasm_sha256"]
    if args.stellar:
        builds = read(HERE / "LIVE109_STELLAR_BUILDS.json")
        assert builds["primary"] == builds["rebuild"] == bench.digest(candidate_wasm)
        assert builds["off"] == identity["wasm_sha256"]
    else:
        assert bench.digest(candidate_wasm) == safety["builds"]["candidate"]
    assert all(bench.digest(source / file) == expected for file, expected in identity["source_file_hashes"].items())
    categories = read(HERE / "ENGINE3_CATEGORIES_DEV.json")
    if args.stellar:
        grouped = defaultdict(list)
        for mp in partition("dev"):
            grouped[categories["maps"][mp.stem]["category"]].append(mp)
        maps = [mp for name in sorted(grouped) for mp in sorted(grouped[name], key=bench.digest)[:2]]
        assert len(maps) == 12 and all(len(rows) >= 2 for rows in grouped.values())
        manifest = {mp.name: {"sha256": bench.digest(mp), "category": categories["maps"][mp.stem]["category"]} for mp in maps}
        with (HERE / "LIVE109_STELLAR_DEV_MAPS.json").open("x", encoding="utf8", newline="\n") as out:
            json.dump(manifest, out, indent=2)
            out.write("\n")
    else:
        maps = partition("conf")
    assert categories["pool_atlas_verified"]
    assert all(categories["maps"][mp.stem]["map_hash"] == bench.digest(mp) for mp in maps)
    opponents = {name: bench.CACHE / bench.OPPS[name][0] for name in DEV}
    for name, wasm in opponents.items():
        assert bench.digest(wasm) == bench.OPPS[name][1]
    opponents["live109"] = reference
    seeds = (7331, 9029) if args.stellar else (3157, 6421)
    label = "live109-stellar" if args.stellar else "live109-control"
    binaries = {(arm, seed): build(src, SDK_ROOT / "bots" / f"{label}-{arm}-{seed}", seed)
                for arm, src in (("base", source), ("candidate", candidate_source)) for seed in seeds}
    output = bench.CACHE / f"engine3-{label}"
    output.mkdir()
    for seed in seeds:
        for opponent in opponents:
            (output / f"{seed}-{opponent}").mkdir()
    jobs = [(arm, seed, opponent, mp, side, binaries[arm, seed], wasm,
             output / f"{seed}-{opponent}", categories["maps"][mp.stem]["category"])
            for mp in maps for opponent, wasm in opponents.items() for side in "AB"
            for seed in seeds for arm in ("base", "candidate")]
    rows = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for row in pool.map(play, jobs):
            rows.append(row)
            if len(rows) % 80 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    for base, candidate in pairs:
        assert all(base[k] == candidate[k] for k in ("noise_seed", "opponent", "map_hash", "engine_seed", "side", "size", "category"))
    strata = {}
    for key in ("opponent", "size", "category"):
        grouped = defaultdict(list)
        for base, candidate in pairs:
            grouped[base[key]].append((base, candidate))
        strata[key] = {name: bench.summary(p) for name, p in sorted(grouped.items())}
    overall = bench.summary(pairs)
    errors = sum(bool(r["faults"] or r["opponent_faults"] or r["diagnostic_codes"]) for r in rows)
    passed = (not errors and overall["map_cluster_ci_pp"][1] >= 0 and
              all(v["delta_pp"] >= -10 for values in strata.values() for v in values.values()))
    result = {"reference_release": identity["wasm_sha256"], "reference_archive": identity["archive_sha256"],
              "candidate_release": bench.digest(candidate_wasm), "engine": ENGINE, "cli_sha256": CLI_HASH,
              "n_maps": len(maps), "seeds": seeds, "pass": passed, "overall": overall, "strata": strata,
              "error_cells": errors, "opponents": {name: bench.digest(wasm) for name, wasm in opponents.items()},
              "binaries": {f"{arm}-{seed}": bench.digest(wasm) for (arm, seed), wasm in binaries.items()}}
    result_name = "ENGINE3_LIVE109_STELLAR_DEV.json" if args.stellar else "ENGINE3_LIVE109_CONTROL.json"
    with (HERE / result_name).open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    with (output / "rows.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(rows, out, indent=2)
        out.write("\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
