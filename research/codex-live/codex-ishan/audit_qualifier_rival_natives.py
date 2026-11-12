"""Recount the fixed three-rival native sample, with replay-summary repeats separated."""
from collections import Counter, defaultdict
from math import isclose
from statistics import mean

from audit_ranked_112_114_transition import OUT as PREVIOUS, PLAN as PREVIOUS_PLAN, event_rounds
from audit_uploaded_112_114 import write
from discovery_metrics import timeline
from engine3_pool import ENGINE, HERE, bench, read
from freeze_qualifier_rival_inventory import OUT, PLAN
from resource_live111d_discovery import aggregate, ledger, margins

RESULT = HERE / "QUALIFIER_RIVAL_NATIVE_20261109.json"
METRICS = ("earnedGold", "spentGold", "deaths", "monsterDamageDone", "championDamageDone")
ROUNDS = (50, 100, 150, 300, 600, 800)


def checked_native(row, older):
    directory = PREVIOUS if row["prior_native"] else OUT
    path = directory / "native" / (row["id"] + ".json")
    sha = bench.digest(path)
    if row["prior_native"]:
        assert sha == older[row["id"]]["native_sha256"]
    doc = read(path)
    match, diag = doc["match"], doc["diagnostics"]
    assert (match["engineVersion"], match["engineBuildHash"]) == ("3.0.0", ENGINE)
    assert diag["detailedCaptureComplete"]
    team = "team" + row["side"].upper()
    opponent = "teamB" if team == "teamA" else "teamA"
    assert match["outcome"] == {"win": team, "loss": opponent, "draw": "draw"}[row["result"]]
    arms = {"ours": team, "rival": opponent}
    record = dict(row, native_sha256=sha, map_sha256=match["mapHash"], rounds=match["roundsCompleted"])
    for tag, side in arms.items():
        record[tag] = ledger(doc, side)
        for metric in METRICS:
            observed = sum(float(c["metrics"][metric]) for c in doc["champions"] if c["team"] == side)
            assert isclose(observed, timeline(doc, side, metric, match["roundsStarted"] + 1), abs_tol=1e-3)
    record.update(margins(record["ours"], record["rival"]))
    record["roster"] = {tag: sorted({c["name"] for c in doc["roster"]["champions"] if c["team"] == side})
                        for tag, side in arms.items()}
    record["fuel"] = {tag: len(event_rounds(doc, side, "fuelExhausted")) for tag, side in arms.items()}
    record["faults"] = {tag: diag["botFaults"][side] for tag, side in arms.items()}
    record["codes"] = diag["codes"]
    record["phases"] = {}
    for round_number in ROUNDS:
        if match["roundsCompleted"] < round_number:
            continue
        part = {tag: ledger(doc, side, round_number) for tag, side in arms.items()}
        part.update(margins(part["ours"], part["rival"]))
        part["metrics"] = {metric: [timeline(doc, side, metric, round_number) for side in arms.values()] for metric in METRICS}
        record["phases"][str(round_number)] = part
    return record


def report(rows):
    value = aggregate(rows)
    value["record"] = dict(Counter(r["result"] for r in rows))
    value["group_record"] = {}
    for group in sorted({r["group"] for r in rows}):
        value["group_record"][group] = dict(Counter(r["result"] for r in rows if r["group"] == group))
    value["roster_presence"] = {tag: dict(Counter(name for r in rows for name in r["roster"][tag]))
                                for tag in ("ours", "rival")}
    value["fuel"] = {tag: sum(r["fuel"][tag] for r in rows) for tag in ("ours", "rival")}
    value["faults"] = {tag: sum(r["faults"][tag] for r in rows) for tag in ("ours", "rival")}
    value["code_cells"] = sum(bool(r["codes"]) for r in rows)
    value["phases"] = {}
    for key in map(str, ROUNDS):
        selected = [dict(row, **row["phases"][key]) for row in rows if key in row["phases"]]
        phase = aggregate(selected)
        phase["mean_ours_rival_native"] = {
            metric: [mean(row["metrics"][metric][i] for row in selected) for i in (0, 1)]
            for metric in METRICS
        } if selected else None
        value["phases"][key] = phase
    selected = [r for r in rows if "300" in r["phases"]]
    value["after300"] = {"n": len(selected)}
    for metric in ("camp", "clears"):
        values = [r["ours"][metric] - r["rival"][metric] - r["phases"]["300"]["ours"][metric] + r["phases"]["300"]["rival"][metric]
                  for r in selected]
        value["after300"][metric] = {"mean_ours_minus_rival": mean(values) if values else None,
                                      "negative": sum(v < 0 for v in values), "equal": sum(v == 0 for v in values)}
    return value


def main():
    plan = read(PLAN)
    assert bench.digest(PREVIOUS_PLAN) == plan["prior_plan_sha256"]
    assert {name: bench.digest(OUT / name) for name in plan["page_sha256"]} == plan["page_sha256"]
    old = read(HERE / "RANKED_112_114_TRANSITION_RESULT.json")
    assert old["plan_sha256"] == plan["prior_plan_sha256"]
    older = {r["match"]: r for r in old["native_rows"]}
    selected = [row for row in plan["named"] if row["native_requested"]]
    assert len(selected) == 165 and sum(r["prior_native"] for r in selected) == 20
    rows = [checked_native(row, older) for row in selected]
    repeats = defaultdict(list)
    for row in rows:
        key = (row["kind"], row["rival_id"], row["map_id"], row["side"], row["result"], row["native_sha256"])
        repeats[key].append(row)
    distinct = [items[0] for items in repeats.values()]
    duplicate_ids = [[row["id"] for row in items] for items in repeats.values() if len(items) > 1]
    reports = {}
    for key in plan["buckets"]:
        kind, name = key.split("/")
        reports[key] = {}
        for scope, cohort in (("all", rows), ("unique_native", distinct)):
            subset = [r for r in cohort if r["kind"] == kind and r["name"] == name]
            if subset:
                reports[key][scope] = {"all": report(subset), **{
                    outcome: report([r for r in subset if r["result"] == outcome])
                    for outcome in ("win", "loss")
                }}
    write(RESULT, {"plan_sha256": bench.digest(PLAN), "matched_games": len(rows),
                   "unique_native": len(distinct), "duplicates": duplicate_ids, "reports": reports, "rows": rows,
                   "scope": "Ranked and unranked kept separate. Resource identities verified against native final totals and phase timelines. Native repeats collapse only within same mode, opponent, map, side, and outcome. No submission identity or causal strategy claim."})
    for name, bucket in reports.items():
        if bucket:
            selected = bucket["unique_native"]["loss"]
            print(name, bucket["all"]["all"]["record"], bucket["unique_native"]["all"]["record"],
                  selected["most_negative_unique"], selected["after300"], flush=True)


if __name__ == "__main__":
    main()
