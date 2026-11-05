"""Recount frozen current-engine native metrics, one declared partition at a time."""
import argparse
from collections import Counter, defaultdict
import json
from statistics import mean, median

from discovery_metrics import timeline
from engine3_pool import ENGINE, HERE, read
from freeze_engine3_discovery import OUT, write

ROUNDS = (50, 100, 150, 200, 250, 300, 800)
METRICS = ("earnedGold", "collectedGems", "submittedGems", "gems", "monsterDamageDone", "monsterDamageTaken", "championDamageDone", "deaths")


def profile(doc, team):
    values = {metric: {str(r): timeline(doc, team, metric, r) for r in ROUNDS} for metric in METRICS}
    events = [(event["kind"], event["owner"], entry) for event in doc["events"] if event["owner"].get("team") == team for entry in event["entries"]]
    deposits = sorted((entry["timestamp"]["round"], int(entry["value"])) for kind, owner, entry in events if kind == "gemSubmission")
    purchases = Counter()
    champions = defaultdict(lambda: {"purchases300": Counter()})
    for kind, owner, entry in events:
        if kind == "buyItem" and entry["timestamp"]["round"] <= 300:
            family = entry["target"]["name"].split()[0]
            purchases[family] += int(entry["value"])
            champions[owner["name"]]["purchases300"][family] += int(entry["value"])
    for name in {c["name"] for c in doc["roster"]["champions"] if c["team"] == team}:
        one = {"championTimelines": [r for r in doc["championTimelines"] if r["owner"]["team"] == team and r["owner"]["name"] == name]}
        champions[name].update({metric + "300": timeline(one, team, metric, 300) for metric in METRICS})
    return {"metrics": values, "first_deposit": deposits[0][0] if deposits else None,
            "wards300": sum(kind == "wardPlacement" and entry["timestamp"]["round"] <= 300 for kind, owner, entry in events),
            "camp_clears300": sum(kind == "campClear" and entry["timestamp"]["round"] <= 300 for kind, owner, entry in events),
            "purchases300": purchases, "by_champion": champions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("partition", choices=("discovery", "confirm", "control"))
    args = parser.parse_args()
    pattern = read(HERE / "EXP165-NATIVE-PATTERNS.json")
    if args.partition == "confirm":
        assert (HERE / "LIVE109_NATIVE_DISCOVERY.json").exists()
    selected = [r for r in read(HERE / "LIVE109_DISCOVERY_SPLIT.json")["matches"] if r["partition"] == args.partition]
    assert selected and all((OUT / "summaries" / (r["matchId"] + ".json")).exists() for r in selected)
    rows = []
    for match in selected:
        doc = read(OUT / "summaries" / (match["matchId"] + ".json"))
        assert (doc["match"]["engineVersion"], doc["match"]["engineBuildHash"]) == ("3.0.0", ENGINE)
        ours = "team" + match["side"].upper()
        rival = "teamB" if ours == "teamA" else "teamA"
        us, them = profile(doc, ours), profile(doc, rival)
        u, t = us["metrics"], them["metrics"]
        first_lead = next((r for a, r in enumerate(ROUNDS[:5]) if all(
            t["earnedGold"][str(j)] - u["earnedGold"][str(j)] >= max(100, .15 * u["earnedGold"][str(j)])
            for j in ROUNDS[a:a+2])), None)
        both_banked = us["first_deposit"] is not None and them["first_deposit"] is not None
        ended = doc["match"]["roundsCompleted"] < 800
        patterns = {
            "early_income_without_deaths": t["earnedGold"]["150"] - u["earnedGold"]["150"] >= 100 and u["deaths"]["150"] == t["deaths"]["150"] == 0,
            "early_gem_acquisition": t["collectedGems"]["300"] > u["collectedGems"]["300"],
            "first_bank_later": both_banked and us["first_deposit"] > them["first_deposit"],
            "fewer_wards_300": us["wards300"] < them["wards300"],
            "damage_conversion_gap": u["monsterDamageDone"]["300"] >= t["monsterDamageDone"]["300"] and u["collectedGems"]["300"] < t["collectedGems"]["300"],
            "midgame_total_gems_deficit": not ended and u["submittedGems"]["800"] + u["gems"]["800"] < t["submittedGems"]["800"] + t["gems"]["800"]}
        assert patterns.keys() == pattern["patterns"].keys()
        rows.append({"id": match["matchId"], "opponent": match["opponent"], "group": match["group"], "result": match["result"],
                     "rounds": doc["match"]["roundsCompleted"], "first_sustained_gold_lead": first_lead,
                     "both_deposit": both_banked, "ended_before800": ended, "patterns": patterns, "ours": us, "rival": them})
    counts = Counter(k for row in rows for k, value in row["patterns"].items() if value)
    per_opponent = {}
    for opponent in sorted({r["opponent"] for r in rows}):
        subset = [r for r in rows if r["opponent"] == opponent]
        per_opponent[opponent] = {"n": len(subset), "patterns": dict(Counter(k for r in subset for k, v in r["patterns"].items() if v))}
    margins = {metric: {str(r): {"median_ours_rival": [median(row[side]["metrics"][metric][str(r)] for row in rows) for side in ("ours", "rival")],
                               "mean_rival_minus_ours": mean(row["rival"]["metrics"][metric][str(r)] - row["ours"]["metrics"][metric][str(r)] for row in rows)}
                        for r in (150, 300, 800)} for metric in METRICS}
    result = {"partition": args.partition, "n": len(rows), "groups": len({r["group"] for r in rows}), "engine": ENGINE,
              "patterns": counts, "both_deposit": sum(r["both_deposit"] for r in rows), "running_at800": sum(not r["ended_before800"] for r in rows),
              "first_sustained_gold_lead": dict(Counter(r["first_sustained_gold_lead"] or "none" for r in rows)),
              "margins": margins, "per_opponent": per_opponent, "rows": rows}
    write(HERE / f"LIVE109_NATIVE_{args.partition.upper()}.json", result)
    print(json.dumps({k: result[k] for k in ("partition", "n", "groups", "patterns", "both_deposit", "running_at800", "first_sustained_gold_lead")}, indent=2), flush=True)
    print(json.dumps({m: result["margins"][m] for m in ("earnedGold", "collectedGems", "deaths")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
