"""Recount archived duel groups by ID. Read-only, no submission or quota mutation."""
import argparse
from collections import defaultdict
import json
from math import sqrt
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "tools/vendor/cambc.exe"
CACHE = ROOT / "artifacts/codex-p0/duel-group-cache"
TEAM_ID = "fcf5f666-ea55-4da0-b8d4-97c64bb37236"
ENGINE = "2.0.0"

def show(gid):
    dest=CACHE/f"{gid}.json"
    if dest.exists():
        return json.loads(dest.read_bytes())
    for attempt in range(4):
        proc=subprocess.run([CLI,"match-groups","show",gid,"--json"],capture_output=True,timeout=25)
        try:
            data=json.loads(proc.stdout)
            if proc.returncode==0 and data.get("groupId")==gid and not data.get("nextCursor"):
                dest.write_bytes(proc.stdout)
                return data
        except (ValueError, AttributeError):
            pass
        error=proc.stderr.decode(errors="replace")
        retry=re.search(r"retry after (\d+) seconds",error,re.I)
        if retry:
            time.sleep(int(retry.group(1))+1)
        elif attempt<3:
            time.sleep(2+attempt)
    raise ValueError(f"Unable to read group {gid}")

def arm_cells(plan, arm):
    groups=plan["arms"][arm]["groups"]
    assert len(groups)==len(plan["groups"])
    cells={}
    for idx,(gid,g) in enumerate(zip(groups,plan["groups"],strict=True)):
        if gid is None:
            continue
        data=show(gid)
        for m in data["matches"]:
            if m["status"]!="finished":
                continue
            pos=m["position"]-1
            assert 0<=pos<5 and (idx,pos) not in cells
            ours,opp=sorted(m["teams"],key=lambda t:t["teamId"]!=TEAM_ID)
            assert ours["teamId"]==TEAM_ID and opp["teamId"]==g["opponentId"]
            assert ours["side"]==g["sides"][pos] and m["map"]==g["maps"][pos], (gid,pos,m["map"],g["maps"][pos])
            assert all(t["engineVersion"]==ENGINE for t in m["teams"])
            cells[(idx,pos)]=(ours["result"]=="win",m["matchId"])
    return cells

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("plan",type=Path)
    p.add_argument("base")
    p.add_argument("candidate")
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    plan=json.loads(a.plan.read_bytes())
    CACHE.mkdir(parents=True,exist_ok=True)
    x,y=(arm_cells(plan,arm) for arm in (a.base,a.candidate))
    keys=sorted(x.keys() & y.keys())
    b=sum(y[k][0] and not x[k][0] for k in keys)
    c=sum(x[k][0] and not y[k][0] for k in keys)
    d={"base":a.base,"candidate":a.candidate,"base_games":len(x),"candidate_games":len(y),
       "base_wins":sum(x[k][0] for k in keys),"candidate_wins":sum(y[k][0] for k in keys),
       "paired":len(keys),"b":b,"c":c,"z":(b-c)/sqrt(b+c) if b+c else 0,
       "pin_note":"Ordered opponent/map/side and group IDs verified; platform read output does not expose opponent submission ID or pin source."}
    a.out.write_text(json.dumps({**d,"pairs":[[i,j,x[i,j],y[i,j]] for i,j in keys]},indent=2)+"\n",encoding="utf8",newline="\n")
    print(json.dumps(d,indent=2),flush=True)

if __name__=="__main__":
    main()
