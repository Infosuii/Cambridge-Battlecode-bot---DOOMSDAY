"""Recount the draft, focus purchases and early damage from native release statistics."""
from collections import Counter
import json

import ablate_dev as bench
from discovery_metrics import timeline
from engine3_pool import HERE, read


def measure(row, output):
    directory = output / f"{row['noise_seed']}-{row['opponent']}" / f"{row['map']}-{row['side']}-{row['arm']}"
    doc = read(directory / "native.json")
    ours = "team" + row["side"]
    roster = [p["champion"] for p in doc["roster"]["draft"] if p["team"] == ours]
    focus = Counter()
    for event in doc["events"]:
        if event["kind"] == "buyItem" and event["owner"]["team"] == ours and event["owner"]["name"] == "Stellar":
            for entry in event["entries"]:
                if "Focus" in entry["target"]["name"]:
                    focus["all"] += int(entry["value"])
                    if entry["timestamp"]["round"] <= 300:
                        focus["before300"] += int(entry["value"])
    stellar = {"championTimelines": [r for r in doc["championTimelines"]
                                    if r["owner"]["team"] == ours and r["owner"]["name"] == "Stellar"]}
    metric = {f"team_{name}_{round_number}": timeline(doc, ours, name, round_number)
              for name in ("monsterDamageDone", "collectedGems", "earnedGold", "deaths") for round_number in (150, 300)}
    return {"roster": roster, "stellar_picks": roster.count("Stellar"), "marcella_picks": roster.count("Marcella"),
            "stellar_focus_shards": focus["all"], "stellar_focus_shards_before300": focus["before300"],
            "stellar_monster_damage300": timeline(stellar, ours, "monsterDamageDone", 300) if stellar["championTimelines"] else 0,
            **metric}


def main():
    output = bench.CACHE / "engine3-live109-stellar"
    rows = read(output / "rows.json")
    report = read(HERE / "ENGINE3_LIVE109_STELLAR_DEV.json")
    totals = {arm: Counter() for arm in ("base", "candidate")}
    mismatches = 0
    for base, candidate in zip(rows[::2], rows[1::2], strict=True):
        before, after = (measure(row, output) for row in (base, candidate))
        mapped = ["Stellar" if name == "Marcella" else "Marcella" if name == "Stellar" else name for name in before["roster"]]
        mismatches += sorted(mapped) != sorted(after["roster"])
        for arm, data in (("base", before), ("candidate", after)):
            totals[arm].update({k: v for k, v in data.items() if k != "roster"})
    moved = (totals["candidate"]["stellar_picks"] > totals["base"]["stellar_picks"] and
             totals["candidate"]["stellar_focus_shards"] > 0 and
             totals["candidate"]["stellar_monster_damage300"] > 0)
    result = {"n_pairs": len(rows) // 2, "candidate_release": report["candidate_release"],
              "totals": totals, "priority_swap_roster_mismatches": mismatches, "mechanism_moved": moved,
              "strength_gate_pass": report["pass"]}
    with (HERE / "LIVE109_STELLAR_BEHAVIOR.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
