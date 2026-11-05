"""Measure actor-specific banking and bag loss from detailed match statistics."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

GEM_EVENTS = {"gemCollection", "gemSubmission", "gemLoss"}


def measure(stats, threshold=30, horizon=60):
    match = stats["match"]
    assert stats["diagnostics"]["detailedCaptureComplete"]
    assert not any(stats["diagnostics"]["botFaults"].values())
    rosters = {c["id"]: c["team"] for c in stats["roster"]["champions"]}
    events = defaultdict(list)
    deaths = set()
    for stream in stats["events"]:
        if stream["kind"] not in GEM_EVENTS | {"death"}:
            continue
        actor = stream["owner"]["id"]
        assert rosters[actor] == stream["owner"]["team"]
        for entry in stream["entries"]:
            tick = entry["timestamp"]
            if stream["kind"] == "death":
                deaths.add((actor, tick["input"]))
            else:
                events[actor].append((tick["ordinal"], tick["input"], tick["round"],
                                      stream["kind"], int(entry["value"])))
    ending_bags = {s["owner"]["id"]: int(s["runs"][-1]["value"])
                   for s in stats["championTimelines"] if s["metric"] == "gems"}
    totals = {team: Counter() for team in set(rosters.values())}
    episodes = []
    for actor, team in rosters.items():
        totals_team = totals[team]
        bag = 0
        opportunity = None
        for _, input_id, round_no, kind, amount in sorted(events[actor]):
            assert amount >= 0
            if opportunity is not None and round_no > opportunity["round"] + horizon:
                episodes.append({**opportunity, "outcome": "unresolved_at_horizon"})
                opportunity = None
            if kind == "gemCollection":
                before = bag
                bag += amount
                totals_team["collected"] += amount
                if before < threshold <= bag:
                    opportunity = {"actor": actor, "team": team, "round": round_no, "bag": bag}
                continue
            bag -= amount
            assert bag >= 0
            at_death = kind == "gemLoss" and (actor, input_id) in deaths
            if kind == "gemSubmission":
                totals_team["banked"] += amount
                totals_team["large_deposits"] += int(amount >= threshold)
            elif at_death:
                totals_team["death_gems"] += amount
                totals_team["large_death_losses"] += int(amount >= threshold)
            else:
                totals_team["other_gem_loss"] += amount
            if opportunity is not None and (amount or at_death):
                episodes.append({**opportunity, "end_round": round_no, "amount": amount,
                                 "outcome": "deposited" if kind == "gemSubmission" else
                                 "lost_at_death" if at_death else "other_loss"})
                opportunity = None
        assert bag == ending_bags.get(actor, 0), (actor, bag, ending_bags.get(actor))
        totals_team["held_at_end"] += bag
        if opportunity is not None:
            outcome = ("unresolved_at_horizon" if match["roundsCompleted"] >= opportunity["round"] + horizon
                       else "censored_by_match_end")
            episodes.append({**opportunity, "outcome": outcome})
    for team in stats["teams"]:
        assert totals[team["team"]]["banked"] == int(team["submittedGems"])
    return {"map_sha256": match["mapHash"], "seed": match["seed"],
            "teams": {team: dict(counts) for team, counts in sorted(totals.items())},
            "episodes": episodes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stats", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    matches = [measure(json.loads(path.read_text())) for path in args.stats]
    outcomes = Counter(e["outcome"] for match in matches for e in match["episodes"])
    report = {
        "scope": "Detailed engine statistics with actor-specific gem accounting.",
        "opportunity": "Start when an actor crosses 30 held gems. Track its first positive deposit or loss for 60 rounds.",
        "limits": "Timed-out and censored opportunities are explicit. Events do not identify interrupted channels, visibility or interception intent.",
        "matches_reconciled": len(matches), "outcomes": outcomes, "matches": matches,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(len(matches), dict(outcomes))


if __name__ == "__main__":
    main()
