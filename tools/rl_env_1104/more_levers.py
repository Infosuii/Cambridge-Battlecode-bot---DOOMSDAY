"""More levers from decoded ladder games: record by version and opponent, lineups, the opening (pairing, first camp,
first purchase, gold sources by round 150), first contact (who starts it, numbers, who dies first), what a kill pays.
usage: more_levers.py CACHE v137 v138 ... [--only v140 v141]   (--only: versions for the 'current bot' columns)"""
import collections, json, os, statistics as st, sys

sys.stdout.reconfigure(encoding="utf-8")
cache = sys.argv[1]
args = sys.argv[2:]
only = set()
if "--only" in args:
    only = set(args[args.index("--only") + 1:]); args = args[:args.index("--only")]
versions = set(args)
NAMES = ["ryth", "vesper", "vendetta", "cassi", "issac", "stellar", "prism", "marcella", "willow", "ren", "varg", "tavi", "HoR"]
KIND = {120: "cluster", 1350: "wolf", 2400: "elk", 5000: "golem", 20000: "mono"}
cheb = lambda p, q: max(abs(p[0] - q[0]), abs(p[1] - q[1]))
matches = json.load(open(os.path.join(cache, "matches.json"), encoding="utf-8"))
G = []
for mt in matches:
    if mt.get("version") not in versions:
        continue
    p = os.path.join(cache, "dumps", mt["matchId"] + ".json")
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding="utf-8"))
    us = 0 if mt["us"].get("side", "a") == "a" else 1
    fr = {f[0]: {u[0]: u for u in f[1]} for f in d["frames"] if f[0] <= 320}
    R = sorted(fr)
    f0 = fr[R[0]]
    team = {i: u[1] for i, u in f0.items()}
    typ = {i: u[2] for i, u in f0.items()}
    cen = {t: (st.mean(u[3] for u in f0.values() if u[1] == t and u[3] is not None), st.mean(u[4] for u in f0.values() if u[1] == t and u[3] is not None)) for t in (0, 1)}
    camps = {(c[1], c[2]): KIND.get(int(c[3]), "other") for c in d["camps0"]}
    g = dict(result=mt["us"].get("result"), version=mt["version"], opp=mt["opp"].get("name"), map=mt.get("map"),
             ours=sorted(NAMES[typ[i]] for i in team if team[i] == us), theirs=sorted(NAMES[typ[i]] for i in team if team[i] != us))
    first_camp, first_camp_round, first_shop = {}, {}, {}
    contact = None
    for s in d["steps"]:
        r, k, u = s[0], s[1], s[2]
        if r > 300:
            break
        if k == "Shop" and u not in first_shop:
            first_shop[u] = r
        if k in ("Attack", "Cast ability") and s[5] is not None:
            ck = camps.get((s[5], s[6]))
            if ck and u not in first_camp:
                first_camp[u], first_camp_round[u] = ck, r
            if ck is None and contact is None and k == "Attack":
                f = fr.get(r) or {}
                tgt = next((e for e in f.values() if e[1] != team.get(u) and e[6] and e[3] == s[5] and e[4] == s[6]), None)
                me = f.get(u)
                if tgt and me and me[3] is not None:
                    pos = (me[3], me[4])
                    na = sum(1 for e in f.values() if e[1] == team[u] and e[6] and e[3] is not None and cheb((e[3], e[4]), pos) <= 6)
                    nd = sum(1 for e in f.values() if e[1] != team[u] and e[6] and e[3] is not None and cheb((e[3], e[4]), pos) <= 6)
                    dso, dse = cheb(pos, cen[team[u]]), cheb(pos, cen[1 - team[u]])
                    contact = dict(round=r, by="us" if team[u] == us else "them", na=na, nd=nd, zone="own" if dso < 0.5 * dse else "enemy" if dse < 0.5 * dso else "middle")
    # first death after contact, kill pay
    deaths = []
    pay = []
    for a, b in zip(R, R[1:]):
        for i, u in fr[b].items():
            p_ = fr[a].get(i)
            if p_ and p_[6] and not u[6] and p_[3] is not None:
                deaths.append((b, team[i]))
                pos = (p_[3], p_[4])
                near = [j for j, e in fr[a].items() if team[j] != team[i] and e[6] and e[3] is not None and cheb((e[3], e[4]), pos) <= 5]
                gold = sum(max(0, (fr[b2][j][8] or 0) - (fr[a][j][8] or 0)) for j in near for b2 in (R[min(len(R) - 1, R.index(b) + 1)],) if j in fr[b2])
                gems = sum(max(0, (fr[b2][j][7] or 0) - (fr[a][j][7] or 0)) for j in near for b2 in (R[min(len(R) - 1, R.index(b) + 1)],) if j in fr[b2])
                pay.append((gold, gems, p_[7] or 0))
    g["contact"] = contact
    if contact:
        fd = next((t for rr, t in deaths if rr >= contact["round"] and rr <= contact["round"] + 20), None)
        g["first_death"] = None if fd is None else ("us" if fd == us else "them")
    g["first_blood"] = None if not deaths else ("us" if deaths[0][1] == us else "them")  # who DIED first
    g["first_blood_round"] = deaths[0][0] if deaths else None
    g["pay"] = pay
    for side, t in (("us", us), ("them", 1 - us)):
        ids = [i for i in team if team[i] == t]
        paired = tot = 0
        for r in R:
            if r > 100:
                break
            ps = {i: (fr[r][i][3], fr[r][i][4]) for i in ids if i in fr[r] and fr[r][i][6] and fr[r][i][3] is not None}
            for i, p_ in ps.items():
                tot += 1
                paired += any(j != i and cheb(q, p_) <= 4 for j, q in ps.items())
        r150 = max(r for r in R if r <= 150)
        g[side] = dict(paired=100 * paired / max(1, tot), first_camp=collections.Counter(first_camp.get(i, "none") for i in ids),
                       first_camp_round=st.mean(first_camp_round.get(i, 150) for i in ids), first_shop=st.mean(first_shop.get(i, 300) for i in ids),
                       shopped150=sum(first_shop.get(i, 999) <= 150 for i in ids) / len(ids),
                       pocket150=st.mean((fr[r150][i][8] or 0) for i in ids if i in fr[r150]), n=len(ids))
    G.append(g)
wr = lambda gs: 100 * sum(x["result"] == "win" for x in gs) / max(1, len(gs))
print(f"{len(G)} games")
print("RECORD by version: " + ", ".join(f"{v} {sum(x['result'] == 'win' for x in gs)}-{sum(x['result'] != 'win' for x in gs)}" for v, gs in sorted(collections.defaultdict(list, {v: [x for x in G if x['version'] == v] for v in versions}).items())))
cur = [x for x in G if x["version"] in only] if only else G
old = [x for x in G if x["version"] not in only] if only else []
print(f"current bot ({sorted(only)}): {len(cur)} games, win {wr(cur):.0f}%; earlier versions: {len(old)} games, win {wr(old):.0f}%")
byopp = collections.defaultdict(list)
for x in cur:
    byopp[x["opp"]].append(x)
print("current bot by opponent: " + ", ".join(f"{o} {sum(x['result'] == 'win' for x in gs)}-{sum(x['result'] != 'win' for x in gs)}" for o, gs in sorted(byopp.items(), key=lambda kv: -len(kv[1]))[:14]))
for label, gs in (("ALL", G), ("CURRENT", cur)):
    print(f"\n==== {label} ({len(gs)} games) ====")
    lin = collections.defaultdict(list)
    for x in gs:
        lin[" ".join(x["ours"])].append(x)
    print("our lineups: " + "; ".join(f"[{k}] {wr(v):.0f}% of {len(v)}" for k, v in sorted(lin.items(), key=lambda kv: -len(kv[1]))[:8]))
    for side in ("ours", "theirs"):
        print(f"win rate when {side} include: " + ", ".join(f"{n} {wr([x for x in gs if n in x[side]]):.0f}% ({sum(n in x[side] for x in gs)})" for n in NAMES if sum(n in x[side] for x in gs) >= 8))
    for res in ("win", "loss"):
        rs = [x for x in gs if x["result"] == res]
        if not rs:
            continue
        m = lambda side, key: st.mean(x[side][key] for x in rs)
        fc = lambda side: ", ".join(f"{k} {100 * v // sum(c.values())}%" for c in [sum((x[side]["first_camp"] for x in rs), collections.Counter())] for k, v in c.most_common(4))
        print(f"  our {res}: paired in r0-100 us {m('us', 'paired'):.0f}% them {m('them', 'paired'):.0f}% | first camp hit at round us {m('us', 'first_camp_round'):.0f} them {m('them', 'first_camp_round'):.0f} | first purchase round us {m('us', 'first_shop'):.0f} them {m('them', 'first_shop'):.0f} | bought by r150 us {100 * m('us', 'shopped150'):.0f}% them {100 * m('them', 'shopped150'):.0f}% | pocket gold at r150 us {m('us', 'pocket150'):.0f} them {m('them', 'pocket150'):.0f}")
        print(f"      first camp type us: {fc('us')} | them: {fc('them')}")
    for name, fn in (("we bought earlier (mean first purchase)", lambda x: x["them"]["first_shop"] - x["us"]["first_shop"]),
                     ("more of us bought by r150", lambda x: x["us"]["shopped150"] - x["them"]["shopped150"]),
                     ("we were more paired in r0-100", lambda x: x["us"]["paired"] - x["them"]["paired"]),
                     ("we hit a camp earlier", lambda x: x["them"]["first_camp_round"] - x["us"]["first_camp_round"])):
        a = [x for x in gs if fn(x) > 0]; b = [x for x in gs if fn(x) < 0]
        print(f"  {name:40s}: win {wr(a):3.0f}% ({len(a)}) | otherwise {wr(b):3.0f}% ({len(b)})")
    fb = [x for x in gs if x["first_blood"]]
    a = [x for x in fb if x["first_blood"] == "them"]; b = [x for x in fb if x["first_blood"] == "us"]
    print(f"  first death of the game is THEIRS: win {wr(a):.0f}% ({len(a)}) | OURS: win {wr(b):.0f}% ({len(b)}); median round of first death {st.median(x['first_blood_round'] for x in fb):.0f}")
    ct = [x for x in gs if x["contact"]]
    print(f"  first contact: median round {st.median(x['contact']['round'] for x in ct):.0f}; started by us {100 * sum(x['contact']['by'] == 'us' for x in ct) // len(ct)}%; zone of the attacker: {dict(collections.Counter(x['contact']['zone'] for x in ct))}")
    for by in ("us", "them"):
        for lab, sel in (("attacker has more bodies within 6", lambda c: c["na"] > c["nd"]), ("level", lambda c: c["na"] == c["nd"]), ("attacker has fewer", lambda c: c["na"] < c["nd"])):
            xs = [x for x in ct if x["contact"]["by"] == by and sel(x["contact"])]
            if len(xs) < 5:
                continue
            fd = [x for x in xs if x.get("first_death")]
            print(f"     started by {by:4s}, {lab:34s}: {len(xs):3d} games; a death within 20 rounds in {100 * len(fd) // len(xs)}%, the attacker's side died first in {100 * sum(x['first_death'] == by for x in fd) // max(1, len(fd))}%; we win the game {wr(xs):.0f}%")
    pay = [p for x in gs for p in x["pay"]]
    print(f"  a kill before r300 pays the killers within 5 tiles: gold +{st.mean(p[0] for p in pay):.0f}, gems +{st.mean(p[1] for p in pay):.1f} (victim's bag {st.mean(p[2] for p in pay):.1f}); n={len(pay)}")
