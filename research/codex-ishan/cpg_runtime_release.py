"""Retain the archived CPG contact policy with the verified runtime changes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

from bounded_verdict import apply
from large_roster_stress import HERE, bench, read
from pg_dash_followup import stress_cases
from pg_travel_scan import prepare as prepare_runtime

OUT = bench.CACHE / "cpg-runtime-stress"
CPG = "a06ae0655dc5a473db4c783e4b436487ac39959e04eb02573090b938625657a4"


def prepare(src, enabled):
    prepare_runtime(src, enabled)
    if enabled:
        apply(src / "jd_config.h", (("#define JD_CONTACT 0\n#define JD_PROGRESS 1",
                                      "#define JD_CONTACT 3\n#define JD_PROGRESS 1"),))


def native(row):
    path = OUT / "games" / f"{row['arm']}-0-{row['opponent']}-{row['map']}-{row['side']}" / "native.json"
    return read(path)


def verify(wasm):
    base = bench.CACHE / "cpg-archive-1.wasm"
    assert bench.digest(base) == CPG
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    jobs = [(arm, 0, opponent, mp, side, binary) for opponent, mp, side in stress_cases()
            for arm, binary in (("base", base), ("candidate", wasm))]
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(bench.one, jobs))
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    draft_changes = errors = 0
    for b, c in pairs:
        assert all(b[k] == c[k] for k in ("opponent", "map_hash", "engine_seed", "side"))
        old, new = native(b), native(c)
        draft_changes += old["roster"]["draft"] != new["roster"]["draft"]
        errors += any(any(doc["diagnostics"]["botFaults"].values()) or doc["diagnostics"]["codes"] for doc in (old, new))
    outcomes = bench.summary(pairs)
    passed = (len(pairs) == 39 and outcomes["fuel"][1] < outcomes["fuel"][0] and
              not outcomes["per_cell_fuel_regressions"] and not draft_changes and not errors)
    result = {"base_sha256": CPG, "sha256": bench.digest(wasm), "engine": bench.ENGINE,
              "outcomes": outcomes, "draft_changes": draft_changes, "errors": errors, "pass": passed}
    with (HERE / "CPG_RUNTIME_EXACT.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--src", type=Path)
    target.add_argument("--verify", type=Path)
    parser.add_argument("--off", action="store_true")
    args = parser.parse_args()
    if args.src:
        prepare(args.src, not args.off)
    else:
        verify(args.verify)
