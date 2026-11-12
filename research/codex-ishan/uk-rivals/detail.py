"""Recount capture values and completed stationary runs for the frozen rival sample."""
from collections import defaultdict
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE.parents[2] / "artifacts/codex-p0/uk-targets-1104"


def read(path):
    return json.loads(path.read_bytes())


def main():
    matches = read(HERE / "SAMPLE.json")["matches"]
    captures = {r["id"]: r["captures"] for r in read(CACHE / "capture_pressure.json")}
    stationary = {r["id"]: r["runs"] for r in read(CACHE / "still-runs.json")}
    rows = []
    for match in matches:
        mid = match["id"]
        native = read(CACHE / "summaries" / f"{mid}.json")
        owners = {c["id"]: c["team"] for c in native["roster"]["champions"]}
        ours = int(match["side"].upper() == "B")
        result = {"id": mid, "rival": match["opponent"], "result": match["result"]}
        for name, team in (("ours", ours), ("opponent", 1 - ours)):
            tag = "team" + "AB"[team]
            cap = [c for c in captures[mid] if c["team"] == team and c["round"] <= 300 and c["gold"] > 0]
            still = [r for r in stationary[mid] if owners[r["actor"]] == tag and r["len"] >= 8
                     and not (r["ctx"]["enemies"] or r["fuel"] or r["gem_gain"] or r["gold_gain"])]
            result[name] = {
                "nominal_camp_gold": sum(c["gold"] for c in cap),
                "inferred_vesper_camp_gold": sum(v["gain"] for c in cap for v in c["capturers"] if v["type"] == 1),
                "elk_or_higher_hp_captures": sum(c["hp"] >= 2400 for c in cap),
                "completed_quiet_stationary_rounds": sum(r["len"] for r in still),
                "completed_quiet_stationary_rounds_near_live_camp": sum(
                    r["len"] for r in still if r["ctx"]["camp_dist"] <= 5 and r["ctx"]["camp_alive"]),
            }
        rows.append(result)
    totals = defaultdict(dict)
    for row in rows:
        group = totals[row["rival"]].setdefault(row["result"], {"n": 0, "ours": {}, "opponent": {}})
        group["n"] += 1
        for side in ("ours", "opponent"):
            for key, v in row[side].items():
                group[side][key] = group[side].get(key, 0) + v
    with (HERE / "DETAIL.json").open("x", encoding="utf8", newline="\n") as out:
        json.dump({"totals": totals, "rows": rows}, out, indent=2)
        out.write("\n")


if __name__ == "__main__":
    main()
