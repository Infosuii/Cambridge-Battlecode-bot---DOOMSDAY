"""Fresh matched safety baseline on the official engine after the balance update."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

import ablate_dev as bench

HERE = Path(__file__).resolve().parent
SDK_ROOT = Path("C:/dd/codex-sdk5-20261105")
CLI = bench.ROOT / "tools/vendor/cambc-5.0.0.exe"
CLI_HASH = "4a94c15027d94c4702e1b84471cb25110a5d2c4e3c67976e65439d93582e774c"
ENGINE = "96ce858f548c14560eff737967a691a30eaf0a469afd1f4f400f125e094bd1fd"
OUT = bench.CACHE / "engine3-pool-20261105"


def read(path):
    return json.loads(path.read_bytes())


def one(job, *, output=OUT, seed=1, opponent="v92"):
    arm, mp, side, wasm, reference = job
    directory = output / f"{mp.stem}-{side}-{arm}"
    directory.mkdir()
    bots = (wasm, reference) if side == "A" else (reference, wasm)
    with (directory / "run.log").open("wb") as log:
        subprocess.run([CLI, "run", *bots, "--map", mp, "--release", "--json", "--fuel", "100000",
                        "--log-limit", "0", "--statistics", directory / "native.json", "--out-dir", directory],
                       cwd=SDK_ROOT, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    doc = read(directory / "native.json")
    match = doc["match"]
    assert (match["engineVersion"], match["engineBuildHash"]) == ("3.0.0", ENGINE)
    assert doc["diagnostics"]["detailedCaptureComplete"] and match["outcome"] in ("teamA", "teamB", "draw")
    assert match["mapHash"] == bench.digest(mp)
    ours = "team" + side
    opponent_team = "teamB" if side == "A" else "teamA"
    fuel = [entry["timestamp"]["round"] for event in doc["events"]
            if event["kind"] == "fuelExhausted" and event["owner"]["team"] == ours for entry in event["entries"]]
    return {"arm": arm, "noise_seed": seed, "opponent": opponent, "map": mp.stem, "side": side,
            "map_hash": match["mapHash"], "engine_seed": match["seed"],
            "score": 1 if match["outcome"] == ours else 0.5 if match["outcome"] == "draw" else 0,
            "fuel_outs": len(fuel), "round1_fuel_outs": fuel.count(1),
            "faults": doc["diagnostics"]["botFaults"][ours],
            "opponent_faults": doc["diagnostics"]["botFaults"][opponent_team],
            "diagnostic_codes": doc["diagnostics"]["codes"]}


def main():
    builds = read(HERE / "ENGINE3_REBASELINE_BUILDS.json")
    assert bench.digest(CLI) == CLI_HASH
    reference = SDK_ROOT / "bots/v92-e3/bot.wasm"
    candidate = SDK_ROOT / "bots/retry-e3/bot.wasm"
    assert bench.digest(reference) == builds["reference"] == builds["reference_rebuild"] == builds["off"]
    assert bench.digest(candidate) == builds["candidate"] == builds["candidate_rebuild"]
    original = read(bench.ROOT / "docs/codex/CPG_POOL_SAFETY.json")
    pinned = {r["map"]: r["map_hash"] for r in original["rows"] if r["arm"] == "v92"}
    maps = sorted((bench.ROOT / "maps/ladder-pool").glob("*.map26a"))
    assert len(pinned) == len(maps) == 86 and all(bench.digest(mp) == pinned[mp.stem] for mp in maps)
    jobs = [(arm, mp, side, wasm, reference) for mp in maps for side in "AB"
            for arm, wasm in (("base", reference), ("candidate", candidate))]
    OUT.mkdir()
    rows = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(one, jobs):
            rows.append(row)
            if len(rows) % 80 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    for base, cand in pairs:
        assert all(base[k] == cand[k] for k in ("map_hash", "engine_seed", "opponent", "side"))
    overall = bench.summary(pairs)
    errors = sum(bool(r["faults"] or r["opponent_faults"] or r["diagnostic_codes"]) for r in rows)
    result = {"engine_version": "3.0.0", "engine": ENGINE, "cli_sha256": CLI_HASH,
              "builds": builds, "overall": overall,
              "b": sum(c["score"] > b["score"] for b, c in pairs),
              "c": sum(b["score"] > c["score"] for b, c in pairs),
              "newly_suspended": sum(b["fuel_outs"] == 0 and c["fuel_outs"] > 0 for b, c in pairs),
              "error_cells": errors, "pass": not errors and not overall["per_cell_fuel_regressions"]}
    with (HERE / "ENGINE3_REBASELINE_POOL.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
