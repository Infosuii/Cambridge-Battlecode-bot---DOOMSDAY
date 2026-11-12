"""What predicts the result, and how the early deaths happen (all decoded games).
Part 1 (time_budget.py --json output): win rate by early leads (deaths, gold, gems, elk gems, golem gems, wards).
Part 2 (dumps): every death before round CUT: killer (enemy champions within 5 tiles / a camp), numbers there, side of
the map, victim type and bag, what the victim was doing. usage: early_deaths.py CACHE TB_JSON v137 v138 ... [--cut 300]"""
import collections, json, os, statistics as st, sys

sys.stdout.reconfigure(encoding="utf-8")
cache, tbj = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
cut = 300
if "--cut" in args:
    cut = int(args[args.index("--cut") + 1]); args = args[:args.index("--cut")]
versions = set(args)
NAMES = ["ryth", "vesper", "vendetta", "cassi", "issac", "stellar", "prism", "marcella", "willow", "ren", "varg", "tavi", "HoR"]
KIND = {120: "cluster", 1350: "wolf", 2400: "elk", 5000: "golem", 20000: "mono"}
cheb = lambda p, q: max(abs(p[0] - q[0]), abs(p[1] - q[1]))
G = json.load(open(tbj, encoding="utf-8"))
tot = lambda g, side, key, ks: sum(sum(g[side][key][k].values()) if isinstance(g[side][key][k], dict) else g[side][key][k] for k in ks)
src = lambda g, side, s, ks: sum(g[side]["gems"][k].get(s, 0) for k in ks)
print(f"PART 1: win rate by who leads early ({len(G)} games)")
tests = {
    "fewer deaths in r0-150": lambda g: g["them"]["deaths"][0] - g["us"]["deaths"][0],
    "fewer deaths in r0-300": lambda g: sum(g["them"]["deaths"][:2]) - sum(g["us"]["deaths"][:2]),
    "more gold in r0-150": lambda g: tot(g, "us", "gold", (0,)) - tot(g, "them", "gold", (0,)),
    "more gems gained in r0-150": lambda g: tot(g, "us", "gems", (0,)) - tot(g, "them", "gems", (0,)),
    "more gems gained in r0-300": lambda g: tot(g, "us", "gems", (0, 1)) - tot(g, "them", "gems", (0, 1)),
    "more elk gems in r0-300": lambda g: src(g, "us", "elk", (0, 1)) - src(g, "them", "elk", (0, 1)),
    "more cluster gems in r0-300": lambda g: src(g, "us", "cluster", (0, 1)) - src(g, "them", "cluster", (0, 1)),
    "more golem+mono gems r300-800": lambda g: src(g, "us", "golem", (2, 3)) + src(g, "us", "mono", (2, 3)) - src(g, "them", "golem", (2, 3)) - src(g, "them", "mono", (2, 3)),
    "more wards r0-300": lambda g: sum(g["us"]["wards"][:2]) - sum(g["them"]["wards"][:2]),
    "more banked by r300": lambda g: sum(g["us"]["banked"][:2]) - sum(g["them"]["banked"][:2]),
    "higher team HP at r150-300": lambda g: g["us"]["hp"][1] - g["them"]["hp"][1],
}
for name, fn in tests.items():
    lead = [g for g in G if fn(g) > 0]; trail = [g for g in G if fn(g) < 0]; tie = [g for g in G if fn(g) == 0]
    wr = lambda gs: 100 * sum(g["result"] == "win" for g in gs) / max(1, len(gs))
    print(f"  we have {name:30s}: win {wr(lead):3.0f}% ({len(lead):3d} games) | behind: win {wr(trail):3.0f}% ({len(trail):3d}) | level: {wr(tie):3.0f}% ({len(tie)})")
# conditional: early deaths level, does gold decide? gold level-ish, do deaths decide?
dd = lambda g: g["them"]["deaths"][0] - g["us"]["deaths"][0]
gd = lambda g: tot(g, "us", "gold", (0,)) - tot(g, "them", "gold", (0,))
for lab, sel in (("no early death gap", lambda g: dd(g) == 0), ("we died more early", lambda g: dd(g) < 0), ("they died more early", lambda g: dd(g) > 0)):
    gs = [g for g in G if sel(g)]
    a = [g for g in gs if gd(g) > 0]; b = [g for g in gs if gd(g) <= 0]
    print(f"  {lab:22s}: gold lead at 150 -> win {100 * sum(g['result'] == 'win' for g in a) / max(1, len(a)):3.0f}% ({len(a)}); gold behind -> {100 * sum(g['result'] == 'win' for g in b) / max(1, len(b)):3.0f}% ({len(b)})")
# yield per monster round
print("  yield: (gems+gold from wolf/elk/golem/mono) per champion-round spent hitting monsters, us | them")
for res in ("loss", "win"):
    row = []
    for k in range(5):
        def y(side):
            num = sum(sum(g[side]["gems"][k].get(s, 0) + g[side]["gold"][k].get(s, 0) for s in ("wolf", "elk", "golem", "mono")) for g in G if g["result"] == res)
            den = sum(g[side]["act"][k].get("monster", 0) for g in G if g["result"] == res)
            return num / max(1, den)
        row.append(f"{y('us'):4.1f} | {y('them'):4.1f}")
    print(f"    our {res:4s}: " + "   ".join(row))
by_n = collections.defaultdict(list)
for g in G:
    by_n[g["n"]].append(g)
print("  by bodies on our team: " + ", ".join(f"{n}: win {100 * sum(g['result'] == 'win' for g in gs) / len(gs):.0f}% of {len(gs)} (early deaths us {st.mean(g['us']['deaths'][0] for g in gs):.2f} them {st.mean(g['them']['deaths'][0] for g in gs):.2f})" for n, gs in sorted(by_n.items())))

print(f"\nPART 2: deaths before round {cut}")
matches = json.load(open(os.path.join(cache, "matches.json"), encoding="utf-8"))
rows = []
ngames = 0
for mt in matches:
    if mt.get("version") not in versions:
        continue
    p = os.path.join(cache, "dumps", mt["matchId"] + ".json")
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding="utf-8"))
    ngames += 1
    us = 0 if mt["us"].get("side", "a") == "a" else 1
    fr = {f[0]: {u[0]: u for u in f[1]} for f in d["frames"] if f[0] <= cut + 1}
    R = sorted(fr)
    f0 = fr[R[0]]
    cen = {t: (st.mean(u[3] for u in f0.values() if u[1] == t and u[3] is not None), st.mean(u[4] for u in f0.values() if u[1] == t and u[3] is not None)) for t in (0, 1)}
    camps = [((c[1], c[2]), KIND.get(int(c[3]), "other")) for c in d["camps0"]]
    last_atk = {}
    for s in d["steps"]:
        if s[0] > cut:
            break
        if s[1] in ("Attack", "Cast ability") and s[5] is not None:
            ck = next((k for p_, k in camps if p_ == (s[5], s[6])), None)
            last_atk[s[2]] = (s[0], ck or "champ")
            # keep history by round for lookup at death
            last_atk.setdefault(("h", s[2]), []).append((s[0], ck or "champ"))
    for a, b in zip(R, R[1:]):
        for i, u in fr[b].items():
            p_ = fr[a].get(i)
            if not (p_ and p_[6] and not u[6] and p_[3] is not None):
                continue
            pos = (p_[3], p_[4]); t = u[1]
            foes = [e for e in fr[a].values() if e[1] != t and e[6] and e[3] is not None and cheb((e[3], e[4]), pos) <= 5]
            friends = [e for e in fr[a].values() if e[1] == t and e[6] and e[0] != i and e[3] is not None and cheb((e[3], e[4]), pos) <= 5]
            mon = [k for cp, k in camps if k in ("wolf", "elk", "golem", "mono") and cheb(cp, pos) <= 4]
            hist = [x for x in last_atk.get(("h", i), []) if b - 4 <= x[0] <= b]
            doing = "hitting monsters" if any(x[1] in ("wolf", "elk", "golem", "mono") for x in hist) else "hitting champion" if any(x[1] == "champ" for x in hist) else "hitting cluster" if hist else "not attacking"
            killer = "champions" if foes else "camp" if mon else "unknown"
            if foes and mon and doing == "hitting monsters":
                killer = "champions while at a camp"
            dso, dse = cheb(pos, cen[t]), cheb(pos, cen[1 - t])
            side = "own third" if dso < 0.5 * dse else "enemy third" if dse < 0.5 * dso else "middle"
            rows.append(dict(who="us" if t == us else "them", round=b, killer=killer, foes=len(foes), friends=len(friends), side=side, type=NAMES[u[2]], bag=p_[7] or 0, doing=doing,
                             result=mt["us"].get("result"), map=mt.get("map"), maxhp_foe=max((e[5] or 0) for e in foes) if foes else 0, hp_prev=p_[5] or 0))
print(f"{ngames} games")
for who in ("us", "them"):
    W = [r for r in rows if r["who"] == who]
    n = len(W) or 1
    c = lambda key: ", ".join(f"{k} {100 * v // n}%" for k, v in collections.Counter(r[key] for r in W).most_common(6))
    print(f"  {who}: {len(W)} deaths ({len(W) / ngames:.2f} per game); before r150: {sum(r['round'] < 150 for r in W) / ngames:.2f}")
    print(f"     killer: {c('killer')}")
    print(f"     victim was: {c('doing')}")
    print(f"     where: {c('side')}")
    ch = [r for r in W if r['foes']]
    print(f"     when champions were there: mean foes {st.mean(r['foes'] for r in ch):.2f} vs friends beside the victim {st.mean(r['friends'] for r in ch):.2f}; alone (no friend within 5) {100 * sum(r['friends'] == 0 for r in ch) // max(1, len(ch))}%; 2+ foes {100 * sum(r['foes'] >= 2 for r in ch) // max(1, len(ch))}%")
    print(f"     victim type: {c('type')}   mean bag {st.mean(r['bag'] for r in W):.1f}")
json.dump(rows, open(os.path.join(cache, "early_deaths.json"), "w"))
