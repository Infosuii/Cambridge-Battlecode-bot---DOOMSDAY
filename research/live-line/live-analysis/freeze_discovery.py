"""Freeze independent discovery/confirmation match groups from a 48-hour CLI census."""
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/"artifacts/codex-p0/discovery48"
OUT=Path(__file__).resolve().parent
OURS="fcf5f666-ea55-4da0-b8d4-97c64bb37236"
AS_OF=datetime.fromisoformat("2026-11-04T13:42:00+00:00")
BEGIN=AS_OF-timedelta(hours=48)

def stable(s):
    return sha256(("codex-discovery-20261104:" + s).encode()).hexdigest()

def read(path):
    return json.loads(path.read_bytes())

def main():
    ladder=read(ROOT/"docs/codex/LADDER.json")
    above={x["teamId"]:x for x in ladder["above"]}
    seen=set()
    losses=[]
    # Use ranked games to avoid known mixed or repeated unranked duel arms.
    for page in (CACHE/"raw").glob("ranked-*.json"):
        for m in read(page)["matches"]:
            mid=m["matchId"]
            if mid in seen or not (BEGIN<=datetime.fromisoformat(m["createdAt"])<AS_OF):
                continue
            seen.add(mid)
            if m["status"]!="finished" or not all(t.get("engineVersion")=="2.0.0" for t in m["teams"]):
                continue
            us,them=sorted(m["teams"],key=lambda t:t["teamId"]!=OURS)
            if us["teamId"]!=OURS or us["result"]!="loss" or them["teamId"] not in above:
                continue
            opp=above[them["teamId"]]
            tier=0 if opp["rank"]<=10 else 1 if opp["rank"]<=35 else 2
            losses.append({"matchId":mid,"groupId":m["groupId"],"createdAt":m["createdAt"],
                           "map":m["map"],"side":us["side"],"opponent":them["name"],
                           "opp_team_id":them["teamId"],"opp_rank":opp["rank"],"opp_rating":opp["rating"],
                           "tier":tier,"our_draft":us.get("draftPicks"),"their_draft":them.get("draftPicks")})
    strata=defaultdict(list)
    groups=set()
    # One replay per group and a cap per opponent; spread exposure across rating tiers.
    for row in sorted(losses,key=lambda r:stable(r["matchId"])):
        group=row["groupId"] or row["matchId"]
        if group in groups:
            continue
        groups.add(group)
        strata[row["tier"]].append(row)
    pick=[]
    for _,rows in sorted(strata.items()):
        per_opp=Counter()
        chosen=[]
        for row in rows:
            if per_opp[row["opp_team_id"]]>=4:
                continue
            chosen.append(row)
            per_opp[row["opp_team_id"]]+=1
            if len(chosen)==24:
                break
        for i,row in enumerate(chosen):
            pick.append({**row,"partition":"confirm" if i%3==2 else "discovery"})
    assert len({r["groupId"] or r["matchId"] for r in pick})==len(pick)
    out={"start_utc":BEGIN.isoformat(),"end_utc":AS_OF.isoformat(),"engine":"2.0.0","census_matches":len(seen),
         "eligible_ranked_losses":len(losses),"eligible_groups":len(groups),
         "sample_counts":dict(Counter(r["partition"] for r in pick)),
         "tier_counts":dict(Counter(r["tier"] for r in pick)),
         "method":"Ranked 2.0.0 losses to teams above DOOMSDAY in the captured ladder. One replay per group, fixed SHA-256 order, up to four per opponent and 24 per rank tier. Every third selected group within each tier is held back. No assignment to a live submission is inferred.",
         "matches":pick}
    output=OUT/"DISCOVERY_SAMPLE.json"
    if output.exists():
        raise SystemExit("Sample already frozen")
    output.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf8",newline="\n")
    print({k:v for k,v in out.items() if k!="matches"})

if __name__=="__main__":
    main()
