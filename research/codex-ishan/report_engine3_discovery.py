"""Aggregate preregistered native and replay patterns without fitting a policy."""
from collections import Counter, defaultdict
import argparse
import json
from statistics import mean, median

from engine3_pool import HERE, read
from freeze_engine3_discovery import write


def grouped_rates(rows, eligible, predicate):
    groups = defaultdict(list)
    values = []
    for row in rows:
        if eligible(row):
            value = bool(predicate(row))
            values.append(value)
            groups[row["group"]].append(value)
    return {"n": len(values), "count": sum(values), "groups": len(groups),
            "game_rate": mean(values) if values else None,
            "equal_group_rate": mean(mean(v) for v in groups.values()) if groups else None}


def main(prefix="LIVE109"):
    native_patterns = read(HERE / "EXP165-NATIVE-PATTERNS.json")["patterns"]
    replay_patterns = read(HERE / "EXP165-REPLAY-PATTERNS.json")["patterns"]
    result = {"scope": "Outcome-selected descriptive current-engine cases/controls; group-cluster rates, imperfect source identity. Not causal, not a strength or release test.", "native": {}, "replay": {}}
    for partition in ("discovery", "confirm", "control"):
        data = read(HERE / f"{prefix}_NATIVE_{partition.upper()}.json")
        rows = data["rows"]
        report = {"n": len(rows), "groups": data["groups"], "patterns": {}}
        for pattern in native_patterns:
            eligible = (lambda r: r["both_deposit"]) if pattern == "first_bank_later" else (lambda r: not r["ended_before800"]) if pattern == "midgame_total_gems_deficit" else (lambda r: True)
            report["patterns"][pattern] = grouped_rates(rows, eligible, lambda r: r["patterns"][pattern])
        result["native"][partition] = report
        replay = read(HERE / f"{prefix}_REPLAY_{partition.upper()}.json")["rows"]
        predicates = {
            "less_capture_gold300": lambda r: r["ours"]["inferred_capture_gold300"] < r["rival"]["inferred_capture_gold300"],
            "less_grouped_early": lambda r: r["ours"]["grouped_early"] < r["rival"]["grouped_early"],
            "more_no_hit_deaths600": lambda r: r["ours"]["no_pvp_basic_or_cast_deaths600"] > r["rival"]["no_pvp_basic_or_cast_deaths600"],
            "slower_capture_conversion300": lambda r: median(r["ours"]["inferred_clear_to_capture_delays"]) > median(r["rival"]["inferred_clear_to_capture_delays"])}
        def eligibility(name, row):
            if name == "slower_capture_conversion300":
                return all(len(row[side]["inferred_clear_to_capture_delays"]) >= 2 for side in ("ours", "rival"))
            if name == "less_grouped_early":
                return all(row[side]["grouped_early"] is not None for side in ("ours", "rival"))
            return True
        replay_report = {"n": len(replay), "groups": len({r["group"] for r in replay}),
                         "patterns": {p: grouped_rates(replay, lambda r: eligibility(p, r), predicates[p]) for p in replay_patterns},
                         "deaths600": [sum(r[side]["deaths600"] for r in replay) for side in ("ours", "rival")],
                         "no_hit_deaths600": [sum(r[side]["no_pvp_basic_or_cast_deaths600"] for r in replay) for side in ("ours", "rival")],
                         "median_capture_gold300": [median(r[side]["inferred_capture_gold300"] for r in replay) for side in ("ours", "rival")]}
        result["replay"][partition] = replay_report
    write(HERE / f"{prefix}_DISCOVERY_PATTERN_REPORT.json", result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", default="LIVE109")
    main(parser.parse_args().prefix)
