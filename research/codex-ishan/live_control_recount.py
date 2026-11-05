"""Recover reports from immutable completed engine-3 native games; never run games."""
import argparse
from collections import defaultdict
import json

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, read
from qualify_local import DEV, partition


def native_row(arm, seed, opponent, mp, side, output, categories):
    doc = read(output / f"{seed}-{opponent}" / f"{mp.stem}-{side}-{arm}" / "native.json")
    match = doc["match"]
    assert (match["engineVersion"], match["engineBuildHash"]) == ("3.0.0", ENGINE)
    assert doc["diagnostics"]["detailedCaptureComplete"]
    assert match["mapHash"] == bench.digest(mp) == categories[mp.stem]["map_hash"]
    assert match["outcome"] in ("teamA", "teamB", "draw")
    ours = "team" + side
    theirs = "teamB" if side == "A" else "teamA"
    fuel = [entry["timestamp"]["round"] for event in doc["events"]
            if event["kind"] == "fuelExhausted" and event["owner"]["team"] == ours for entry in event["entries"]]
    area = match["width"] * match["height"]
    return {"arm": arm, "noise_seed": seed, "opponent": opponent, "map": mp.stem, "side": side,
            "map_hash": match["mapHash"], "engine_seed": match["seed"],
            "score": 1 if match["outcome"] == ours else 0.5 if match["outcome"] == "draw" else 0,
            "fuel_outs": len(fuel), "round1_fuel_outs": fuel.count(1),
            "faults": doc["diagnostics"]["botFaults"][ours], "opponent_faults": doc["diagnostics"]["botFaults"][theirs],
            "diagnostic_codes": doc["diagnostics"]["codes"],
            "size": "small" if area < 1600 else "medium" if area < 4900 else "large",
            "category": categories[mp.stem]["category"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stellar", action="store_true")
    args = parser.parse_args()
    identity = read(HERE / "LIVE109_SOURCE_VERIFIED.json")
    assert bench.digest(CLI) == CLI_HASH
    reference = SDK_ROOT / "bots/live109/bot.wasm"
    assert bench.digest(reference) == identity["wasm_sha256"]
    if args.stellar:
        manifest = read(HERE / "LIVE109_STELLAR_DEV_MAPS.json")
        dev = {mp.name: mp for mp in partition("dev")}
        maps = [dev[name] for name in manifest]
        assert len(maps) == 12 and all(bench.digest(mp) == manifest[mp.name]["sha256"] for mp in maps)
        label, project_label, seeds = "live109-stellar", "live109-stellar", (7331, 9029)
        builds = read(HERE / "LIVE109_STELLAR_BUILDS.json")
        candidate = SDK_ROOT / "bots/live109-stellar/bot.wasm"
        assert bench.digest(candidate) == builds["primary"] == builds["rebuild"]
        assert builds["off"] == identity["wasm_sha256"]
        result_name = "ENGINE3_LIVE109_STELLAR_DEV.json"
    else:
        maps = partition("conf")
        label, project_label, seeds = "live109-control", "live-control", (3157, 6421)
        candidate = SDK_ROOT / "bots/retry-e3/bot.wasm"
        result_name = "ENGINE3_LIVE109_CONTROL.json"
    output = bench.CACHE / f"engine3-{label}"
    categories = read(HERE / "ENGINE3_CATEGORIES_DEV.json")
    assert categories["pool_atlas_verified"]
    opponents = {name: bench.CACHE / bench.OPPS[name][0] for name in DEV}
    assert all(bench.digest(wasm) == bench.OPPS[name][1] for name, wasm in opponents.items())
    opponents["live109"] = reference
    binaries = {f"{arm}-{seed}": bench.digest(SDK_ROOT / "bots" / f"{project_label}-{arm}-{seed}/bot.wasm")
                for arm in ("base", "candidate") for seed in seeds}
    rows = [native_row(arm, seed, opponent, mp, side, output, categories["maps"])
            for mp in maps for opponent in opponents for side in "AB" for seed in seeds for arm in ("base", "candidate")]
    assert len(list(output.glob("*/*/native.json"))) == len(rows)
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    for base, cand in pairs:
        assert all(base[k] == cand[k] for k in ("noise_seed", "opponent", "map_hash", "engine_seed", "side", "size", "category"))
    strata = {}
    for key in ("opponent", "size", "category"):
        grouped = defaultdict(list)
        for base, cand in pairs:
            grouped[base[key]].append((base, cand))
        strata[key] = {name: bench.summary(p) for name, p in sorted(grouped.items())}
    overall = bench.summary(pairs)
    errors = sum(bool(r["faults"] or r["opponent_faults"] or r["diagnostic_codes"]) for r in rows)
    passed = not errors and overall["map_cluster_ci_pp"][1] >= 0 and all(
        v["delta_pp"] >= -10 for values in strata.values() for v in values.values())
    result = {"reference_release": identity["wasm_sha256"], "reference_archive": identity["archive_sha256"],
              "candidate_release": bench.digest(candidate), "engine": ENGINE, "cli_sha256": CLI_HASH,
              "n_maps": len(maps), "seeds": list(seeds), "pass": passed, "overall": overall, "strata": strata,
              "error_cells": errors, "opponents": {name: bench.digest(wasm) for name, wasm in opponents.items()}, "binaries": binaries}
    if args.stellar:
        for path, data in ((HERE / result_name, result), (output / "rows.json", rows)):
            with path.open("x", encoding="utf8", newline="\n") as out:
                json.dump(data, out, indent=2)
                out.write("\n")
    else:
        assert result == read(HERE / result_name)
        assert rows == read(output / "rows.json")
        print("Historical 640-game control report and all rows match exactly.", flush=True)
    print(json.dumps({"pass": passed, "overall": overall, "strata_deltas": {
        key: {name: value["delta_pp"] for name, value in values.items()} for key, values in strata.items()}}, indent=2), flush=True)


if __name__ == "__main__":
    main()
