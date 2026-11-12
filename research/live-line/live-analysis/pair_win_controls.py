"""Matched ranked win controls for the frozen loss sample, using listing metadata only."""
from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
CACHE=ROOT/"artifacts/codex-p0/discovery48"
US="fcf5f666-ea55-4da0-b8d4-97c64bb37236"
def read(p): return json.loads(p.read_bytes())
def dt(s): return datetime.fromisoformat(s)

plan=read(OUT/"DISCOVERY_SAMPLE.json")
excluded={r["groupId"] or r["matchId"] for r in plan["matches"]}
by_opp=defaultdict(dict)
for f in (CACHE/"raw").glob("ranked-*.json"):
    for m in read(f)["matches"]:
        if m["status"]!="finished" or not dt(plan["start_utc"])<=dt(m["createdAt"])<dt(plan["end_utc"]):
            continue
        if not all(t.get("engineVersion")=="2.0.0" for t in m["teams"]):
            continue
        us,them=sorted(m["teams"],key=lambda t:t["teamId"]!=US)
        if us["teamId"]==US and us["result"]=="win":
            by_opp[them["teamId"]][m["matchId"]]={**m,"side":us["side"]}

rows=[]
for loss in plan["matches"]:
    opts=[m for m in by_opp[loss["opp_team_id"]].values() if (m["groupId"] or m["matchId"]) not in excluded]
    if not opts:
        continue
    win=min(opts,key=lambda m:(m["map"]!=loss["map"],m["side"]!=loss["side"],
                              abs(dt(m["createdAt"])-dt(loss["createdAt"])),m["matchId"]))
    excluded.add(win["groupId"] or win["matchId"])
    rows.append({"loss_id":loss["matchId"],"matchId":win["matchId"],"groupId":win["groupId"],
                 "createdAt":win["createdAt"],"opponent":loss["opponent"],"side":win["side"],"map":win["map"],
                 "same_map":win["map"]==loss["map"],"same_side":win["side"]==loss["side"]})
(OUT/"DISCOVERY_WIN_CONTROLS.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf8",newline="\n")
print(len(rows),"controls",sum(r["same_map"] for r in rows),"same map",sum(r["same_side"] for r in rows),"same side")
