"""How the platform opponents beat us (E75): rounds 0-300 of the decoded platform games (agent2/lab/platform_decode.js).

Per team (0 = us): deaths, kills, gold income split into kill gold (a jump of 100+ in the round an enemy died within
5) and other gold, gems gained, banked, stats, gold spent and the item families bought, spacing (distance to the
nearest living teammate), share of time with a teammate within 3, map side, and the context of every kill (attackers
and defenders within 4 and 8, whether the victim stood at a camp, carried gems).

usage: python -I tools/platform_study.py platform_matches/dec [UNTIL=300]
"""
import json
import site
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.append(site.getusersitepackages())

NAMES = ["Ryth", "Vesper", "Vendetta", "Cassi", "Issac", "Stellar", "Prism", "Marcella", "Willow", "Ren", "Varg", "Tavi", "Heart"]
FAM = ["monster", "power", "durability", "treasure", "jungle", "home", "bruiser", "tribute", "capture", "prospector", "hunter", "skirmish", "greed", "collectors"]


def cheb(a, b):
    return max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"]))


def main():
    d = Path(sys.argv[1])
    until = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    seen = set()
    games = []
    for f in sorted(d.glob("*.json")):
        g = json.loads(f.read_text())
        rs = g["rounds"]
        key = (len(rs), tuple(rs[-1]["banked"]))
        if key in seen:
            continue
        seen.add(key)
        games.append((f.stem, g))
    T = {t: defaultdict(float) for t in (0, 1)}
    kills_ctx = {t: [] for t in (0, 1)}
    items_by = {t: {r: Counter() for r in (100, 200, 300)} for t in (0, 1)}
    picks = {t: Counter() for t in (0, 1)}
    per_game = []
    for name, g in games:
        rs = [r for r in g["rounds"] if r["champs"]]
        groups = g["groups"]
        camp_tiles = [(t[0], t[1]) for gr in groups for t in gr["tiles"]]
        first = rs[0]
        for c in first["champs"]:
            picks[c["team"]][NAMES[c["type"]] if 0 <= c["type"] < len(NAMES) else c["type"]] += 1
        # spawn centres: mean position of each team's living champions at the first round
        sc = {}
        for t in (0, 1):
            ps = [c for c in first["champs"] if c["team"] == t and c["x"] >= 0]
            sc[t] = (sum(c["x"] for c in ps) / max(1, len(ps)), sum(c["y"] for c in ps) / max(1, len(ps)))
        prev = None
        gstat = {t: defaultdict(float) for t in (0, 1)}
        for r in rs:
            rn = r["round"]
            if rn > until:
                break
            cur = {c["h"]: c for c in r["champs"]}
            if prev:
                died = [h for h, c in cur.items() if prev.get(h) and prev[h]["alive"] and not c["alive"]]
                for h, c in cur.items():
                    p = prev.get(h)
                    if not p:
                        continue
                    t = c["team"]
                    dg = c["gold"] - p["gold"]
                    if dg > 0:
                        killgold = dg >= 100 and any(cur[v]["team"] != t and cheb(prev[v], p) <= 5 for v in died)
                        gstat[t]["gold_kill" if killgold else "gold_other"] += dg
                    elif dg < 0 and c["alive"]:
                        gstat[t]["gold_spent"] += -dg
                    if c["alive"] and p["alive"] and c["gems"] > p["gems"]:
                        gstat[t]["gems_gained"] += c["gems"] - p["gems"]
                for v in died:
                    pv = prev[v]
                    t = pv["team"]
                    gstat[t]["deaths"] += 1
                    gstat[1 - t]["kills"] += 1
                    att4 = sum(1 for q in prev.values() if q["team"] != t and q["alive"] and cheb(q, pv) <= 4)
                    att8 = sum(1 for q in prev.values() if q["team"] != t and q["alive"] and cheb(q, pv) <= 8)
                    def4 = sum(1 for q in prev.values() if q["team"] == t and q["h"] != v and q["alive"] and cheb(q, pv) <= 4)
                    at_camp = any(max(abs(pv["x"] - x), abs(pv["y"] - y)) <= 2 for x, y in camp_tiles)
                    da = ((pv["x"] - sc[t][0]) ** 2 + (pv["y"] - sc[t][1]) ** 2) ** 0.5
                    de = ((pv["x"] - sc[1 - t][0]) ** 2 + (pv["y"] - sc[1 - t][1]) ** 2) ** 0.5
                    side = "own" if da < 0.8 * de else "theirs" if de < 0.8 * da else "mid"
                    kills_ctx[1 - t].append({"game": name, "r": rn, "victim": NAMES[pv["type"]], "att4": att4, "att8": att8, "def4": def4,
                                             "at_camp": at_camp, "side_of_victim": side, "bag": pv["gems"], "hp_frac": round(pv["hp"] / max(1, pv["mhp"]), 2)})
            # spacing and side, every 5 rounds
            if rn % 5 == 0:
                for t in (0, 1):
                    alive = [c for c in r["champs"] if c["team"] == t and c["alive"] and c["x"] >= 0]
                    for c in alive:
                        others = [cheb(c, o) for o in alive if o["h"] != c["h"]]
                        if others:
                            gstat[t]["near_sum"] += min(others)
                            gstat[t]["near_n"] += 1
                            gstat[t]["with3"] += 1 if min(others) <= 3 else 0
                        da = ((c["x"] - sc[t][0]) ** 2 + (c["y"] - sc[t][1]) ** 2) ** 0.5
                        de = ((c["x"] - sc[1 - t][0]) ** 2 + (c["y"] - sc[1 - t][1]) ** 2) ** 0.5
                        gstat[t]["on_their_half"] += 1 if de < da else 0
                        gstat[t]["pos_n"] += 1
            if rn in (100, 200, 300):
                for t in (0, 1):
                    cs = [c for c in r["champs"] if c["team"] == t]
                    gstat[t][f"banked{rn}"] = r["banked"][t]
                    gstat[t][f"str{rn}"] = sum(c["str"] for c in cs)
                    gstat[t][f"mhp{rn}"] = sum(c["mhp"] for c in cs)
                    gstat[t][f"carried{rn}"] = sum(c["gems"] for c in cs if c["alive"])
            prev = cur
        for rr in (100, 200, 300):
            for s in g["items"].get(str(rr), []):
                if s["items"]:
                    for i, n in enumerate(s["items"]):
                        if n:
                            items_by[s["team"]][rr][FAM[i // 6] + ("-shard" if i % 2 == 0 else "-EMBLEM")] += n
        for t in (0, 1):
            for k, v in gstat[t].items():
                T[t][k] += v
        per_game.append((name, {t: dict(gstat[t]) for t in (0, 1)}))
    n = len(games)
    print(f"{n} distinct games, rounds 0-{until}")
    keys = ["deaths", "kills", "gold_kill", "gold_other", "gold_spent", "gems_gained", "banked100", "banked200", "banked300", "carried300",
            "str100", "str200", "str300", "mhp100", "mhp300"]
    for k in keys:
        print(f"  {k:12s} us {T[0][k] / n:8.1f}   them {T[1][k] / n:8.1f}")
    for t in (0, 1):
        print(f"  {'us' if t == 0 else 'them'}: nearest teammate {T[t]['near_sum'] / max(1, T[t]['near_n']):.1f} tiles, teammate within 3 "
              f"{100 * T[t]['with3'] / max(1, T[t]['near_n']):.0f}% of the time, on the enemy half {100 * T[t]['on_their_half'] / max(1, T[t]['pos_n']):.0f}%")
    for t in (0, 1):
        ks = kills_ctx[t]
        if not ks:
            continue
        print(f"\n  kills by {'us' if t == 0 else 'them'} ({len(ks)}): attackers within 4 mean {sum(k['att4'] for k in ks) / len(ks):.2f}, "
              f"victim's allies within 4 mean {sum(k['def4'] for k in ks) / len(ks):.2f}; victim at a camp {sum(k['at_camp'] for k in ks)}; "
              f"victim's side {Counter(k['side_of_victim'] for k in ks)}; victims {Counter(k['victim'] for k in ks).most_common(6)}; "
              f"bag mean {sum(k['bag'] for k in ks) / len(ks):.0f}; att4 dist {Counter(k['att4'] for k in ks)}; def4 dist {Counter(k['def4'] for k in ks)}")
    print("\n  picks us", picks[0].most_common(8))
    print("  picks them", picks[1].most_common(8))
    for rr in (100, 200, 300):
        for t in (0, 1):
            print(f"  items r{rr} {'us' if t == 0 else 'them'}: {items_by[t][rr].most_common(10)}")
    print("\n  per game (us-them): deaths / kills / gold_other / gold_kill / banked300 / str300")
    for name, s in per_game:
        a, b = s[0], s[1]
        print(f"   {name[:12]} deaths {a.get('deaths', 0):.0f}-{b.get('deaths', 0):.0f} gold_other {a.get('gold_other', 0):.0f}-{b.get('gold_other', 0):.0f} "
              f"gold_kill {a.get('gold_kill', 0):.0f}-{b.get('gold_kill', 0):.0f} banked300 {a.get('banked300', 0):.0f}-{b.get('banked300', 0):.0f} "
              f"str300 {a.get('str300', 0):.0f}-{b.get('str300', 0):.0f}")


if __name__ == "__main__":
    main()
