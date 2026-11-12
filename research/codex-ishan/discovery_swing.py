"""Recount frozen patterns and test the early earned-gold marker on win controls."""
import json
from pathlib import Path
from statistics import mean

from discovery_metrics import CACHE, OUT, ROUNDS, timeline

def read(p):
    return json.loads(p.read_bytes())

discovery=read(OUT/"LOSS_DISCOVERY.json")["rows"]
confirm=read(OUT/"LOSS_CONFIRM.json")["rows"]
pairs={
 "earned_gold_r150":lambda r:r["gold_gap_150"],
 "opposing_half_clears_after300":lambda r:r["winner"]["enemy_clears_after300"]-r["ours"]["enemy_clears_after300"],
 "wards":lambda r:r["winner"]["wards"]-r["ours"]["wards"],
 "banked_gems_before300":lambda r:r["winner"]["banked_300"]-r["ours"]["banked_300"],
 "bruiser_shards_before300":lambda r:r["winner"]["bruiser_before300"]-r["ours"]["bruiser_before300"],
}
def measure(rows,metric):
    vals=[metric(r) for r in rows]
    positive=[v for v in vals if v>0]
    return {"n":len(vals),"positive":len(positive),"mean_positive_swing":mean(positive) if positive else None,
            "frequency_times_swing":sum(positive)/len(vals),"mean_paired_difference":mean(vals)}

losses={r["id"]:r for r in discovery+confirm}
controls=read(OUT/"DISCOVERY_WIN_CONTROLS.json")
result=[]
for c in controls:
    s=read(CACHE/"win-controls"/(c["matchId"]+".json"))
    us="team"+c["side"].upper()
    them="teamB" if us=="teamA" else "teamA"
    assert s["match"]["engineVersion"]=="2.0.0" and s["match"]["outcome"]==us
    our=[timeline(s,us,"earnedGold",t) for t in ROUNDS]
    their=[timeline(s,them,"earnedGold",t) for t in ROUNDS]
    has=[b-a>=100 and b-a>=0.15*a for a,b in zip(our,their,strict=True)]
    marker=next((t for i,t in enumerate(ROUNDS[:5]) if has[i] and has[i+1]),None)
    result.append({**c,"win_marker_first_round":marker,
                   "loss_marker_first_round":losses[c["loss_id"]]["first_sustained_gold_lead"]})
report={
 "paired_swing":{k:{"discovery":measure(discovery,f),"confirmation":measure(confirm,f)} for k,f in pairs.items()},
 "matched_gold_marker":{"n":len(result),
                        "loss_present":sum(c["loss_marker_first_round"] is not None for c in result),
                        "win_present":sum(c["win_marker_first_round"] is not None for c in result),
                        "same_map":sum(c["same_map"] for c in result),"same_side":sum(c["same_side"] for c in result)},
 "note":"Frequency times observed positive swing is a descriptive ceiling in the metric's original units, not wins or an achievable causal effect."
}
(OUT/"DISCOVERY_SWING.json").write_text(json.dumps({**report,"controls":result},ensure_ascii=False,indent=2)+"\n",encoding="utf8",newline="\n")
print(json.dumps(report,indent=2))
