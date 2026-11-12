"""Reopen the full matched native matrix and quantify when fuel-outs occur."""
from statistics import mean, median

from audit_uploaded_112_114 import write
from audit_uploaded_112_114_pool import RUN
from engine3_pool import HERE, bench, read

POOL = HERE / "UPLOADED_112_114_POOL_RESULT.json"
BINS = ((1, 1), (2, 50), (51, 150), (151, 300), (301, 600), (601, None))


def in_bin(r, lo, hi):
    return r >= lo and (hi is None or r <= hi)


def bins(rounds):
    return {f"{lo}-{hi or 'end'}": sum(in_bin(r, lo, hi) for r in rounds) for lo, hi in BINS}


def main():
    frozen = read(POOL)
    arms = {name: {} for name in frozen["reports"]}
    for row in frozen["rows"]:
        cell = (row["map"], row["side"])
        root = RUN / f'{row["map"]}-{row["side"]}-{row["arm"]}'
        native = root / "native.json"
        assert bench.digest(native) == row["native_sha256"]
        doc = read(native)
        team = "team" + row["side"]
        rounds = [int(e["timestamp"]["round"]) for g in doc["events"]
                  if g["kind"] == "fuelExhausted" and g["owner"].get("team") == team for e in g["entries"]]
        assert len(rounds) == row["fuel_outs"] and rounds.count(1) == row["round1_fuel_outs"]
        assert row["map_hash"] == doc["match"]["mapHash"] and row["engine_seed"] == doc["match"]["seed"]
        assert all(1 <= r <= doc["match"]["roundsStarted"] for r in rounds)
        assert cell not in arms[row["arm"]]
        arms[row["arm"]][cell] = (rounds, doc["match"]["roundsCompleted"])
    keys = set(arms["v92"])
    assert len(keys) == 172 and all(arm.keys() == keys for arm in arms.values())
    report = {}
    for name, arm in arms.items():
        values = list(arm.values())
        round_bins = bins([r for rounds, _ in values for r in rounds])
        assert sum(round_bins.values()) == frozen["reports"][name]["fuel"]
        report[name] = {"round_bins": round_bins, "mean_rounds": mean(r for _, r in values),
                        "median_rounds": median(r for _, r in values)}
    subset = {}
    for until in (150, 300, 600, 800):
        cells = [k for k in keys if all(arm[k][1] >= until for arm in arms.values())]
        subset[str(until)] = {"all_arms_reached_round": len(cells),
                              "fuel_through_round": {a: sum(r <= until for k in cells for r in arm[k][0])
                                                     for a, arm in arms.items()}}
    pair_comparison = {}
    for a, b in (("v92", "v113"), ("v112", "v113"), ("v112", "v114"), ("v113", "v114")):
        directions = {}
        for lo, hi in BINS:
            diffs = [sum(in_bin(r, lo, hi) for r in arms[b][k][0]) - sum(in_bin(r, lo, hi) for r in arms[a][k][0]) for k in keys]
            directions[f"{lo}-{hi or 'end'}"] = {"decreased_cells": sum(d < 0 for d in diffs),
                                                 "tied_cells": sum(d == 0 for d in diffs),
                                                 "increased_cells": sum(d > 0 for d in diffs)}
        pair_comparison[f"{a}->{b}"] = directions
    write(HERE / "UPLOADED_112_114_FUEL_PHASES.json",
          {"pool_sha256": bench.digest(POOL), "reopened": len(keys) * len(arms), "all": report,
           "common_round_exposure": subset, "paired_directions": pair_comparison,
           "limits": "Event timing only. Completed-round matching is descriptive and may select on game trajectory. Native summaries do not expose the code path that exhausted fuel."})
    print(report, subset, flush=True)


if __name__ == "__main__":
    main()
