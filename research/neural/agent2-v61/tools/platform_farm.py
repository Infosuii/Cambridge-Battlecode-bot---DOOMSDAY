"""How the platform opponents farm twice as fast (E75): rounds 0-UNTIL of the decoded platform games, per team.

Per champion-round: dead, at spawn (within 2 of where it started), at a camp (within 2 of a camp tile), elsewhere.
Captures: a gem gain of 3+ while alive within 2 of a camp tile; shared when a teammate within 3 gained gems the same
round. Banks: the bag drops to 0 while alive (bag size recorded). Health lost with no enemy within 6 (camp damage) and
trips home. Also the first capture round and the gems of the groups captured.

usage: python -I tools/platform_farm.py platform_matches/dec [UNTIL=300]
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def main():
    d = Path(sys.argv[1])
    until = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    seen = set()
    S = {t: defaultdict(float) for t in (0, 1)}
    bags = {t: [] for t in (0, 1)}
    capsz = {t: [] for t in (0, 1)}
    firstcap = {t: [] for t in (0, 1)}
    grp_gems = {t: Counter() for t in (0, 1)}
    n = 0
    for f in sorted(d.glob("*.json")):
        g = json.loads(f.read_text())
        rs = [r for r in g["rounds"] if r["champs"]]
        key = (len(g["rounds"]), tuple(g["rounds"][-1]["banked"]))
        if key in seen:
            continue
        seen.add(key)
        n += 1
        tiles = []
        for gi, gr in enumerate(g["groups"]):
            for t in gr["tiles"]:
                tiles.append((t[0], t[1], gi))
        start = {c["h"]: (c["x"], c["y"]) for c in rs[0]["champs"]}
        prev = None
        fc = {}
        for r in rs:
            if r["round"] > until:
                break
            cur = {c["h"]: c for c in r["champs"]}
            gained = {h for h, c in cur.items() if prev and prev.get(h) and c["gems"] > prev[h]["gems"]}
            for h, c in cur.items():
                t = c["team"]
                S[t]["champ_rounds"] += 1
                if not c["alive"]:
                    S[t]["dead"] += 1
                    continue
                p = (c["x"], c["y"])
                near_camp = [gi for x, y, gi in tiles if cheb(p, (x, y)) <= 2]
                if cheb(p, start[h]) <= 2:
                    S[t]["at_spawn"] += 1
                elif near_camp:
                    S[t]["at_camp"] += 1
                else:
                    S[t]["elsewhere"] += 1
                if not prev or h not in prev:
                    continue
                q = prev[h]
                if not q["alive"]:
                    continue
                dg = c["gems"] - q["gems"]
                if dg >= 3 and near_camp:
                    S[t]["captures"] += 1
                    capsz[t].append(dg)
                    grp_gems[t][g["groups"][near_camp[0]]["gems"]] += 1
                    mates = [o for o in gained if o != h and cur[o]["team"] == t and cheb(p, (cur[o]["x"], cur[o]["y"])) <= 3]
                    S[t]["shared"] += 1 if mates else 0
                    if (t, h) not in fc:
                        fc[(t, h)] = r["round"]
                if q["gems"] > 0 and c["gems"] == 0:
                    S[t]["banks"] += 1
                    bags[t].append(q["gems"])
                enemies6 = [o for o in cur.values() if o["team"] != t and o["alive"] and cheb(p, (o["x"], o["y"])) <= 6]
                if c["hp"] < q["hp"] and not enemies6:
                    S[t]["camp_dmg"] += q["hp"] - c["hp"]
                if cheb(p, start[h]) <= 2 and cheb((q["x"], q["y"]), start[h]) > 2:
                    S[t]["trips_home"] += 1
            prev = cur
        for (t, h), rr in fc.items():
            firstcap[t].append(rr)
    print(f"{n} games, rounds 0-{until}")
    for t in (0, 1):
        s = S[t]
        cr = s["champ_rounds"]
        name = "us  " if t == 0 else "them"
        print(f"{name}: dead {100 * s['dead'] / cr:.0f}%  at spawn {100 * s['at_spawn'] / cr:.0f}%  at a camp {100 * s['at_camp'] / cr:.0f}%  elsewhere "
              f"{100 * s['elsewhere'] / cr:.0f}% of champion-rounds")
        print(f"      captures/game {s['captures'] / n:.1f} (shared with a teammate {100 * s['shared'] / max(1, s['captures']):.0f}%), gems per capture "
              f"{sum(capsz[t]) / max(1, len(capsz[t])):.1f}, banks/game {s['banks'] / n:.1f}, bag at bank {sum(bags[t]) / max(1, len(bags[t])):.0f}, "
              f"trips home/game {s['trips_home'] / n:.1f}, camp damage taken/game {s['camp_dmg'] / n:.0f}")
        fcs = sorted(firstcap[t])
        print(f"      first capture round: median {fcs[len(fcs) // 2] if fcs else '-'}; group sizes captured {sorted(grp_gems[t].items())[:12]}")


if __name__ == "__main__":
    main()
