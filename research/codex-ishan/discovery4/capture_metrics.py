"""Summarize the frozen capture conversion checks for one ranked replay split."""
import argparse
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CACHE = ROOT / "artifacts/codex-p0/discovery4"
ROUND_LIMIT = 300


def read(path):
    return json.loads(path.read_bytes())


def team_metrics(row, team):
    captures = [c for c in row["captures"]
                if c["team"] == team and c["round"] <= ROUND_LIMIT and c["gold"] > 0]
    delays = []
    stolen = []
    for capture in captures:
        attackers = {h["team"] for h in capture["hitters"]}
        assert attackers <= {0, 1}, attackers
        if attackers == {team}:
            delay = capture["round"] - capture["clear_end"]
            assert delay >= 0, capture
            delays.append(delay)
        if attackers == {1 - team}:
            stolen.append(capture)

    def gold(records):
        return sum(sum(c["gain"] for c in record["capturers"]) for record in records)

    return {
        "captures": len(captures),
        "inferred_gold": gold(captures),
        "unattributed": sum(not c["hitters"] for c in captures),
        "single_team_attacker_captures": len(delays),
        "median_clear_to_capture": median(delays) if len(delays) >= 2 else None,
        "interruptions_near_enemy": sum(
            c["round"] <= ROUND_LIMIT and c["team"] == team and c["near_enemy"] and c["gold"] > 0
            for c in row["interruptions"]
        ),
        "other_team_only_attacker_captures": len(stolen),
        "other_team_only_attacker_gold": gold(stolen),
        "other_team_only_attacker_rounds": [c["round"] for c in stolen],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("partition", choices=("discovery", "confirm"))
    a = p.parse_args()
    local = CACHE / a.partition
    games = read(local / "matches.json")
    records = {r["id"]: r for r in read(local / "analysis/capture_pressure.json")}
    assert records.keys() == {m["matchId"] for m in games}

    comparisons = [
        ("inferred_gold", 1),
        ("median_clear_to_capture", 0),
        ("interruptions_near_enemy", 0),
        ("other_team_only_attacker_captures", 1),
    ]
    rows = []
    for m in games:
        ours = {"A": 0, "B": 1}[m["side"].upper()]
        r = records[m["matchId"]]
        rows.append({
            "match_id": m["matchId"],
            "ours": team_metrics(r, ours),
            "winner": team_metrics(r, 1 - ours),
        })

    counts = {}
    for metric, higher in comparisons:
        pairs = [(r["ours"][metric], r["winner"][metric]) for r in rows]
        differences = [pair[higher] - pair[1 - higher] for pair in pairs if None not in pair]
        counts[metric] = {
            "supported": len(differences),
            "directional_games": sum(x > 0 for x in differences),
            "mean_positive_difference": (
                sum(x for x in differences if x > 0) / sum(x > 0 for x in differences)
                if any(x > 0 for x in differences) else None
            ),
        }
    result = {"n": len(rows), "counts": counts, "rows": rows}
    (OUT / f"CAPTURES_{a.partition.upper()}.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
