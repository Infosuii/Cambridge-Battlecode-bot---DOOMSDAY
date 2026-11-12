"""Summarize a CLFP fuel-profile batch (bots/claude-native-1104/src/clfp.h): engine fuel-outs, where turns ran out
(stage between two markers), and how much fuel non-overrun turns left unused.

usage (repo root): python tools/rl_env_1104/strategy/fuel_profile.py artifacts/tmp/rl_env_1104/fp1 [more dirs...]
(each dir holds <map>-<side>.repl26a + <map>-<side>.json from run-batch with logs on)
"""
import collections
import glob
import json
import os
import sys
import zipfile

import numpy as np

NAMES = {0: "turn start", 1: "pre nn_decide", 2: "post nn_decide", 3: "pre nn_lazy_score", 4: "post nn_lazy_score",
         5: "end play_turn", 6: "after nn_turn_end", 7: "turn end", 61: "turn_end: before warm-up",
         62: "turn_end: before rebuild", 63: "turn_end: before block refresh"}
BUCKETS = ["<2k", "2-5k", "5-10k", "10-20k", "20-40k", ">40k"]
MID = np.array([1000, 3500, 7500, 15000, 30000, 60000])  # rough bucket midpoints for a mean-unused estimate


def summarize(d: str) -> dict:
    seg, B, fo, games, wins, turns = collections.Counter(), np.zeros(6, int), 0, 0, 0, 0
    for rep in sorted(glob.glob(os.path.join(d, "*.repl26a"))):
        side = os.path.basename(rep)[:-8].split("-")[-1]
        raw = zipfile.ZipFile(rep).read(f"team-{side.lower()}.stdout").replace(bytes(1), b"\n").decode("utf-8", "replace")
        U = []
        for line in raw.splitlines():
            q = line.split(" ")
            if q[:2] == ["CLFP", "O"] and len(q) == 5:
                seg[(int(q[3]), int(q[4]))] += 1
            elif q[:2] == ["CLFP", "U"] and len(q) == 11:
                U.append([int(v) for v in q[2:]])
        U.sort(key=lambda u: (u[0], u[1]))
        for u in U[-3:]:  # each of the 3 bodies prints cumulative counters: its last report
            B += np.array(u[3:])
            turns += u[1]
        s = json.load(open(rep[:-8] + ".json"))
        our = "team" + side
        fo += sum(len(e["entries"]) for e in s["events"] if e["kind"] == "fuelExhausted" and e["owner"].get("team") == our)
        wins += s["match"]["outcome"] == our
        games += 1
    tot = sum(seg.values()) or 1
    return dict(games=games, wins=wins, fuel_outs=fo, fuel_outs_per_game=round(fo / max(1, games), 1),
                overruns_by_stage={f"{NAMES[a]} -> {NAMES[b]}": c for (a, b), c in seg.most_common()},
                unused_share={k: round(float(v / B.sum()), 3) for k, v in zip(BUCKETS, B)},
                unused_mean_estimate=int((B * MID).sum() / max(1, B.sum())), turns_reported=turns)


if __name__ == "__main__":
    for d in sys.argv[1:]:
        r = summarize(d)
        print(f"== {d}: {r['games']} games, {r['wins']} wins, fuel-outs {r['fuel_outs']} ({r['fuel_outs_per_game']}/game), "
              f"mean unused ~{r['unused_mean_estimate']}")
        print("   overruns by stage:", r["overruns_by_stage"])
        print("   unused fuel share:", r["unused_share"])
