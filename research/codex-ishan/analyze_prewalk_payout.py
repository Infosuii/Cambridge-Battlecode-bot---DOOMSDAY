"""Trace native camp payouts after the already-verified early clears."""
from collections import Counter
import json
from statistics import median

from verify_prewalk_clear import HERE, OUT, read


def payouts(doc, team, group, start, end):
    return sorted((e["timestamp"]["round"], int(e["value"]))
                  for event in doc["events"] if event["kind"] == "gemCollection" and event["owner"]["team"] == team
                  for e in event["entries"]
                  if start <= e["timestamp"]["round"] <= end and
                  e.get("target", {}).get("kind") == "campGroup" and e["target"]["id"] == group)


def main():
    matched = read(HERE / "PREWALK_CLEAR_EXACT_CLEARS.json")["matched"]
    rows = []
    for item in matched:
        group, round_number = item["group"], item["round"]
        team = "team" + item["side"]
        case = f"0-{item['opponent']}-{item['map']}-{item['side']}"
        base, candidate = (read(OUT / f"{arm}-{case}/native.json") for arm in ("base", "window"))
        last = min(300, round_number + 20)
        before, after = (payouts(doc, team, group, round_number, last) for doc in (base, candidate))
        base_clear = item["base_later_clear"]
        later = payouts(base, team, group, base_clear, min(300, base_clear + 20)) if base_clear and base_clear <= 300 else []
        earlier = after and (not before or after[0][0] < before[0][0])
        rows.append({k: item[k] for k in ("map", "opponent", "side", "group", "round", "base_later_clear")} |
                    {"base_window": before, "candidate_window": after, "candidate_earlier_payout": bool(earlier),
                     "base_wait": later[0][0] - base_clear if later else None,
                     "candidate_wait": after[0][0] - round_number if after else None})
    totals = Counter()
    for r in rows:
        for arm in ("base", "candidate"):
            payments = r[f"{arm}_window"]
            totals[f"{arm}_received"] += bool(payments)
            totals[f"{arm}_gems"] += sum(g for _, g in payments)
        totals["candidate_earlier"] += r["candidate_earlier_payout"]
    shared = [r for r in rows if r["base_wait"] is not None and r["candidate_wait"] is not None]
    wait = {arm: median(r[f"{arm}_wait"] for r in shared) for arm in ("base", "candidate")} if shared else {}
    result = {"n": len(rows), "totals": totals, "paired_wait_n": len(shared), "paired_wait_median": wait}
    with (HERE / "PREWALK_CLEAR_PAYOUT.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump({**result, "rows": rows}, f, indent=2)
        f.write("\n")
    print(result, flush=True)


if __name__ == "__main__":
    main()
