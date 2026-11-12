"""Depositing under pressure and fighting with numbers, us v opponents, over decoded ladder games.
A  channel mechanics: deposit duration by bag, what ends a deposit, whether damage interrupts it
B  deposits started with / without an enemy near: completed, cancelled, died
C  carriers (20+ gems) arriving within 8 of an altar: deposit / die / walk away, by enemy presence
D  number advantage (our bodies within 5 > their bodies within 6): how often the champion attacks a champion
E  deaths with a bag of 20+ within 10 tiles of an altar
usage: deposit_fights.py CACHE v137 v138 ... [--only v140 v141]"""
import collections, json, os, statistics as st, sys

sys.stdout.reconfigure(encoding="utf-8")
cache = sys.argv[1]
args = sys.argv[2:]
only = set()
if "--only" in args:
    only = set(args[args.index("--only") + 1:]); args = args[:args.index("--only")]
versions = set(args)
cheb = lambda p, q: max(abs(p[0] - q[0]), abs(p[1] - q[1]))
matches = json.load(open(os.path.join(cache, "matches.json"), encoding="utf-8"))
DEP, ARR, ADV, DTH = [], [], collections.Counter(), []
ngames = collections.Counter()
for mt in matches:
    v = mt.get("version")
    if v not in versions:
        continue
    p = os.path.join(cache, "dumps", mt["matchId"] + ".json")
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding="utf-8"))
    cur = v in only
    ngames[cur] += 1
    us = 0 if mt["us"].get("side", "a") == "a" else 1
    fr = {f[0]: {u[0]: u for u in f[1]} for f in d["frames"]}
    R = sorted(fr)
    team = {i: u[1] for i, u in fr[R[0]].items()}
    who = lambda i: "us" if team[i] == us else "them"
    ev = collections.defaultdict(list)  # unit -> [(round, kind)]
    atk_champ = collections.defaultdict(set)  # round -> units that attacked a champion
    altars = set()
    for s in d["steps"]:
        r, k, u = s[0], s[1], s[2]
        if k in ("Submit gems", "Gems submitted", "Cancel channel", "Recall"):
            ev[u].append((r, k))
            if k == "Submit gems" and s[5] is not None:
                altars.add((s[5], s[6]))
        elif k in ("Attack", "Cast ability") and s[5] is not None:
            f = fr.get(r) or {}
            if any(e[1] != team.get(u) and e[6] and e[3] == s[5] and e[4] == s[6] for e in f.values()):
                atk_champ[r].add(u)
    altars = sorted(altars)
    alive_pos = lambda r: [(i, (u[3], u[4])) for i, u in fr[r].items() if u[6] and u[3] is not None]
    # A / B: deposits
    chan = collections.defaultdict(list)  # unit -> [(start, end)]
    for u, es in ev.items():
        for k, (r, kind) in enumerate(es):
            if kind != "Submit gems" or r not in fr or u not in fr[r]:
                continue
            f0 = fr.get(r - 1, fr[r]).get(u) or fr[r][u]
            bag = f0[7] or 0
            end, out = None, "unknown"
            for r2, k2 in es[k + 1:]:
                if k2 == "Gems submitted":
                    end, out = r2, "completed"; break
                if k2 in ("Cancel channel", "Submit gems", "Recall"):
                    end, out = r2, "cancelled" if k2 == "Cancel channel" else "restarted"; break
            lim = end if end is not None else min(R[-1], r + 40)
            hp0 = f0[5] or 0
            hpmin = hp0
            for rr in range(r, lim + 1):
                uu = fr.get(rr, {}).get(u)
                if uu is None:
                    continue
                if not uu[6]:
                    if out != "completed" or rr < (end or 10 ** 9):
                        end, out = rr, "died"
                    break
                hpmin = min(hpmin, uu[5] or 0)
            pos = (f0[3], f0[4]) if f0[3] is not None else None
            foes_start = sum(1 for i, q in alive_pos(r) if team[i] != team[u] and pos and cheb(q, pos) <= 6) if pos else 0
            friends_start = sum(1 for i, q in alive_pos(r) if team[i] == team[u] and i != u and pos and cheb(q, pos) <= 6) if pos else 0
            foes_during = 0
            if pos and end:
                for rr in range(r, end + 1):
                    if rr in fr:
                        foes_during = max(foes_during, sum(1 for i, q in alive_pos(rr) if team[i] != team[u] and cheb(q, pos) <= 5))
            DEP.append(dict(cur=cur, who=who(u), bag=bag, dur=(end - r) if end else None, out=out, hit=hpmin < hp0 - 1, foes=foes_start, friends=friends_start, foes_during=foes_during, lead=0))
            if end:
                chan[u].append((r, end))
    if not altars:
        continue
    in_chan = lambda u, r: any(a <= r <= b for a, b in chan[u])
    # C: arrivals of carriers; D: advantage; E: deaths near altars
    near_prev = collections.defaultdict(bool)
    prev = fr[R[0]]
    for idx in range(1, len(R)):
        r = R[idx]
        f = fr[r]
        ap = alive_pos(r)
        for i, pos in ap:
            u = f[i]
            t = team[i]
            foes = [q for j, q in ap if team[j] != t and cheb(q, pos) <= 6]
            if foes:
                friends = 1 + sum(1 for j, q in ap if team[j] == t and j != i and cheb(q, pos) <= 5)
                m = friends - len(foes)
                key = (cur, who(i), "+2 or more" if m >= 2 else "+1" if m == 1 else "level" if m == 0 else "behind", "bag20+" if (u[7] or 0) >= 20 else "light")
                ADV[key + ("rounds",)] += 1
                ADV[key + ("attacks",)] += i in atk_champ.get(r, ()) or i in atk_champ.get(r + 1, ())
            bag = u[7] or 0
            da = min(cheb(pos, a) for a in altars)
            near = bag >= 20 and da <= 8
            if near and not near_prev[i]:
                foes8 = sum(1 for j, q in ap if team[j] != t and cheb(q, pos) <= 8)
                friends8 = sum(1 for j, q in ap if team[j] == t and j != i and cheb(q, pos) <= 8)
                out, wait = "still there", None
                for r2 in R[idx:idx + 40]:
                    u2 = fr[r2].get(i)
                    if u2 is None:
                        break
                    if not u2[6]:
                        out = "died"; break
                    if (u2[7] or 0) < bag - 5 and any(a <= r2 + 1 and b >= r2 - 1 for a, b in chan[i]):
                        out, wait = "deposited", r2 - r; break
                    if u2[3] is not None and min(cheb((u2[3], u2[4]), a) for a in altars) > 12:
                        out = "walked away"; break
                ARR.append(dict(cur=cur, who=who(i), foes=foes8, friends=friends8, out=out, wait=wait, bag=bag))
            near_prev[i] = near
        for i, u in f.items():
            p_ = prev.get(i)
            if p_ and p_[6] and not u[6] and p_[3] is not None and (p_[7] or 0) >= 20:
                pos = (p_[3], p_[4])
                if min(cheb(pos, a) for a in altars) <= 10:
                    pp = [(j, (e[3], e[4])) for j, e in prev.items() if e[6] and e[3] is not None]
                    DTH.append(dict(cur=cur, who=who(i), bag=p_[7], chan=in_chan(i, r - 1) or in_chan(i, r),
                                    friends=sum(1 for j, q in pp if team[j] == team[i] and j != i and cheb(q, pos) <= 6),
                                    foes=sum(1 for j, q in pp if team[j] != team[i] and cheb(q, pos) <= 6)))
        prev = f
pct = lambda a, b: f"{100 * a / max(1, b):.0f}%"
for label, sel in (("ALL", lambda x: True), ("CURRENT " + " ".join(sorted(only)), lambda x: x["cur"])):
    n = sum(ngames.values()) if label == "ALL" else ngames[True]
    print(f"\n================ {label}: {n} games ================")
    D = [x for x in DEP if sel(x)]
    if label == "ALL":
        print("A  deposit duration (completed) by bag: " + ", ".join(f"{a}-{b}: {st.mean(x['dur'] for x in xs):.1f} rounds (n {len(xs)})" for a, b in ((1, 10), (10, 20), (20, 30), (30, 45), (45, 60), (60, 90), (90, 150), (150, 999)) for xs in [[x for x in D if x["out"] == "completed" and a <= x["bag"] < b]] if xs))
        hit = [x for x in D if x["hit"]]
        print(f"A  deposits during which the depositor lost health: {len(hit)}; outcome {dict(collections.Counter(x['out'] for x in hit))}  -> damage alone does" + (" NOT" if sum(x['out'] == 'completed' for x in hit) > 0.2 * len(hit) else "") + " interrupt")
    for w in ("us", "them"):
        W = [x for x in D if x["who"] == w]
        for lab, s2 in (("no enemy within 6 at the start", lambda x: x["foes"] == 0), ("enemy within 6 at the start", lambda x: x["foes"] > 0), ("an enemy came within 5 during", lambda x: x["foes"] == 0 and x["foes_during"] > 0)):
            xs = [x for x in W if s2(x)]
            c = collections.Counter(x["out"] for x in xs)
            print(f"B  {w:4s} deposits, {lab:32s}: {len(xs):5d} ({len(xs) / max(1, n):5.1f}/game)  completed {pct(c['completed'], len(xs))} cancelled {pct(c['cancelled'] + c['restarted'], len(xs))} died {pct(c['died'], len(xs))}  mean bag {st.mean(x['bag'] for x in xs) if xs else 0:.0f}")
    A = [x for x in ARR if sel(x)]
    for w in ("us", "them"):
        for lab, s2 in (("no enemy within 8", lambda x: x["foes"] == 0), ("enemy within 8, we have fewer or equal bodies", lambda x: x["foes"] > 0 and x["friends"] + 1 <= x["foes"]), ("enemy within 8, we have more bodies", lambda x: x["foes"] > 0 and x["friends"] + 1 > x["foes"])):
            xs = [x for x in A if x["who"] == w and s2(x)]
            c = collections.Counter(x["out"] for x in xs)
            ws = [x["wait"] for x in xs if x["wait"] is not None]
            print(f"C  {w:4s} carrier (20+) reaches 8 tiles of an altar, {lab:44s}: {len(xs):5d} ({len(xs) / max(1, n):4.1f}/game) deposited {pct(c['deposited'], len(xs))} died {pct(c['died'], len(xs))} walked away {pct(c['walked away'], len(xs))} still there {pct(c['still there'], len(xs))}; rounds to deposit {st.mean(ws) if ws else 0:.0f}")
    for bagk in ("light", "bag20+"):
        for m in ("+2 or more", "+1", "level", "behind"):
            row = []
            for w in ("us", "them"):
                k = (label != "ALL", w, m, bagk)
                if label == "ALL":
                    rr = ADV[(True, w, m, bagk, "rounds")] + ADV[(False, w, m, bagk, "rounds")]
                    aa = ADV[(True, w, m, bagk, "attacks")] + ADV[(False, w, m, bagk, "attacks")]
                else:
                    rr, aa = ADV[(True, w, m, bagk, "rounds")], ADV[(True, w, m, bagk, "attacks")]
                row.append(f"{w} {pct(aa, rr)} of {rr}")
            print(f"D  attacks a champion, enemy within 6, bodies {m:10s} {bagk:6s}: " + " | ".join(row))
    T = [x for x in DTH if sel(x)]
    for w in ("us", "them"):
        xs = [x for x in T if x["who"] == w]
        print(f"E  {w:4s} deaths with 20+ gems within 10 of an altar: {len(xs)} ({len(xs) / max(1, n):.2f}/game), mean bag {st.mean(x['bag'] for x in xs) if xs else 0:.0f}; while depositing {pct(sum(x['chan'] for x in xs), len(xs))}; no teammate within 6 {pct(sum(x['friends'] == 0 for x in xs), len(xs))}; foes there {st.mean(x['foes'] for x in xs) if xs else 0:.1f}")
