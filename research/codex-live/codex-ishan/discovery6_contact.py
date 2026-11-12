"""Check whether early collection deficits are present before replay proximity."""
import argparse
from collections import Counter
import json
from statistics import median

from profile_discovery5 import CACHE, HERE, read, timeline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("split", choices=("discovery", "confirm"))
    split = parser.parse_args().split
    rows = read(HERE / f"DISCOVERY6_{split.upper()}.json")["rows"]
    counts = Counter()
    results = []
    for r in rows:
        ours = "team" + r["side"].upper()
        winner = "teamB" if ours == "teamA" else "teamA"
        contacts = [r[s]["first_contact"]["round"] for s in ("ours", "winner") if r[s]["first_contact"]]
        first = min(contacts, default=None)
        boundary = min(first - 1, 300) if first else 300
        data = read(CACHE / f"discovery6/{split}/summaries/{r['matchId']}.json")
        gaps = {k: timeline(data, winner, k, boundary) - timeline(data, ours, k, boundary)
                for k in ("earnedGold", "collectedGems")}
        gap_300 = r["winner"]["collected"]["300"] - r["ours"]["collected"]["300"]
        counts["winner_collected_more_at_300"] += gap_300 > 0
        counts["winner_collected_more_before_contact"] += gaps["collectedGems"] > 0
        counts["winner_collected_more_by_300_despite_no_precontact_lead"] += gap_300 > 0 and gaps["collectedGems"] <= 0
        counts["winner_more_camp_gold"] += r["winner"]["camp"]["inferred_gold"] > r["ours"]["camp"]["inferred_gold"]
        counts["winner_more_first_contact_allies"] += (
            all(r[s]["first_contact"] for s in ("ours", "winner")) and
            r["winner"]["first_contact"]["allies4"] > r["ours"]["first_contact"]["allies4"])
        results.append({"matchId": r["matchId"], "map": r["map"], "opponent": r["opponent"],
                        "contact_round": first, "sample_round": boundary, "precontact_gap": gaps, "collection_gap_300": gap_300})
    result = {"n": len(rows), "counts": counts, "median_precontact_collection_gap":
              median(r["precontact_gap"]["collectedGems"] for r in results), "rows": results}
    path = HERE / f"DISCOVERY6_CONTACT_{split.upper()}.json"
    with path.open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print({k: v for k, v in result.items() if k != "rows"})


if __name__ == "__main__":
    main()
