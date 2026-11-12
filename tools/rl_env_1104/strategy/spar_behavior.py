"""Behavior check for sparring styles vs their unchanged parent (JOHNDOE #151 calibration).

Reads a run_eval output dir (work/batch.txt + work/g<i>.json + replays) and, per candidate x opponent, reports what each
style is meant to change, measured from official engine events (geometry-free):
  contested camp gems - our camp gems from groups the enemy also collected from in that game (camp invasion)
  enemy camp gems     - the opponent's total camp-group gems (invasion should cut them)
  enemy gems lost     - gems the opponent's champions lost on death (gemLoss; carrier pressure should raise it)
  enemy deaths        - opponent champion deaths
  enemy banked        - opponent submittedGems
  ours banked         - our submittedGems
plus trigger counts from our stdout (SPR = raid target changes, SPC = carrier chases started).

usage: python -I tools/rl_env_1104/strategy/spar_behavior.py runs/rl_env_1104/eval/e3-spar-calib-01 [--out file.json]
"""
import argparse
import collections
import json
import os
import zipfile


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--out")
    a = ap.parse_args()
    rep = json.load(open(os.path.join(a.run, "report.json"), encoding="utf-8"))
    cands = {os.path.abspath(v).replace("\\", "/").lower(): k for k, v in rep["candidates"].items()}
    opps = {os.path.abspath(v).replace("\\", "/").lower(): k for k, v in rep["opponents"].items()}
    work = os.path.join(a.run, "work")
    agg = collections.defaultdict(lambda: collections.defaultdict(float))
    for i, line in enumerate(open(os.path.join(work, "batch.txt"), encoding="utf-8")):
        q = line.split()
        pa, pb = q[0].lower(), q[1].lower()
        if pa in cands and pb in opps:
            cand, opp, our, side = cands[pa], opps[pb], "teamA", "a"
        elif pb in cands and pa in opps:
            cand, opp, our, side = cands[pb], opps[pa], "teamB", "b"
        else:
            continue
        sj = os.path.join(work, f"g{i}.json")
        if not os.path.exists(sj):
            continue
        s = json.load(open(sj, encoding="utf-8"))
        theirs = "teamB" if our == "teamA" else "teamA"
        by_team_group = collections.defaultdict(lambda: collections.defaultdict(float))
        lost = deaths = 0.0
        for e in s["events"]:
            t = e["owner"].get("team")
            if e["kind"] == "gemCollection":
                for x in e["entries"]:
                    if x["context"] == "campGroup":
                        by_team_group[t][x["target"]["id"]] += float(x["value"])
            elif e["kind"] == "gemLoss" and t == theirs:
                lost += sum(float(x["value"]) for x in e["entries"])
            elif e["kind"] == "death" and t == theirs:
                deaths += len(e["entries"])
        ours_g, their_g = by_team_group[our], by_team_group[theirs]
        sc = {t["team"]: float(t["submittedGems"]) for t in s["teams"]}
        k = agg[(cand, opp)]
        k["games"] += 1
        k["wins"] += s["match"]["outcome"] == our
        k["contested_camp_gems"] += sum(v for g, v in ours_g.items() if g in their_g)
        k["our_camp_gems"] += sum(ours_g.values())
        k["enemy_camp_gems"] += sum(their_g.values())
        k["enemy_gems_lost"] += lost
        k["enemy_deaths"] += deaths
        k["enemy_banked"] += sc.get(theirs, 0)
        k["ours_banked"] += sc.get(our, 0)
        rp = [f for f in os.listdir(work) if f.startswith(f"g{i}.") and f.endswith(".repl26a")] or \
             ([f"g{i}.repl26a"] if os.path.exists(os.path.join(work, f"g{i}.repl26a")) else [])
        if rp:
            try:
                out = zipfile.ZipFile(os.path.join(work, rp[0])).read(f"team-{side}.stdout")
                txt = out.replace(bytes(1), b"\n").decode("utf-8", "replace").splitlines()
                k["SPR"] += sum(l.startswith("SPR ") for l in txt)
                k["SPC"] += sum(l.startswith("SPC ") for l in txt)
            except (KeyError, zipfile.BadZipFile):
                pass
    rows = {}
    for (cand, opp), k in sorted(agg.items()):
        n = k["games"]
        rows[f"{cand} vs {opp}"] = {m: round(v / n, 2) if m not in ("games", "wins") else int(v) for m, v in k.items()}
    hdr = ["games", "wins", "contested_camp_gems", "our_camp_gems", "enemy_camp_gems", "enemy_gems_lost", "enemy_deaths",
           "enemy_banked", "ours_banked", "SPR", "SPC"]
    print("cell".ljust(22) + " ".join(h[:14].rjust(14) for h in hdr))
    for name, r in rows.items():
        print(name.ljust(22) + " ".join(str(r.get(h, 0)).rjust(14) for h in hdr))
    if a.out:
        json.dump(dict(run=a.run, per_game_means=rows), open(a.out, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
