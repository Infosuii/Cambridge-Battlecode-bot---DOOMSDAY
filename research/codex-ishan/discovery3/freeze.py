"""Freeze a fresh 16/8 sample from the current ranked census and prior coverage."""
from collections import Counter
from datetime import datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CACHE = ROOT / "artifacts/codex-p0"
RAW = CACHE / "discovery3"
TEAM = "fcf5f666-ea55-4da0-b8d4-97c64bb37236"
AS_OF = datetime.fromisoformat("2026-11-04T15:31:00+00:00")

def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))

def main():
    teams = read(RAW / "ladder.json")["teams"]
    ours = next(t for t in teams if t["teamId"] == TEAM)
    above = {t["teamId"]: t for t in teams if t["rank"] < ours["rank"]}
    assert len(above) == ours["rank"] - 1
    prev = [OUT.parent / "DISCOVERY_SAMPLE.json", OUT.parent / "discovery2/DISCOVERY_SAMPLE.json"]
    excluded = {m["groupId"] or m["matchId"] for f in prev for m in read(f)["matches"]}
    history = [*sorted((CACHE/"discovery48/raw").glob("ranked-*.json")), CACHE/"ranked-resume-1.json"]
    census = {m["matchId"]:m for f in history for m in read(f)["matches"]}
    current = read(RAW / "matches.json")["matches"]
    assert {m["matchId"] for m in current} & census.keys(), "Ranked capture needs another page"
    census.update((m["matchId"], m) for m in current)
    losses = []
    for m in census.values():
        if m["status"] != "finished" or not AS_OF-timedelta(hours=48) <= datetime.fromisoformat(m["createdAt"]) < AS_OF:
            continue
        if not all(t.get("engineVersion") == "2.0.0" for t in m["teams"]):
            continue
        us, opp = sorted(m["teams"], key=lambda t:t["teamId"] != TEAM)
        group = m["groupId"] or m["matchId"]
        if us["teamId"] != TEAM or us["result"] != "loss" or opp["teamId"] not in above or group in excluded:
            continue
        rank = above[opp["teamId"]]
        losses.append(dict(matchId=m["matchId"], groupId=m["groupId"], createdAt=m["createdAt"],
                           map=m["map"], side=us["side"], opponent=opp["name"], opp_team_id=opp["teamId"],
                           opp_rank=rank["rank"], opp_rating=rank["rating"],
                           our_draft=us.get("draftPicks"), their_draft=opp.get("draftPicks")))
    chosen = []
    used = set(excluded)
    counts = Counter()
    for m in sorted(losses, key=lambda m: sha256(("codex-discovery3-1104:"+m["matchId"]).encode()).hexdigest()):
        group = m["groupId"] or m["matchId"]
        if group in used or counts[m["opp_team_id"]] >= 4:
            continue
        used.add(group)
        counts[m["opp_team_id"]] += 1
        chosen.append({**m, "partition":"confirm" if len(chosen)%3==2 else "discovery"})
        if len(chosen) == 24:
            break
    assert len(chosen) == 24
    result = dict(as_of=AS_OF.isoformat(), our_rank=ours["rank"], our_rating=ours["rating"],
                  prior_groups_excluded=len(excluded), eligible_loss_rows=len(losses),
                  source_sha256={f.name:sha256(f.read_bytes()).hexdigest() for f in (RAW/"matches.json", RAW/"ladder.json")},
                  method="Engine 2 ranked losses to teams now above DOOMSDAY. Overlapping 48-hour census, exclude earlier groups, fixed SHA order, max four per opponent. Every third selected group reserved.",
                  matches=chosen)
    with (OUT/"DISCOVERY_SAMPLE.json").open("x",encoding="utf8",newline="\n") as f:
        json.dump(result,f,indent=2,ensure_ascii=False)
        f.write("\n")
    print({k:v for k,v in result.items() if k!="matches"})

if __name__ == "__main__":
    main()
