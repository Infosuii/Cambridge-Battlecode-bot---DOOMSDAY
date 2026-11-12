"""Recount the archived ranked sample's resource margins from native events and timelines."""
from collections import defaultdict
from math import isclose
from statistics import mean

from audit_ranked_112_114_transition import OUT, PLAN, RIVALS, numeric_summary
from audit_uploaded_112_114 import write
from discovery_metrics import timeline
from engine3_pool import HERE, bench, read
from resource_live111d_discovery import aggregate, ledger, margins

ROUNDS = (50, 100, 150, 300)
METRICS = ("earnedGold", "spentGold", "deaths")
RESULT = HERE / "RANKED_112_114_TRANSITION_RESULT.json"


def main():
    plan, audit = read(PLAN), read(RESULT)
    assert bench.digest(PLAN) == audit["plan_sha256"]
    by_match = {row["match"]: row for row in plan["cells"]}
    groups = defaultdict(list)
    rows = []
    for pinned in audit["native_rows"]:
        mid = pinned["match"]
        match = by_match[mid]
        path = OUT / "native" / f"{mid}.json"
        assert bench.digest(path) == pinned["native_sha256"]
        doc = read(path)
        ours = "team" + match["side"].upper()
        rival = "teamB" if ours == "teamA" else "teamA"
        tags = {"ours": ours, "rival": rival}
        row = {"match": mid, "group": match["group"], "window": match["window"], "result": match["result"],
               "rival_id": match["rival_id"], "rival_name": match["rival"],
               "map": match["map"], "side": match["side"], "native_sha256": pinned["native_sha256"]}
        for tag, team in tags.items():
            row[tag] = ledger(doc, team)
            for metric in METRICS:
                value = sum(float(c["metrics"][metric]) for c in doc["champions"] if c["team"] == team)
                assert isclose(value, timeline(doc, team, metric, doc["match"]["roundsStarted"] + 1), abs_tol=1e-3)
        row.update(margins(row["ours"], row["rival"]))
        row["phases"] = {}
        for r in ROUNDS:
            if doc["match"]["roundsCompleted"] < r:
                continue
            phase = {tag: ledger(doc, team, r) for tag, team in tags.items()}
            phase.update(margins(phase["ours"], phase["rival"]))
            phase["metrics"] = {metric: [timeline(doc, team, metric, r) for team in tags.values()] for metric in METRICS}
            row["phases"][str(r)] = phase
        groups["all/" + row["result"]].append(row)
        groups[row["window"] + "/" + row["result"]].append(row)
        if row["rival_id"] in RIVALS:
            groups[RIVALS[row["rival_id"]] + "/" + row["result"]].append(row)
        rows.append(row)

    reports = {}
    for label, subset in sorted(groups.items()):
        report = aggregate(subset)
        report["phases"] = {}
        for r in map(str, ROUNDS):
            selected = [dict(row, **row["phases"][r]) for row in subset if r in row["phases"]]
            phase = aggregate(selected)
            phase["mean_ours_rival_native"] = {
                metric: [mean(row["metrics"][metric][i] for row in selected) for i in (0, 1)]
                for metric in METRICS
            } if selected else None
            phase["our_spending_per_earned_gold"] = numeric_summary(
                [row["metrics"]["spentGold"][0] / row["metrics"]["earnedGold"][0] for row in selected
                 if row["metrics"]["earnedGold"][0] > 0]
            )
            report["phases"][r] = phase
        reports[label] = report
    write(HERE / "RANKED_112_114_RESOURCE_AUDIT.json",
          {"ranked_result_sha256": bench.digest(RESULT), "reports": reports, "rows": rows,
           "scope": "Descriptive native event ledger and independent terminal/phase observations. Time windows do not pin a submission. Named-rival and late-window cohorts differ by opponent mix."})
    for name, value in reports.items():
        print(name, value["n"], value["mean_components"], value["most_negative_unique"],
              value["phases"]["100"]["mean_ours_rival_native"])


if __name__ == "__main__":
    main()
