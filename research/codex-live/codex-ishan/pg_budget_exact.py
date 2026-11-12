"""Compare the exact combined PG release against the exact PG dev arm."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import ablate_dev as bench

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_bytes())


def main():
    base = read(HERE / "PG_RIVAL_RELEASE_DEV.json")
    manifest = read(HERE / "PG_BUDGET_BUILDS.json")
    wasm = bench.ROOT / "bots/codex-pg-budget/bot.wasm"
    assert bench.digest(wasm) == manifest["release"] and base["engine"] == bench.ENGINE
    maps = {p.stem: p for p in (bench.CACHE / "jd-sets/conf").glob("*.map26a")}
    for opp in sorted({r["opponent"] for r in base["rows"]}):
        name, expected = bench.OPPS[opp]
        assert bench.digest(bench.CACHE / name) == expected
    bench.OUT = bench.CACHE / "pg-budget-exact-dev"
    (bench.OUT / "games").mkdir(parents=True)
    jobs = [("budget", 0, r["opponent"], maps[r["map"]], r["side"], wasm) for r in base["rows"]]
    with ThreadPoolExecutor(max_workers=5) as pool:
        rows = list(pool.map(bench.one, jobs))
    for b, c in zip(base["rows"], rows, strict=True):
        assert all(b[k] == c[k] for k in ("map_hash", "engine_seed", "opponent", "side", "map"))
    fuel = sum(r["fuel_outs"] for r in rows)
    faults = sum(r["faults"] for r in rows)
    codes = sum(bool(r["diagnostic_codes"]) for r in rows)
    report = {"n": len(rows), "engine": bench.ENGINE, "base_release": base["release"],
              "release": manifest["release"], "fuel": [base["release_fuel"], fuel],
              "faults": faults, "diagnostic_cells": codes,
              "pass": fuel < base["release_fuel"] and not faults and not codes, "rows": rows}
    with (HERE / "PG_BUDGET_EXACT_DEV.json").open("x", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print({k: v for k, v in report.items() if k != "rows"}, flush=True)


if __name__ == "__main__":
    main()
