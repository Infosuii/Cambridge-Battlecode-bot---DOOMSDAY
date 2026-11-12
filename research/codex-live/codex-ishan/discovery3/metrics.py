"""Compare the winner to DOOMSDAY using only the requested frozen split."""
import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import mean, median

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
CACHE=ROOT/"artifacts/codex-p0/discovery3"
ROUNDS=(50,100,150,200,250,300,600)
def read(p): return json.loads(p.read_bytes())
def timeline(s,team,metric,round):
    series=[row["runs"] for row in s["championTimelines"] if row["owner"]["team"]==team and row["metric"]==metric]
    assert series,(team,metric)
    acc=0
    for runs in series:
        t=0
        for run in runs:
            v=float(run["value"])
            t+=run["duration"]
            if t>round:
                break
        acc+=v
    return acc

def row(m,s,profile,death):
    ours="team"+m["side"].upper()
    theirs="teamB" if ours=="teamA" else "teamA"
    assert s["match"]["engineVersion"]=="2.0.0" and s["match"]["outcome"]==theirs
    g={tag:{str(t):timeline(s,team,"earnedGold",t) for t in ROUNDS} for tag,team in (("us",ours),("winner",theirs))}
    gaps=[g["winner"][str(t)]-g["us"][str(t)] for t in ROUNDS]
    lead=[gap>=100 and gap>=0.15*g["us"][str(t)] for t,gap in zip(ROUNDS,gaps,strict=True)]
    first=next((t for i,t in enumerate(ROUNDS[:5]) if lead[i] and lead[i+1]),None)
    def side(p,t):
        sh=p["us" if t==0 else "them"]
        ds=[d for d in death["deaths"] if d["team"]==(0 if (ours=="teamA")==(t==0) else 1)]
        return {"first_deposit":sh["first_deposit"],"banked_300":sum(x[1] for x in sh["deposits"][:2]),
                "deposits":sum(x[0] for x in sh["deposits"]),"wards":sum(sum(x) for x in sh["wards"]),
                "enemy_clears_after300":sum(x[2] for x in sh["clears"][2:]),
                "early_deaths":sum(sh["deaths"][0]),"bruiser_before300":sum(x.get("Bruiser",0) for x in sh["shards_by_phase"][:2]),
                "treasure_open":bool(sh["item_order"] and sh["item_order"][0][1].startswith("Treasure")),
                "deaths_through600":len(ds),"no_pvp_basic_or_cast":sum(d["pvp_attacks"]==0 and d["casts"]==0 for d in ds)}
    return {"id":m["matchId"],"map":m["map"],"opponent":m["opponent"],"ours":side(profile,0),"winner":side(profile,1),
            "gold":g,"first_sustained_gold_lead":first,"gold_gap_150":gaps[2],
            "rounds":s["match"]["roundsCompleted"]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("partition",choices=("discovery","confirm"))
    a=p.parse_args()
    local=CACHE/a.partition
    profiles={r["matchId"]:r for r in read(local/"analysis/summary_rows.json")}
    deaths={r["id"]:r for r in read(local/"analysis/death_context.json")}
    rows=[]
    for m in read(local/"matches.json"):
        mid=m["matchId"]
        rows.append(row(m,read(local/"summaries"/f"{mid}.json"),profiles[mid],deaths[mid]))
    keys=rows[0]["ours"].keys()
    metrics={}
    for k in keys:
        arms=[[r[who][k] for r in rows if r[who][k] is not None] for who in ("ours","winner")]
        metrics[k]={"mean":list(map(mean,arms)),"median":list(map(median,arms))}
    pairs=[r for r in rows if r["ours"]["first_deposit"] is not None and r["winner"]["first_deposit"] is not None]
    pred={
      "gold_lead_early":sum(r["first_sustained_gold_lead"] is not None for r in rows),
      "gold_lead_without_early_deaths":sum(r["gold_gap_150"]>=100 and not r["ours"]["early_deaths"] and not r["winner"]["early_deaths"] for r in rows),
      "winner_first_bank_earlier":sum(r["winner"]["first_deposit"]<r["ours"]["first_deposit"] for r in pairs),
      "more_winner_enemy_clears_after300":sum(r["winner"]["enemy_clears_after300"]>r["ours"]["enemy_clears_after300"] for r in rows),
      "more_winner_wards":sum(r["winner"]["wards"]>r["ours"]["wards"] for r in rows),
    }
    v={"n":len(rows),"arms":["DOOMSDAY","winner"],"metrics":metrics,"event_counts":pred,
       "sustained_gold_lead_first_round":dict(Counter(r["first_sustained_gold_lead"] or "none" for r in rows)),
       "earned_gold_median":{str(t):[median(r["gold"][tag][str(t)] for r in rows) for tag in ("us","winner")] for t in ROUNDS}}
    (OUT/f"LOSS_{a.partition.upper()}.json").write_text(json.dumps({**v,"rows":rows},indent=2,ensure_ascii=False)+"\n",encoding="utf8",newline="\n")
    print(json.dumps(v,indent=2))

if __name__=="__main__":
    main()
