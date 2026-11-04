"""Retain the archived CPG contact policy with the verified runtime changes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

from bounded_verdict import apply
from large_roster_stress import HERE, bench, read
from pg_dash_followup import stress_cases
from pg_travel_scan import prepare as prepare_runtime
from v92_field_pack import apply_pack

OUT = bench.CACHE / "cpg-runtime-stress"
CPG = "a06ae0655dc5a473db4c783e4b436487ac39959e04eb02573090b938625657a4"


def prepare(src, enabled, packed=False, strike_only=False):
    prepare_runtime(src, enabled)
    if enabled:
        contact = 1 if strike_only else 3
        apply(src / "jd_config.h", (("#define JD_CONTACT 0\n#define JD_PROGRESS 1",
                                     f"#define JD_CONTACT {contact}\n#define JD_PROGRESS 1"),))
    if packed:
        apply_pack(src, enabled)


def native(row):
    path = OUT / "games" / f"{row['arm']}-0-{row['opponent']}-{row['map']}-{row['side']}" / "native.json"
    return read(path)


def verify(wasm, packed=False, strike_only=False):
    global OUT
    base = bench.CACHE / "cpg-archive-1.wasm"
    expected = CPG
    if packed:
        OUT = bench.CACHE / "cpg-runtime-packed-stress"
        base = bench.ROOT / "bots/codex-cpg-runtime/bot.wasm"
        expected = read(HERE / "CPG_RUNTIME_BUILDS.json")["primary"]
    elif strike_only:
        OUT = bench.CACHE / "cpg-runtime-strike-stress"
    assert bench.digest(base) == expected
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
    passed = (len(pairs) == 39 and not outcomes["per_cell_fuel_regressions"] and not draft_changes and not errors)
    passed = passed and (outcomes["fuel"] == [0, 0] if packed else outcomes["fuel"][1] < outcomes["fuel"][0])
    result = {"base_sha256": expected, "sha256": bench.digest(wasm), "engine": bench.ENGINE,
              "outcomes": outcomes, "draft_changes": draft_changes, "errors": errors, "pass": passed}
    name = ("CPG_RUNTIME_PACKED_EXACT.json" if packed else "CPG_RUNTIME_STRIKE_EXACT.json" if strike_only else
            "CPG_RUNTIME_EXACT.json")
    with (HERE / name).open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--src", type=Path)
    target.add_argument("--verify", type=Path)
    parser.add_argument("--off", action="store_true")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--packed", action="store_true")
    modes.add_argument("--strike-only", action="store_true")
    args = parser.parse_args()
    if args.src:
        prepare(args.src, not args.off, args.packed, args.strike_only)
    else:
        verify(args.verify, args.packed, args.strike_only)
