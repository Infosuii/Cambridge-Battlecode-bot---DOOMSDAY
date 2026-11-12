"""Midgame target-command attribution on exact v109 (JOHNDOE #148/#149): CLTR CTR rows (bots' committed target and
mode changes) joined to the engine's official gem events.

A *segment* is a stretch in which one body keeps one committed target group in a farming mode. It ends when the target
or the mode changes; the end reason is what the next CTR row shows:
  mode   - another mode pre-empted farming (fight, flee, bank/tribute, teleport, ...)
  v92    - farm() re-scored and v92's own pick changed the target (source 0)
  actor  - the native actor's command overrode v92's pick (source 1)
  ally   - a poorer ally on the region took the reward (source 2)
  dead   - the body died (source 3)
Each segment is joined to camp gems collected from that group by the body itself (actor), by any own body (team)
and by the enemy, during the segment plus a short tail (gems land when the capture completes).

usage (repo root): python tools/rl_env_1104/strategy/target_trace.py artifacts/tmp/rl_env_1104/v109trace/games
       [--rounds 300 800] [--tail 10] [--out research/rl_env_1104/strategy/V109_TARGET_TRACE.json]
"""
import argparse
import collections
import glob
import json
import os
import zipfile

import numpy as np

FARM_MODES = None  # every mode that keeps a target counts; reasons distinguish pre-emption by mode change


def ctr_rows(rep: str, side: str) -> list:
    raw = zipfile.ZipFile(rep).read(f"team-{side.lower()}.stdout").replace(bytes(1), b"\n").decode("utf-8", "replace")
    out = []
    for line in raw.splitlines():
        q = line.split(" ")
        if q[0] == "CTR" and len(q) == 12:
            try:
                out.append(dict(round=int(q[1]), id=int(q[2]), slot=int(q[3]), mode=q[4], target=int(q[5]),
                                v92=int(q[6]), actor=int(q[7]), src=int(q[8]), gems=int(q[9]), hp=int(q[10])))
            except ValueError:
                pass
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("games")
    ap.add_argument("--rounds", nargs=2, type=int, default=[300, 800])
    ap.add_argument("--tail", type=int, default=10)
    ap.add_argument("--out", default="research/rl_env_1104/strategy/V109_TARGET_TRACE.json")
    a = ap.parse_args()
    lo, hi = a.rounds
    seg_all, per_game = [], []
    ident_hits = ident_total = 0
    for rep in sorted(glob.glob(os.path.join(a.games, "*.repl26a"))):
        tag = os.path.basename(rep)[:-8]
        opp, side = tag.split("-")[0], tag.split("-")[-1]
        stats = json.load(open(rep[:-8] + ".json", encoding="utf-8"))
        our = "team" + side
        theirs = "teamB" if our == "teamA" else "teamA"
        col = collections.defaultdict(list)  # group -> [(round, owner id, team, gems)]
        for e in stats["events"]:
            if e["kind"] != "gemCollection":
                continue
            for x in e["entries"]:
                if x["context"] == "campGroup":
                    col[x["target"]["id"]].append((x["timestamp"]["round"], e["owner"]["id"], e["owner"]["team"],
                                                   float(x["value"])))
        rows = ctr_rows(rep, side)
        by_body = collections.defaultdict(list)
        for r in rows:
            by_body[r["id"]].append(r)
        segs = []
        for bid, rs in by_body.items():
            rs.sort(key=lambda r: r["round"])
            # a commitment = consecutive rows with the same target (mode changes inside it do not end it)
            merged = []
            for r in rs:
                if merged and merged[-1]["target"] == r["target"]:
                    merged[-1]["modes"].add(r["mode"])
                    continue
                merged.append(dict(r, modes={r["mode"]}))
            rs = merged
            for i, r in enumerate(rs):
                if r["target"] < 0:
                    continue
                nxt = rs[i + 1] if i + 1 < len(rs) else None
                end = nxt["round"] if nxt else stats["match"]["roundsCompleted"]
                if end < lo or r["round"] > hi:
                    continue
                if nxt is None:
                    reason = "game_end"
                else:
                    reason = {0: "v92", 1: "actor", 2: "ally", 3: "dead"}.get(nxt["src"], "other")
                g = r["target"]
                ev = [x for x in col.get(g, []) if r["round"] <= x[0] <= end + a.tail]
                segs.append(dict(opp=opp, side=side, body=bid, group=g, start=r["round"], end=end, len=end - r["round"],
                                 mode=r["mode"], modes=sorted(r["modes"]), end_mode=nxt["mode"] if nxt else "-", set_by={0: "v92", 1: "actor", 2: "ally", 3: "dead"}.get(r["src"], "?"),
                                 reason=reason,
                                 own=sum(v for _, o, t, v in ev if t == our and o == bid),
                                 team=sum(v for _, o, t, v in ev if t == our),
                                 enemy=sum(v for _, o, t, v in ev if t == theirs)))
                # identity check of internal group index vs engine campGroup id: did this body collect from the
                # group it was committed to, versus from any group, during long segments?
                if end - r["round"] >= 10:
                    any_own = sum(1 for gg, lst in col.items() for x in lst
                                  if x[1] == bid and x[2] == our and r["round"] <= x[0] <= end + a.tail)
                    if any_own:
                        ident_total += 1
                        ident_hits += any(x[1] == bid and x[2] == our for x in ev)
        seg_all += segs
        sc = {t["team"]: int(t["submittedGems"]) for t in stats["teams"]}
        per_game.append(dict(game=tag, opp=opp, side=side, win=stats["match"]["outcome"] == our,
                             ours=sc.get(our), theirs=sc.get(theirs), segments=len(segs),
                             reasons=dict(collections.Counter(s["reason"] for s in segs)),
                             own_gems=sum(s["own"] for s in segs), enemy_gems_on_our_targets=sum(s["enemy"] for s in segs)))
    rep = dict(kind="v109 midgame target/execution attribution (diagnostic; engine 3.0.0)", rounds=[lo, hi],
               tail=a.tail, games=len(per_game),
               group_id_identity_check=dict(segments_with_own_collection=ident_total, collected_from_committed=ident_hits,
                                            rate=round(ident_hits / ident_total, 3) if ident_total else None))
    summ = {}
    for opp in sorted(set(s["opp"] for s in seg_all)) + ["ALL"]:
        ss = [s for s in seg_all if opp == "ALL" or s["opp"] == opp]
        out = {}
        for reason in sorted(set(s["reason"] for s in ss)):
            r = [s for s in ss if s["reason"] == reason]
            out[reason] = dict(n=len(r), mean_len=round(float(np.mean([s["len"] for s in r])), 1),
                               own_gems_per_seg=round(float(np.mean([s["own"] for s in r])), 2),
                               team_gems_per_seg=round(float(np.mean([s["team"] for s in r])), 2),
                               enemy_took_gems_per_seg=round(float(np.mean([s["enemy"] for s in r])), 2),
                               zero_own_collection=round(float(np.mean([s["own"] == 0 for s in r])), 3))
        g = [x for x in per_game if opp == "ALL" or x["opp"] == opp]
        summ[opp] = dict(games=len(g), wins=sum(x["win"] for x in g), by_end_reason=out,
                         set_by=dict(collections.Counter(s["set_by"] for s in ss)))
    rep["summary"] = summ
    rep["per_game"] = per_game
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps({k: rep[k] for k in ("games", "group_id_identity_check")}))
    for opp, s in summ.items():
        print(f"== {opp}: {s['wins']}/{s['games']} wins, targets set by {s['set_by']}")
        for reason, v in sorted(s["by_end_reason"].items(), key=lambda kv: -kv[1]["n"]):
            print(f"   {reason:9s} n={v['n']:5d} len {v['mean_len']:6.1f}  own gems/seg {v['own_gems_per_seg']:5.2f}  "
                  f"team {v['team_gems_per_seg']:5.2f}  enemy took {v['enemy_took_gems_per_seg']:5.2f}  "
                  f"zero-own {v['zero_own_collection']:.0%}")


if __name__ == "__main__":
    main()
