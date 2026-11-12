"""Establish the exact new live-source safety baseline without altering frozen references."""
from concurrent.futures import ThreadPoolExecutor
import json

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, one, read
from freeze_engine3_discovery import write


def main():
    identity = read(HERE / "LIVE111_SOURCE_VERIFIED.json")
    reference = SDK_ROOT / "bots/v92-e3/bot.wasm"
    candidate = SDK_ROOT / "bots/live111/bot.wasm"
    assert bench.digest(CLI) == CLI_HASH and bench.digest(candidate) == identity["wasm_sha256"] == identity["rebuild_sha256"]
    assert bench.digest(reference) == bench.OPPS["v92"][1]
    original = read(HERE / "ENGINE3_REBASELINE_POOL.json")
    assert original["engine"] == ENGINE
    baseline = {(r["map"], r["side"]): r for r in original["rows"] if r["arm"] == "base"}
    maps = sorted((bench.ROOT / "maps/ladder-pool").glob("*.map26a"))
    assert len(maps) == 86 and len(baseline) == 172
    assert all(bench.digest(mp) == baseline[mp.stem, "A"]["map_hash"] for mp in maps)
    output = bench.CACHE / "engine3-live111-pool"
    output.mkdir()
    jobs = [("candidate", mp, side, candidate, reference) for mp in maps for side in "AB"]
    rows = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(lambda job: one(job, output=output), jobs):
            rows.append(row)
            if len(rows) % 40 == 0: print(f"{len(rows)}/172", flush=True)
    pairs = [(baseline[r["map"], r["side"]], r) for r in rows]
    for a, b in pairs:
        assert all(a[k] == b[k] for k in ("map_hash", "engine_seed", "side", "opponent"))
    totals = bench.summary(pairs)
    errors = sum(bool(r["faults"] or r["opponent_faults"] or r["diagnostic_codes"]) for r in rows)
    result = {"platform_source_version": 111, "candidate_release": identity["wasm_sha256"], "source_archive": identity["archive_sha256"],
              "reference_release": bench.digest(reference), "engine": ENGINE, "overall": totals, "error_cells": errors,
              "safety_pass": not errors and not totals["per_cell_fuel_regressions"], "interpretation": "Safety/context only; fixed-release pool, no noisy strength or ladder claim.", "rows": rows}
    write(HERE / "LIVE111_POOL_SAFETY.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2), flush=True)


if __name__ == "__main__":
    main()
