"""Aggregate decoded ladder replays (tools/replay3/review.mjs output) into death and idle diagnostics, ours vs theirs.

For every champion death: HP fraction 3 and 1 rounds before death, enemies/allies within 4 in the 3 rounds before,
gems carried, and whether it was a burst (>= 50% HP lost in the last 3 rounds) and whether the killer(s) were out of
4-tile range the round before (long-range burst). Idle: per-body stationary runs (>= 8 rounds, no attack/cast/channel),
split into team-idle rounds where >= 3 bodies of a team idle together at full health with no enemy within 4.
Results split by our result (win/loss) and team (us/them).

usage: python -I tools/rl_env_1104/strategy/ladder_deaths.py <review json glob dir> <match_index.json>
"""
import collections
import glob
import json
import os
import statistics
import sys

ME = "fcf5f666-ea55-4da0-b8d4-97c64bb37236"


def main() -> None:
    rdir, idx_path = sys.argv[1], sys.argv[2]
    idx = {m["matchId"]: m for m in json.load(open(idx_path, encoding="utf-8"))}
    agg = collections.defaultdict(collections.Counter)
    lists = collections.defaultdict(list)
    games = collections.Counter()
    for f in glob.glob(os.path.join(rdir, "review-*.json")):
        r = json.load(open(f, encoding="utf-8"))
        m = idx.get(r["match"])
        if not m:
            continue
        me = [t for t in m["teams"] if t["teamId"] == ME][0]
        our = "teamA" if me["side"] == "a" else "teamB"
        res = "win" if me["result"] == "win" else "loss"
        games[res] += 1
        idle_by_team_round = collections.defaultdict(lambda: collections.Counter())
        for b in r["bodies"]:
            who = "us" if b["team"] == our else "them"
            key = (res, who)
            for d in b["deaths"]:
                bf = [x for x in d["before"] if x.get("hp") is not None]
                if not bf:
                    continue
                last = bf[-1]
                mx = max(1.0, float(last.get("maxhp") or 1))
                t3 = [x for x in bf if x["round"] >= d["round"] - 3]
                hp3 = (t3[0]["hp"] / mx) if t3 else last["hp"] / mx
                e_max = max((x["enemies4"] or 0) for x in t3) if t3 else 0
                a_max = max((x["allies4"] or 0) for x in t3) if t3 else 0
                burst = hp3 >= 0.5
                agg[key]["deaths"] += 1
                agg[key]["deaths_" + d["context"]] += 1
                if d["context"] == "champion":
                    agg[key]["burst"] += burst
                    agg[key]["no_enemy_within4_prev"] += (last["enemies4"] or 0) == 0
                    agg[key]["outnumbered"] += e_max > a_max + 1
                    agg[key]["even_or_better"] += e_max <= a_max + 1
                    lists[key + ("hp3",)].append(hp3)
                    lists[key + ("e4",)].append(e_max); lists[key + ("a4",)].append(a_max)
                    lists[key + ("gems",)].append(last.get("gems") or 0)
                    ph = "early" if d["round"] <= 300 else "mid" if d["round"] <= 800 else "late"
                    agg[key]["champ_death_" + ph] += 1
            for s in b["stationary_runs"]:
                agg[key]["idle_runs"] += 1
                agg[key]["idle_rounds"] += s["end"] - s["start"]
            # per-round stationary flags for team idle (approximate from runs)
            for s in b["stationary_runs"]:
                if (s.get("enemies4") or 0) == 0:
                    for rr in range(s["start"], s["end"]):
                        idle_by_team_round[b["team"]][rr] += 1
        for team, rc in idle_by_team_round.items():
            who = "us" if team == our else "them"
            agg[(res, who)]["team_idle_rounds_3plus"] += sum(1 for v in rc.values() if v >= 3)
    for key in sorted(agg):
        n = games[key[0]]
        c = agg[key]
        cd = max(1, c["deaths_champion"])
        out = {k: round(v / n, 2) for k, v in sorted(c.items()) if k in ("deaths", "deaths_champion", "deaths_camp", "idle_runs", "idle_rounds", "team_idle_rounds_3plus", "champ_death_early", "champ_death_mid", "champ_death_late")}
        out.update({"burst_share": round(c["burst"] / cd, 2), "no_enemy_prev_share": round(c["no_enemy_within4_prev"] / cd, 2),
                    "outnumbered_share": round(c["outnumbered"] / cd, 2),
                    "mean_hp3": round(statistics.mean(lists[key + ("hp3",)] or [0]), 2),
                    "mean_e4": round(statistics.mean(lists[key + ("e4",)] or [0]), 2), "mean_a4": round(statistics.mean(lists[key + ("a4",)] or [0]), 2)})
        print(key, f"games={n}", out)


if __name__ == "__main__":
    main()
