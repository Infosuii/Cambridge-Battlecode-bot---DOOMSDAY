"""Classify idle time in decoded ladder replays (review-*.json from tools/replay3/review.mjs), ours vs theirs.

A body is idle in a round when it is alive, at the same tile as the previous sample, and took no attack/cast/
channel/bank action in between (the reviewer's stationary definition), counted for every idle round (not only
runs >= 8). Each idle round is classed as:
  spawn_heal   on/near its own spawn (within 2 of its round-1 tile) with HP below max and rising
  spawn_full   on/near spawn at >= 98% HP
  field_full   elsewhere at >= 98% HP, no enemy within 4
  field_hurt   elsewhere below 98% HP, no enemy within 4
  contact      an enemy within 4
and by whether the body carried gems. Reports idle rounds per game by class, us vs them, by our result.

usage: python -I tools/rl_env_1104/strategy/ladder_idle.py artifacts/tmp/ladder_review data/ladder/live_v112_20261108/match_index.json
"""
import collections
import glob
import json
import os
import sys

ME = "fcf5f666-ea55-4da0-b8d4-97c64bb37236"


def main() -> None:
    rdir, idx_path = sys.argv[1], sys.argv[2]
    idx = {m["matchId"]: m for m in json.load(open(idx_path, encoding="utf-8"))}
    agg = collections.defaultdict(collections.Counter)
    games = collections.Counter()
    runs_example = collections.defaultdict(list)
    for f in glob.glob(os.path.join(rdir, "review-*.json")):
        r = json.load(open(f, encoding="utf-8"))
        m = idx.get(r["match"])
        if not m:
            continue
        me = [t for t in m["teams"] if t["teamId"] == ME][0]
        our = "teamA" if me["side"] == "a" else "teamB"
        res = "win" if me["result"] == "win" else "loss"
        games[res] += 1
        for b in r["bodies"]:
            who = "us" if b["team"] == our else "them"
            h = b["history"]
            if not h:
                continue
            spawn = next((x["p"] for x in h if x.get("p")), None)
            acts = collections.defaultdict(set)
            for k, v in b.get("actions", {}).items():
                pass
            for i in range(1, len(h)):
                a, c = h[i - 1], h[i]
                if not (a.get("alive") and c.get("alive") and a.get("p") and c.get("p")):
                    continue
                if (a["p"]["x"], a["p"]["y"]) != (c["p"]["x"], c["p"]["y"]):
                    agg[(res, who)]["moving"] += 1
                    continue
                # attack/cast/channel are not visible per round here; the hp/enemies context is the proxy
                mx = max(1.0, float(c.get("maxhp") or 1))
                at_spawn = spawn is not None and max(abs(c["p"]["x"] - spawn["x"]), abs(c["p"]["y"] - spawn["y"])) <= 2
                full = c["hp"] >= 0.98 * mx
                e4 = c.get("enemies4") or 0
                cls = ("contact" if e4 else "spawn_heal" if at_spawn and not full else "spawn_full" if at_spawn
                       else "field_full" if full else "field_hurt")
                agg[(res, who)]["still_" + cls] += 1
                if c.get("gems"):
                    agg[(res, who)]["still_with_gems"] += 1
                agg[(res, who)]["still"] += 1
    for key in sorted(agg):
        n = games[key[0]]
        print(key, f"games={n}", {k: round(v / n, 1) for k, v in sorted(agg[key].items())})


if __name__ == "__main__":
    main()
