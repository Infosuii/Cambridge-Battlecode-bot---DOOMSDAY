"""Run the frozen L1/L2 map and opponent sets with the master's paired noise rule."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
from shutil import copytree
import subprocess

import ablate_dev as bench

HERE = Path(__file__).resolve().parent
SETS = bench.CACHE / "jd-sets"
V92 = bench.OPPS["v92"][1]
DEV = ("v92", "x3inv", "p65pack", "public-khiri")
SEL = ("v92", "x3ctr", "p65", "v86h")
OTHER = {
    "x3ctr": ("opp-x3ctr.wasm", "96612d0a188b95cc6d6bdf830a836f3bcd0b21113b447cbc7001e76bea651cd9"),
    "p65": ("opp-p65.wasm", "ebd1504fa1c39e88ed1da01ac9f53d79b30830e4bef86e644ef3c13d1a01c473"),
    "v86h": ("opp-v86h.wasm", "0fae1c17ee73bd758529b92f7d7ab55f1dea6f2ecf0865cdac423b2ecd5640fb"),
}
PARTITIONS = {
    "dev": (90, "4268c4752502f768848d11ac1bd460a2cc6fc12e32756f240dbc9d71d9114b06"),
    "conf": (16, "94b6b4b43167ba179171f6ff3d616d802531c5cd632704412126cc3a21506852"),
    "select": (100, "2a3b97fddbaf326fdfd7e1523b8e51ab007db38e037b3e7295977b04819f1d2a"),
}


def read(path):
    return json.loads(path.read_bytes())


def partition(name):
    maps = sorted((SETS / name).glob("*.map26a"))
    digest = bench.sha256("\n".join(f"{bench.digest(m)} {m.name}" for m in maps).encode()).hexdigest()
    assert (len(maps), digest) == PARTITIONS[name]
    return maps


def categories(name):
    if "pool_" in name:
        return "generated"
    return "pool" + name[:2] if name[:2] in ("00", "01", "02", "03") else name.split("-")[0]


def build(src, project, seed):
    copytree(src, project / "src")
    header = project / "src/common.h"
    data = header.read_bytes()
    for name, old, new in (("NOVA_SEED", "1", str(seed)), ("NOVA_SEED_EPS", "0.04f", "0.005f")):
        pattern = rb"(?m)^#define " + name.encode() + rb" " + re.escape(old.encode()) + rb"(?=\s|$)"
        data, n = re.subn(pattern, f"#define {name} {new}".encode(), data, count=1)
        assert n == 1, (header, name)
    header.write_bytes(data)
    wasm = project / "bot.wasm"
    with (project / "build.log").open("wb") as log:
        subprocess.run([bench.CLI, "build", project, "--release", "--output", wasm],
                       cwd=bench.ROOT, check=True, stdout=log, stderr=subprocess.STDOUT)
    return wasm


def play(job):
    row = bench.one(job)
    arm, seed, opp, mp, side, _ = job
    path = bench.OUT / "games" / f"{arm}-{seed}-{opp}-{mp.stem}-{side}" / "native.json"
    n = read(path)["match"]
    area = n["width"] * n["height"]
    size = "small" if area < 1600 else "medium" if area < 4900 else "large"
    return {**row, "size": size, "category": categories(row["map"])}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("candidate", help="name of bots/codex-<candidate>")
    p.add_argument("stage", choices=("L1", "L2"))
    p.add_argument("--jobs", type=int, default=8)
    a = p.parse_args()
    stage = a.stage
    name = a.candidate
    assert re.fullmatch(r"[a-z0-9-]+", name)
    project = bench.ROOT / "bots" / f"codex-{name}"
    source = project / "src"
    digest = bench.digest(project / "bot.wasm")
    l0 = read(HERE / f"{name.upper()}_POOL_SAFETY.json")
    assert l0["sha256"] == digest and l0["n"] == 172
    assert not l0["fuel_regressions"] and not l0["diagnostic_cells"]
    assert all(r["faults"] == r["opponent_faults"] == 0 for r in l0["total"].values())
    if stage == "L1":
        maps = partition("dev")
        checked = {m.name: bench.digest(m) for m in maps}
        assert all(checked[m.name] == bench.digest(m) for m in partition("conf"))
        opponents, seeds = DEV, (1104, 2701)
    else:
        l1 = read(HERE / f"{name.upper()}_L1.json")
        assert l1["pass"] and l1["candidate_release"] == digest
        maps = partition("select")
        opponents, seeds = SEL, (1907, 4111)
    bench.OPPS.update(OTHER)
    for opp in opponents:
        file, expected = bench.OPPS[opp]
        assert bench.digest(bench.CACHE / file) == expected

    bench.OUT = bench.CACHE / f"qualify-{name}-{stage.lower()}"
    (bench.OUT / "games").mkdir(parents=True)
    arms = {"base": bench.ROOT / "bots/v92/src", "candidate": source}
    bins = {(arm, seed): build(src, bench.OUT / f"{arm}-{seed}", seed)
            for arm, src in arms.items() for seed in seeds}
    jobs = [(arm, seed, opp, mp, side, bins[arm, seed]) for mp in maps for opp in opponents
            for side in "AB" for seed in seeds for arm in arms]
    rows = []
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        for row in pool.map(play, jobs):
            rows.append(row)
            if len(rows) % 160 == 0:
                print(f"{stage} {len(rows)}/{len(jobs)}", flush=True)
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    for b, c in pairs:
        assert all(b[k] == c[k] for k in ("noise_seed", "opponent", "map_hash", "engine_seed", "side", "size", "category"))
    strata = {}
    for key in ("opponent", "size", "category"):
        grouped = defaultdict(list)
        for b, c in pairs:
            grouped[b[key]].append((b, c))
        strata[key] = {k: bench.summary(p) for k, p in sorted(grouped.items())}
    overall = bench.summary(pairs)
    errors = sum(r["faults"] > 0 or bool(r["diagnostic_codes"]) for r in rows)
    passed = (not errors and overall["map_cluster_ci_pp"][1] >= 0 and
              all(v["delta_pp"] >= -10 for by_key in strata.values() for v in by_key.values()))
    result = {"candidate_release": digest, "reference_release": V92, "engine": bench.ENGINE,
              "stage": stage, "seeds": seeds, "n_maps": len(maps),
              "opponents": {o: bench.OPPS[o][1] for o in opponents}, "pass": passed,
              "binaries": {f"{arm}-{seed}": bench.digest(wasm) for (arm, seed), wasm in bins.items()},
              "overall": overall, "strata": strata, "error_cells": errors}
    if stage == "L2":
        result["development_to_selection_pp"] = round(overall["delta_pp"] - l1["overall"]["delta_pp"], 3)
        result["leave_one_opponent_out"] = {
            o: bench.summary([(b, c) for b, c in pairs if b["opponent"] != o]) for o in opponents}
    with (HERE / f"{name.upper()}_{stage}.json").open("x", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    with (bench.OUT / "rows.json").open("x", encoding="utf-8", newline="\n") as f:
        json.dump(rows, f, indent=2)
        f.write("\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
