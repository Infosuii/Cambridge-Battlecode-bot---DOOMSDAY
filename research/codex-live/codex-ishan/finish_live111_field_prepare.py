"""Continue the frozen field-prepare experiment after the independently proven reader repair."""
from concurrent.futures import ThreadPoolExecutor

import ablate_dev as bench
from engine3_pool import ENGINE, HERE, SDK_ROOT, one, read
from freeze_engine3_discovery import write
from qualify_local import partition
from turn_prefix import action_prefix


if __name__ == "__main__":
    repair = read(HERE / "TURN_PREFIX_REPAIR_CONTROLS.json")
    assert repair["historical_labels_unchanged"] and repair["gameplay_difference_detected"]
    original = read(HERE / "LIVE111_FIELD_PREPARE_MECHANISM.json")
    builds = read(HERE / "LIVE111_FIELD_PREPARE_BUILDS.json")
    identity = read(HERE / "LIVE111_SOURCE_VERIFIED.json")
    assert builds["source_archive"] == identity["archive_sha256"]
    for name, record in builds["builds"].items():
        from pathlib import Path
        assert bench.digest(Path(record["path"])) == record["sha256"]
    assert builds["builds"]["off"]["sha256"] == identity["wasm_sha256"]
    assert builds["builds"]["on"]["sha256"] == builds["builds"]["rebuild"]["sha256"]
    case = original["case"]
    output = bench.CACHE / "live111-field-prepare"
    directory = output / case["opponent"] / f"{case['map']}-{case['side']}-prepare"
    before = read(bench.ROOT / case["traces"]["base"]["path"])
    after = read(directory / "turn.json")
    assert bench.digest(directory / "turn.json") == original["turn_sha256"]
    assert bench.digest(directory / "native.json") == original["native_sha256"]
    for doc in (before, after): doc["observation"].pop("input")
    native = read(directory / "native.json")
    assert native["match"]["engineBuildHash"] == ENGINE and native["diagnostics"]["detailedCaptureComplete"]
    errors = native["diagnostics"]["codes"] or any(native["diagnostics"]["botFaults"].values())
    mechanism = {**original, "original_report_sha256": bench.digest(HERE / "LIVE111_FIELD_PREPARE_MECHANISM.json"),
                 "same_action_prefix": action_prefix(before) == action_prefix(after), "reader_repair": "EXP185"}
    mechanism["pass"] = mechanism["same_own_view"] and mechanism["same_action_prefix"] and mechanism["actor_round1_removed"] and not errors
    write(HERE / "LIVE111_FIELD_PREPARE_MECHANISM_RECOUNT.json", mechanism)
    assert mechanism["pass"]
    maps = {p.stem: p for p in partition("dev")}
    baseline = read(HERE / "LIVE111_LARGE_DEV_CENSUS.json")["rows"]
    wasm = SDK_ROOT / "bots/live111-field-prepare-on/bot.wasm"
    def run(base):
        mp = maps[base["map"]]
        ref = bench.CACHE / bench.OPPS[base["opponent"]][0]
        assert bench.digest(mp) == base["map_hash"] and bench.digest(ref) == bench.OPPS[base["opponent"]][1]
        target = output / base["opponent"] / f"{base['map']}-{base['side']}-prepare"
        if target == directory:
            doc = read(target / "native.json")
            ours = "team" + base["side"]
            fuel = [x["timestamp"]["round"] for e in doc["events"] if e["kind"] == "fuelExhausted" and e["owner"]["team"] == ours for x in e["entries"]]
            cand = {**base, "arm": "prepare", "score": 1 if doc["match"]["outcome"] == ours else .5 if doc["match"]["outcome"] == "draw" else 0,
                    "fuel_outs": len(fuel), "round1_fuel_outs": fuel.count(1), "faults": doc["diagnostics"]["botFaults"][ours], "diagnostic_codes": doc["diagnostics"]["codes"]}
            cand.pop("early_events", None)
        else:
            assert not target.exists()
            cand = one(("prepare", mp, base["side"], wasm, ref), output=output / base["opponent"], opponent=base["opponent"])
        assert all(cand[k] == base[k] for k in ("map_hash", "side", "opponent", "engine_seed", "noise_seed"))
        return base, cand
    pairs = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for pair in pool.map(run, baseline):
            pairs.append(pair)
            if len(pairs) % 15 == 0: print(f"{len(pairs)}/60", flush=True)
    summary = bench.summary(pairs)
    errors = sum(bool(r["faults"] or r["opponent_faults"] or r["diagnostic_codes"]) for pair in pairs for r in pair)
    result = {"engine": ENGINE, "builds": builds, "overall": summary, "error_cells": errors,
              "pass": not errors and not summary["per_cell_fuel_regressions"] and summary["round1"][1] <= summary["round1"][0], "pairs": pairs}
    write(HERE / "LIVE111_FIELD_PREPARE_LARGE.json", result)
    print({k: v for k, v in result.items() if k not in ("pairs", "builds")}, flush=True)
