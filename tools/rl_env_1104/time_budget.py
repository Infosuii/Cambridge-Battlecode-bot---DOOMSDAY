"""Where the turns go and where the gems come from, across all decoded ladder games (ladder_decode.py dumps).
Per game, team and phase: champion-rounds by activity (dead, hitting monsters / clusters / champions, moving,
recalling, depositing, capturing, waiting), gems and gold gained by source (the strongest camp within 3 tiles of the
gain, or a kill), banked, deaths. Aggregated over wins and losses, with a per-map sign check for the headline gaps.
usage: time_budget.py --cache DIR --versions v137 v138 ... [--json OUT]"""
import argparse, collections, json, os, statistics as st, sys

ap = argparse.ArgumentParser()
ap.add_argument("--cache", required=True)
ap.add_argument("--versions", nargs="+", required=True)
ap.add_argument("--json")
a = ap.parse_args()
sys.stdout.reconfigure(encoding="utf-8")
PH = [(0, 150), (150, 300), (300, 500), (500, 800), (800, 9999)]
PN = ["0-150", "150-300", "300-500", "500-800", "800+"]
ph = lambda r: 0 if r < 150 else 1 if r < 300 else 2 if r < 500 else 3 if r < 800 else 4
KIND = {120: "cluster", 1350: "wolf", 2400: "elk", 5000: "golem", 20000: "mono"}
RANK = {"cluster": 1, "wolf": 2, "elk": 3, "golem": 4, "mono": 5}
ACTS = ["dead", "monster", "cluster", "champ", "move", "recall", "deposit", "capture", "wait"]
cheb = lambda p, q: max(abs(p[0] - q[0]), abs(p[1] - q[1]))


def analyse(d, us):
    fr = {f[0]: {u[0]: u for u in f[1]} for f in d["frames"]}
    R = sorted(fr)
    team = {i: u[1] for i, u in fr[R[0]].items()}
    camps = {(c[1], c[2]): KIND.get(int(c[3]), "other") for c in d["camps0"]}
    grid = collections.defaultdict(list)
    for p, k in camps.items():
        grid[(p[0] // 4, p[1] // 4)].append((p, k))

    def near_kind(pos):
        best = None
        for gx in (pos[0] // 4 - 1, pos[0] // 4, pos[0] // 4 + 1):
            for gy in (pos[1] // 4 - 1, pos[1] // 4, pos[1] // 4 + 1):
                for p, k in grid.get((gx, gy), ()):
                    if cheb(p, pos) <= 3 and (best is None or RANK.get(k, 0) > RANK.get(best, 0)):
                        best = k
        return best or "other"

    act_at = collections.defaultdict(dict)  # unit -> round -> label
    recall_at, sub_at, done_at, cancel_at = (collections.defaultdict(list) for _ in range(4))
    wards = collections.Counter()
    for s in d["steps"]:
        r, k, u = s[0], s[1], s[2]
        if k in ("Attack", "Cast ability") and s[5] is not None:
            ck = camps.get((s[5], s[6]))
            lab = "champ" if ck is None else "cluster" if ck == "cluster" else "monster"
            if ck is None and k == "Cast ability" and act_at[u].get(r):
                continue
            prev = act_at[u].get(r)
            if prev != "monster":
                act_at[u][r] = lab if not (prev == "cluster" and lab == "champ") else prev
        elif k == "Recall":
            recall_at[u].append(r)
        elif k == "Submit gems":
            sub_at[u].append(r)
        elif k == "Gems submitted":
            done_at[u].append(r)
        elif k == "Cancel channel":
            cancel_at[u].append(r)
        elif k == "Place ward":
            wards[(team.get(u), ph(r))] += 1
    out = {t: {"act": [collections.Counter() for _ in PH], "gems": [collections.Counter() for _ in PH],
               "gold": [collections.Counter() for _ in PH], "banked": [0] * 5, "deaths": [0] * 5, "lost": [0] * 5,
               "hp": [0] * 5, "wards": [wards[(t, k)] for k in range(5)]} for t in (0, 1)}
    death_log = []
    prev = fr[R[0]]
    hpmax = collections.defaultdict(lambda: [0] * 5)
    for idx in range(1, len(R)):
        r = R[idx]
        cur = fr[r]
        k = ph(r)
        for i, u in cur.items():
            p = prev.get(i)
            if p is None:
                continue
            t = team[i]
            o = out[t]
            if not u[6]:
                o["act"][k]["dead"] += 1
                if p[6]:
                    o["deaths"][k] += 1
                    o["lost"][k] += p[7] or 0
                    if p[3] is not None:
                        death_log.append((r, t, (p[3], p[4])))
                continue
            if u[3] is None:
                continue
            pos = (u[3], u[4])
            hpmax[i][k] = max(hpmax[i][k], u[5] or 0)
            dgem = (u[7] or 0) - (p[7] or 0)
            dgold = (u[8] or 0) - (p[8] or 0)
            dep = any(r - 1 <= x <= r for x in done_at[i])
            if dgem > 0:
                src = "kill" if any(dt != t and r - 2 <= dr <= r and cheb(dp, pos) <= 3 for dr, dt, dp in death_log[-12:]) else near_kind(pos)
                o["gems"][k][src] += dgem
            elif dgem < 0 and dep:
                o["banked"][k] += -dgem
            if dgold > 0:
                o["gold"][k]["tribute" if dep else near_kind(pos)] += dgold
            lab = act_at[i].get(r)
            if lab is None:
                if p[3] is not None and (p[3], p[4]) != pos:
                    lab = "move"
                elif any(r - 6 <= x <= r and not any(x < c <= r for c in cancel_at[i]) for x in recall_at[i][-3:]):
                    lab = "recall"
                elif any(x <= r and not any(x < y < r for y in done_at[i]) and r - x <= 14 for x in sub_at[i][-2:]):
                    lab = "deposit"
                else:
                    gain = False
                    for j in range(idx + 1, min(idx + 6, len(R))):
                        f = fr[R[j]].get(i)
                        if f and ((f[7] or 0) > (u[7] or 0) or (f[8] or 0) > (u[8] or 0)):
                            gain = True
                            break
                    lab = "capture" if gain else "wait"
            o["act"][k][lab] += 1
        prev = cur
    for i, v in hpmax.items():
        for k in range(5):
            out[team[i]]["hp"][k] += v[k]
    return {"us": out[us], "them": out[1 - us], "rounds": R[-1], "n": sum(1 for i in team if team[i] == us)}


matches = json.load(open(os.path.join(a.cache, "matches.json"), encoding="utf-8"))
games = []
for mt in matches:
    if mt.get("version") not in a.versions:
        continue
    p = os.path.join(a.cache, "dumps", mt["matchId"] + ".json")
    if not os.path.exists(p):
        continue
    try:
        g = analyse(json.load(open(p, encoding="utf-8")), 0 if mt["us"].get("side", "a") == "a" else 1)
    except Exception as e:
        continue
    g.update(map=mt.get("map"), result=mt["us"].get("result"), opp=mt["opp"].get("name"), version=mt["version"])
    games.append(g)
if a.json:
    def plain(o):
        return {k: ([dict(c) for c in v] if k in ("act", "gems", "gold") else v) for k, v in o.items()}
    json.dump([{**{k: v for k, v in g.items() if k not in ("us", "them")}, "us": plain(g["us"]), "them": plain(g["them"])} for g in games], open(a.json, "w"))
print(f"{len(games)} games, {len({g['map'] for g in games})} maps, {len({g['opp'] for g in games})} opponents; "
      f"{collections.Counter(g['result'] for g in games)}")


def share(gs, side, key, labels, k):
    tot = collections.Counter()
    for g in gs:
        tot.update(g[side][key][k])
    s = sum(tot.values()) or 1
    return [100 * tot[l] / s for l in labels], s / max(1, len(gs))


for res in ("loss", "win"):
    gs = [g for g in games if g["result"] == res]
    if not gs:
        continue
    print(f"\n================ our {res}es: {len(gs)} games ================" if res == "loss" else f"\n================ our wins: {len(gs)} games ================")
    print("TIME BUDGET, % of champion-rounds (us | them)")
    print("  phase      " + "  ".join(f"{x:>13s}" for x in ACTS))
    for k in range(5):
        u, _ = share(gs, "us", "act", ACTS, k)
        t, _ = share(gs, "them", "act", ACTS, k)
        print(f"  {PN[k]:9s}  " + "  ".join(f"{x:5.1f} | {y:5.1f}" for x, y in zip(u, t)))
    SRC = ["cluster", "wolf", "elk", "golem", "mono", "kill", "other"]
    print("GEMS GAINED per game by source (us | them)")
    print("  phase      " + "  ".join(f"{x:>11s}" for x in SRC) + "        total")
    for k in range(5):
        u, us_tot = share(gs, "us", "gems", SRC, k)
        t, th_tot = share(gs, "them", "gems", SRC, k)
        print(f"  {PN[k]:9s}  " + "  ".join(f"{x * us_tot / 100:4.0f} | {y * th_tot / 100:4.0f}" for x, y in zip(u, t)) + f"   {us_tot:5.0f} | {th_tot:5.0f}")
    print("PER GAME by phase: banked us|them, deaths us|them, bags lost us|them, wards us|them, team HP sum us|them, gold in us|them")
    for k in range(5):
        m = lambda side, key: st.mean(g[side][key][k] for g in gs)
        gold = lambda side: st.mean(sum(g[side]["gold"][k].values()) for g in gs)
        print(f"  {PN[k]:9s}  banked {m('us', 'banked'):4.0f} | {m('them', 'banked'):4.0f}   deaths {m('us', 'deaths'):4.2f} | {m('them', 'deaths'):4.2f}   lost {m('us', 'lost'):3.0f} | {m('them', 'lost'):3.0f}"
              f"   wards {m('us', 'wards'):3.0f} | {m('them', 'wards'):3.0f}   hp {m('us', 'hp'):6.0f} | {m('them', 'hp'):6.0f}   gold {gold('us'):5.0f} | {gold('them'):5.0f}")
# Per-map sign check in losses: on how many maps (2+ losses) does the gap have the same sign?
print("\n================ per-map consistency in losses (maps with 2+ losses) ================")
bymap = collections.defaultdict(list)
for g in games:
    if g["result"] == "loss":
        bymap[g["map"]].append(g)
maps = {m: gs for m, gs in bymap.items() if len(gs) >= 2}
tot = lambda g, side, key, ks: sum(sum(g[side][key][k].values()) if isinstance(g[side][key][k], dict) else g[side][key][k] for k in ks)
actp = lambda g, side, lab, ks: 100 * sum(g[side]["act"][k][lab] for k in ks) / max(1, sum(sum(g[side]["act"][k].values()) for k in ks))
checks = {
    "gems gained r0-300 (us-them)": lambda g: tot(g, "us", "gems", (0, 1)) - tot(g, "them", "gems", (0, 1)),
    "gems gained r300-800 (us-them)": lambda g: tot(g, "us", "gems", (2, 3)) - tot(g, "them", "gems", (2, 3)),
    "gold in r0-300": lambda g: tot(g, "us", "gold", (0, 1)) - tot(g, "them", "gold", (0, 1)),
    "gold in r300-800": lambda g: tot(g, "us", "gold", (2, 3)) - tot(g, "them", "gold", (2, 3)),
    "wait % r300-800": lambda g: actp(g, "us", "wait", (2, 3)) - actp(g, "them", "wait", (2, 3)),
    "move % r300-800": lambda g: actp(g, "us", "move", (2, 3)) - actp(g, "them", "move", (2, 3)),
    "monster % r300-800": lambda g: actp(g, "us", "monster", (2, 3)) - actp(g, "them", "monster", (2, 3)),
    "champ-fight % r300-800": lambda g: actp(g, "us", "champ", (2, 3)) - actp(g, "them", "champ", (2, 3)),
    "dead % r300-800": lambda g: actp(g, "us", "dead", (2, 3)) - actp(g, "them", "dead", (2, 3)),
    "recall % r300-800": lambda g: actp(g, "us", "recall", (2, 3)) - actp(g, "them", "recall", (2, 3)),
    "team HP sum r300-500": lambda g: g["us"]["hp"][2] - g["them"]["hp"][2],
    "wards r0-800": lambda g: sum(g["us"]["wards"][:4]) - sum(g["them"]["wards"][:4]),
    "bags lost all game": lambda g: sum(g["us"]["lost"]) - sum(g["them"]["lost"]),
}
print(f"{len(maps)} maps")
for name, fn in checks.items():
    per = [st.mean(fn(g) for g in gs) for gs in maps.values()]
    print(f"  {name:32s} mean gap {st.mean(per):8.1f}   we are lower on {sum(x < 0 for x in per):2d} / higher on {sum(x > 0 for x in per):2d} maps")
