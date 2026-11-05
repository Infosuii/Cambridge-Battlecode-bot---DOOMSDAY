"""Apply the frozen dev and selection criteria to fresh engine-3 games."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
import re
from shutil import copytree
import subprocess

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, one, read
from qualify_local import DEV, OTHER, SEL, categories, partition


def build(src, project, seed):
    copytree(src, project / "src")
    header = project / "src/common.h"
    data = header.read_bytes()
    for name, old, new in (("NOVA_SEED", "1", str(seed)), ("NOVA_SEED_EPS", "0.04f", "0.005f")):
        pattern = rb"(?m)^#define " + name.encode() + b" " + re.escape(old.encode()) + rb"(?=\s|$)"
        data, count = re.subn(pattern, f"#define {name} {new}".encode(), data, count=1)
        assert count == 1, name
    header.write_bytes(data)
    wasm = project / "bot.wasm"
    with (project / "build.log").open("wb") as log:
        subprocess.run([CLI, "build", project, "--release", "--output", wasm], cwd=SDK_ROOT,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    return wasm


def play(job):
    arm, seed, opponent, mp, side, wasm, reference, output = job
    row = one((arm, mp, side, wasm, reference), output=output, seed=seed, opponent=opponent)
    doc = read(output / f"{mp.stem}-{side}-{arm}" / "native.json")
    area = doc["match"]["width"] * doc["match"]["height"]
    return {**row, "size": "small" if area < 1600 else "medium" if area < 4900 else "large",
            "category": categories(mp.stem)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("L1", "L2"))
    parser.add_argument("--jobs", type=int, default=10)
    args = parser.parse_args()
    safety = read(HERE / "ENGINE3_REBASELINE_POOL.json")
    assert safety["pass"] and safety["engine"] == ENGINE and bench.digest(CLI) == CLI_HASH
    reference_source = SDK_ROOT / "bots/v92-e3/src"
    source = SDK_ROOT / "bots/retry-e3/src"
    release = bench.digest(SDK_ROOT / "bots/retry-e3/bot.wasm")
    assert release == safety["builds"]["candidate"]
    if args.stage == "L1":
        maps, opponents, seeds = partition("dev"), DEV, (1104, 2701)
        development = None
    else:
        development = read(HERE / "ENGINE3_RETRY_L1.json")
        assert development["pass"] and development["candidate_release"] == release
        maps, opponents, seeds = partition("select"), SEL, (1907, 4111)
    bench.OPPS.update(OTHER)
    for opponent in opponents:
        file, expected = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / file) == expected
    output = bench.CACHE / f"engine3-retry-{args.stage.lower()}"
    output.mkdir()
    binaries = {(arm, seed): build(src, SDK_ROOT / "bots" / f"retry-{args.stage.lower()}-{arm}-{seed}", seed)
                for arm, src in (("base", reference_source), ("candidate", source)) for seed in seeds}
    for seed in seeds:
        for opponent in opponents:
            (output / f"{seed}-{opponent}").mkdir()
    jobs = [(arm, seed, opponent, mp, side, binaries[arm, seed], bench.CACHE / bench.OPPS[opponent][0],
             output / f"{seed}-{opponent}") for mp in maps for opponent in opponents for side in "AB"
            for seed in seeds for arm in ("base", "candidate")]
    rows = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for row in pool.map(play, jobs):
            rows.append(row)
            if len(rows) % 160 == 0:
                print(f"{args.stage} {len(rows)}/{len(jobs)}", flush=True)
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    for base, candidate in pairs:
        assert all(base[k] == candidate[k] for k in ("noise_seed", "opponent", "map_hash", "engine_seed", "side", "size", "category"))
    strata = {}
    for key in ("opponent", "size", "category"):
        grouped = defaultdict(list)
        for base, candidate in pairs:
            grouped[base[key]].append((base, candidate))
        strata[key] = {k: bench.summary(p) for k, p in sorted(grouped.items())}
    overall = bench.summary(pairs)
    errors = sum(bool(r["faults"] or r["opponent_faults"] or r["diagnostic_codes"]) for r in rows)
    passed = (not errors and overall["map_cluster_ci_pp"][1] >= 0 and
              all(v["delta_pp"] >= -10 for values in strata.values() for v in values.values()))
    result = {"candidate_release": release, "reference_release": safety["builds"]["reference"],
              "engine": ENGINE, "engine_version": "3.0.0", "cli_sha256": CLI_HASH,
              "stage": args.stage, "seeds": seeds, "n_maps": len(maps),
              "opponents": {o: bench.OPPS[o][1] for o in opponents}, "pass": passed,
              "binaries": {f"{arm}-{seed}": bench.digest(wasm) for (arm, seed), wasm in binaries.items()},
              "overall": overall, "strata": strata, "error_cells": errors}
    if development:
        result["development_to_selection_pp"] = round(overall["delta_pp"] - development["overall"]["delta_pp"], 3)
        result["leave_one_opponent_out"] = {
            o: bench.summary([(b, c) for b, c in pairs if b["opponent"] != o]) for o in opponents}
    with (HERE / f"ENGINE3_RETRY_{args.stage}.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    with (output / "rows.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(rows, out, indent=2)
        out.write("\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
