"""Screen the archived unsupported-contact retreat in isolation."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json

from bounded_verdict import apply
from large_roster_stress import HERE, bench, read
from pg_travel_scan import prepare as prepare_travel
from qualify_local import DEV, build, partition

OUT = bench.CACHE / "contact-retreat-dev-r2"
SEEDS = (6311, 7333)


def prepare(src, enabled):
    prepare_travel(src, enabled)
    if enabled:
        apply(src / "jd_config.h", (("#define JD_CONTACT 0\n#define JD_PROGRESS 1",
                                      "#define JD_CONTACT 2\n#define JD_PROGRESS 1"),))
    apply(src / "bot.cpp", (
        ("    if (!in_danger && nearest && !(target && target_ttk <= 1.0f)) {",
         """    if (!in_danger && nearest && !(target && target_ttk <= 1.0f) &&
        rb::fits(0, rb::kReserve.decide + rb::kTailReserve)) {"""),
    ))


def play(job):
    row = bench.one(job)
    arm, seed, opponent, mp, side, _ = job
    native = read(OUT / "games" / f"{arm}-{seed}-{opponent}-{mp.stem}-{side}" / "native.json")
    team = "team" + side
    lost = sum(int(e["value"]) for event in native["events"]
               if event["kind"] == "gemLoss" and event["owner"]["team"] == team
               for e in event["entries"] if e["timestamp"]["round"] <= 600)
    return {**row, "lost_600": lost, "errors": bool(any(native["diagnostics"]["botFaults"].values()) or
                                                  native["diagnostics"]["codes"])}


def main():
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    parent = bench.ROOT / "bots/codex-pg-travel-scan"
    reference = read(HERE / "PG_TRAVEL_SCAN_BUILDS.json")["primary"]
    assert bench.digest(parent / "bot.wasm") == reference
    candidate = OUT / "candidate-source/src"
    prepare(candidate, True)
    arms = {"base": parent / "src", "retreat": candidate}
    for opponent in DEV:
        file, digest = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / file) == digest
    binaries = {(arm, seed): build(src, OUT / f"{arm}-{seed}", seed)
                for arm, src in arms.items() for seed in SEEDS}
    jobs = [(arm, seed, o, m, side, binaries[arm, seed]) for m in partition("conf")
            for o in DEV for side in "AB" for seed in SEEDS for arm in arms]
    rows = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for row in pool.map(play, jobs):
            rows.append(row)
            if len(rows) % 128 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    assert all(all(b[k] == c[k] for k in ("noise_seed", "opponent", "map_hash", "engine_seed", "side")) for b, c in pairs)
    lost = defaultdict(int)
    for b, c in pairs:
        lost[b["opponent"]] += c["lost_600"] - b["lost_600"]
    outcomes = bench.summary(pairs)
    errors = sum(r["errors"] for r in rows)
    passed = not errors and outcomes["delta_pp"] >= -2 and sum(lost.values()) < 0 and sum(v < 0 for v in lost.values()) >= 2
    result = {"engine": bench.ENGINE, "reference_release": reference, "n": len(pairs),
              "binaries": {f"{a}-{s}": bench.digest(p) for (a, s), p in binaries.items()},
              "outcomes": outcomes, "lost_delta": dict(lost), "error_cells": errors, "pass": passed}
    with (HERE / "CONTACT_RETREAT_PROBE.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
