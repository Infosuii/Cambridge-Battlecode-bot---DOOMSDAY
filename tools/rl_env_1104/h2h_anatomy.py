"""Side-by-side anatomy of decoded games (dump.mjs JSON) against one opponent: per game and per team, by phase:
banked gems, gems picked up, deaths and bags lost, attacks by target (camp type / champion), crew sizes on monster
camps, shops and items, wards, locks, recalls, positions (own half, near altars, spread), idle turns.
usage: h2h_anatomy.py US_TEAM(0|1) DUMP.json [DUMP.json ...]"""
import collections, itertools, json, os, statistics as st, sys

sys.stdout.reconfigure(encoding="utf-8")
US = int(sys.argv[1])
NAMES = ["ryth", "vesper", "vendetta", "cassi", "issac", "stellar", "prism", "marcella", "willow", "ren", "varg", "tavi", "HoR"]
FAM = ["monster", "power", "durability", "treasure", "jungle", "home", "bruiser", "tribute", "capture", "prospector", "hunter", "skirmish", "greed", "collectors"]
STAT = ["S", "S*", "F", "F*", "H", "H*"]
cheb = lambda p, q: max(abs(p[0] - q[0]), abs(p[1] - q[1]))
PH = [(0, 150), (150, 300), (300, 500), (500, 800), (800, 9999)]
ph = lambda r: next(i for i, (a, b) in enumerate(PH) if a <= r < b)
camp_kind = lambda hp: {120: "cluster", 1350: "wolf", 2400: "elk", 5000: "golem", 20000: "mono"}.get(int(hp), str(int(hp)))

for path in sys.argv[2:]:
    d = json.load(open(path, encoding="utf-8"))
    fr = {f[0]: {u[0]: u for u in f[1]} for f in d["frames"]}
    R = sorted(fr)
    steps = d["steps"]
    team = {i: u[1] for i, u in fr[R[0]].items()}
    typ = {i: u[2] for i, u in fr[R[0]].items()}
    camps = {(c[1], c[2]): camp_kind(c[3]) for c in d["camps0"]}
    spawn = {t: [(u[3], u[4]) for u in fr[R[0]].values() if u[1] == t and u[3] is not None] for t in (0, 1)}
    cen = {t: (st.mean(x for x, _ in v), st.mean(y for _, y in v)) for t, v in spawn.items()}
    altars = sorted({(s[5], s[6]) for s in steps if s[1] == "Submit gems"})
    print(f"\n######## {os.path.basename(path)[:13]}  rounds {R[-1]}  altars {altars}")
    for t in (US, 1 - US):
        tag = "US  " if t == US else "THEM"
        ids = [i for i in team if team[i] == t]
        banked = [0] * 5; picked = [0] * 5; deaths = [0] * 5; lost = [0] * 5; idle = [0] * 5; alive_r = [0] * 5
        own_half = [0] * 5; near_alt = [0] * 5; spread = [[] for _ in PH]
        bank_events = []
        prev = fr[R[0]]
        sub_round = collections.defaultdict(set)
        for s in steps:
            if s[1] == "Gems submitted":
                sub_round[s[0]].add(s[2])
        for r in R[1:]:
            cur = fr[r]; k = ph(r)
            ps = []
            for i in ids:
                u, p = cur.get(i), prev.get(i)
                if not u or not p:
                    continue
                dg = (u[7] or 0) - (p[7] or 0)
                if p[6] and not u[6]:
                    deaths[k] += 1; lost[k] += p[7] or 0
                elif dg > 0:
                    picked[k] += dg
                elif dg < 0 and (i in sub_round.get(r, ()) or i in sub_round.get(r - 1, ())):
                    banked[k] += -dg; bank_events.append((r, -dg))
                if u[6] and u[3] is not None:
                    alive_r[k] += 1
                    pos = (u[3], u[4]); ps.append(pos)
                    if p[3] == u[3] and p[4] == u[4]:
                        idle[k] += 1
                    if cheb(pos, cen[t]) <= cheb(pos, cen[1 - t]):
                        own_half[k] += 1
                    if altars and min(cheb(pos, a) for a in altars) <= 5:
                        near_alt[k] += 1
            if len(ps) >= 2:
                spread[k].append(st.mean(cheb(a, b) for a, b in itertools.combinations(ps, 2)))
            prev = cur
        atk = [collections.Counter() for _ in PH]
        crew = collections.defaultdict(set)  # (camp pos, round // 8) -> attackers
        cnt = collections.Counter()
        for s in steps:
            if team.get(s[2]) != t:
                continue
            r, kind = s[0], s[1]
            cnt[kind] += 1
            if kind in ("Attack", "Cast ability") and s[5] is not None:
                tgt = (s[5], s[6])
                ck = camps.get(tgt)
                if ck is None:
                    f = fr.get(r) or {}
                    ck = "champ" if any(u[1] != t and u[3] == tgt[0] and u[4] == tgt[1] for u in f.values()) else "other"
                atk[ph(r)][ck] += 1
                if ck in ("wolf", "elk", "golem", "mono"):
                    crew[(tgt, r // 8, ck)].add(s[2])
        crew_sz = collections.defaultdict(list)
        for (tgt, w, ck), a in crew.items():
            crew_sz[ck].append(len(a))
        final = fr[R[-1]]
        items = collections.Counter()
        for it in d["items"]:
            if it[1] != t:
                continue
            for idx, n in enumerate(it[3]):
                if n:
                    items[FAM[idx // 6] + "-" + STAT[idx % 6]] += n
        lineup = " ".join(NAMES[typ[i]] for i in ids)
        print(f"{tag} [{lineup}]  banked total {sum(banked)} in {len(bank_events)} deposits (mean {sum(banked) / max(1, len(bank_events)):.0f}); first deposit r{bank_events[0][0] if bank_events else '-'}")
        print(f"   by phase {[f'{a}-{b}' for a, b in PH]}")
        print(f"   banked {banked}  picked {picked}  deaths {deaths}  bags lost {lost}")
        print(f"   idle % {[round(100 * idle[k] / max(1, alive_r[k])) for k in range(5)]}  own-half % {[round(100 * own_half[k] / max(1, alive_r[k])) for k in range(5)]}  near-altar % {[round(100 * near_alt[k] / max(1, alive_r[k])) for k in range(5)]}  spread {[round(st.mean(x), 1) if x else 0 for x in spread]}")
        print("   attacks " + " | ".join(str(dict(a.most_common(6))) for a in atk))
        print("   crew size on " + ", ".join(f"{ck}: {st.mean(v):.2f} (solo {100 * sum(x == 1 for x in v) // len(v)}%)" for ck, v in crew_sz.items()))
        print(f"   shops {cnt['Shop']} wards {cnt['Place ward']} locks {cnt['Place altar lock']} recalls {cnt['Recall']} cancels {cnt['Cancel channel']} tp {cnt['Teleport complete']} blocked {cnt['Movement blocked']}; end gold {sum((final[i][8] or 0) for i in ids)} unbanked {sum((final[i][7] or 0) for i in ids)}")
        print("   items " + ", ".join(f"{k} x{v}" for k, v in items.most_common(12)))
