"""Test switching from opening gold weight based on the existing gear estimate."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json

from bounded_verdict import apply
from cpg_runtime_release import prepare as prepare_runtime
from large_roster_stress import HERE, bench, read
from qualify_local import DEV, build, partition

OUT = bench.CACHE / "opening-gear-dev"
SEEDS = (6917, 1109)


def prepare(src):
    prepare_runtime(src, True, packed=True)
    apply(src / "bot.h", (
        ("    float gold_weight() const {", "    bool opening_gear_ready = false;\n    float gold_weight() const {"),
        ("        const float weight = tune::kGoldWeight * (round < UB_GOLD_UNTIL ?",
         "        const float weight = opening_gear_ready ? tune::kGoldWeight : tune::kGoldWeight * (round < UB_GOLD_UNTIL ?"),
    ))
    apply(src / "bot.cpp", (
        ("    focus = info.focus;\n    range = info.attack_range;",
         """    focus = info.focus;
    const bool in_opening = round < std::max(UB_GOLD_FADE, UB_GOLD_UNTIL);
    opening_gear_ready = in_opening && APEX_BOOT_ITEMS > 0 &&
        my_items() >= static_cast<float>(APEX_BOOT_ITEMS);
    range = info.attack_range;"""),
    ))


def play(job):
    row = bench.one(job)
    arm, seed, opponent, mp, side, _ = job
    summary = read(OUT / "games" / f"{arm}-{seed}-{opponent}-{mp.stem}-{side}/native.json")
    team = "team" + side
    gems = sum(int(e["value"]) for event in summary["events"]
               if event["kind"] == "gemCollection" and event["owner"]["team"] == team
               for e in event["entries"] if e["timestamp"]["round"] <= 300
               and e.get("target", {}).get("kind") == "campGroup")
    errors = bool(any(summary["diagnostics"]["botFaults"].values()) or summary["diagnostics"]["codes"])
    return {**row, "camp_gems_300": gems, "errors": errors}


def main():
    bench.OUT = OUT
    (OUT / "games").mkdir(parents=True)
    parent = bench.ROOT / "bots/codex-cpg-runtime-packed"
    expected = read(HERE / "CPG_RUNTIME_PACKED_BUILDS.json")["primary"]
    assert bench.digest(parent / "bot.wasm") == expected
    candidate = OUT / "source/src"
    prepare(candidate)
    arms = {"base": parent / "src", "gear": candidate}
    for opponent in DEV:
        filename, digest = bench.OPPS[opponent]
        assert bench.digest(bench.CACHE / filename) == digest
    bins = {(arm, seed): build(src, OUT / f"{arm}-{seed}", seed)
            for arm, src in arms.items() for seed in SEEDS}
    jobs = [(arm, seed, o, mp, side, bins[arm, seed]) for mp in partition("conf") for o in DEV
            for side in "AB" for seed in SEEDS for arm in arms]
    rows = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for row in pool.map(play, jobs):
            rows.append(row)
            if len(rows) % 128 == 0:
                print(f"{len(rows)}/{len(jobs)}", flush=True)
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    by_opponent = defaultdict(list)
    for b, c in pairs:
        assert all(b[k] == c[k] for k in ("noise_seed", "map_hash", "engine_seed", "side", "opponent"))
        by_opponent[b["opponent"]].append((b, c))
    outcome = bench.summary(pairs)
    strata = {o: bench.summary(p) for o, p in by_opponent.items()}
    gems = {o: sum(c["camp_gems_300"] - b["camp_gems_300"] for b, c in p) for o, p in by_opponent.items()}
    errors = sum(r["errors"] for r in rows)
    passed = (len(pairs) == 256 and not errors and outcome["delta_pp"] > 0 and
              all(s["delta_pp"] >= -10 for s in strata.values()) and
              sum(gems.values()) > 0 and sum(g > 0 for g in gems.values()) >= 2)
    result = {"engine": bench.ENGINE, "reference": expected, "outcome": outcome, "strata": strata,
              "binaries": {f"{a}-{s}": bench.digest(p) for (a, s), p in bins.items()},
              "camp_gem_delta": gems, "errors": errors, "pass": passed}
    with (HERE / "OPENING_GEAR_DEV.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({**result, "rows": rows}, out, indent=2)
        out.write("\n")
    print({k: v for k, v in result.items() if k not in ("binaries", "strata")}, flush=True)


if __name__ == "__main__":
    main()
