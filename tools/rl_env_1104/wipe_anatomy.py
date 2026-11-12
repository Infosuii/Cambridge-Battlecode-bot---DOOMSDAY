"""Anatomy of team wipes in decoded ladder games (ladder_decode.py dumps): a wipe is 3+ deaths of one team within
WINDOW rounds. Per wipe: round, local numbers at the first death (alive champions of each team within 8 tiles of it),
each team's spread beforehand (mean pairwise Chebyshev distance 10 rounds before), whether the dead walked in (more
than 8 tiles from the first death when it happened, dying later = trickling into a lost fight), the side of the map,
gems lost, and the trade (the other team's deaths in the same window).
usage: wipe_anatomy.py --cache artifacts/tmp/ladder_1110 --versions v139 v140 [--window 15]"""
import argparse, collections, itertools, json, os, statistics as st, sys

ap = argparse.ArgumentParser()
ap.add_argument("--cache", required=True)
ap.add_argument("--versions", nargs="+", required=True)
ap.add_argument("--window", type=int, default=15)
a = ap.parse_args()
sys.stdout.reconfigure(encoding="utf-8")
matches = json.load(open(os.path.join(a.cache, "matches.json"), encoding="utf-8"))
cheb = lambda p, q: max(abs(p[0] - q[0]), abs(p[1] - q[1]))


def spread(units):
    ps = [(u[3], u[4]) for u in units if u[6] and u[3] is not None]
    if len(ps) < 2:
        return 0.0
    return st.mean(cheb(p, q) for p, q in itertools.combinations(ps, 2))


rows = []
games = 0
for mt in matches:
    if mt.get("version") not in a.versions:
        continue
    p = os.path.join(a.cache, "dumps", mt["matchId"] + ".json")
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding="utf-8"))
    games += 1
    us = 0 if mt["us"].get("side", "a") == "a" else 1
    fr = d["frames"]
    by_round = {f[0]: f[1] for f in fr}
    rounds = sorted(by_round)
    spawn = {}
    for u in by_round[rounds[0]]:
        if u[3] is not None:
            spawn.setdefault(u[1], []).append((u[3], u[4]))
    cen = {t: (st.mean(x for x, _ in v), st.mean(y for _, y in v)) for t, v in spawn.items()}
    deaths = []  # (round, team, id, pos, gems)
    prev = {u[0]: u for u in by_round[rounds[0]]}
    for r in rounds[1:]:
        cur = {u[0]: u for u in by_round[r]}
        for uid, u in cur.items():
            pu = prev.get(uid)
            if pu and pu[6] and not u[6] and pu[3] is not None:
                deaths.append((r, u[1], uid, (pu[3], pu[4]), pu[7] or 0))
        prev = cur
    for team in (0, 1):
        ds = [x for x in deaths if x[1] == team]
        i = 0
        while i < len(ds):
            j = i
            while j + 1 < len(ds) and ds[j + 1][0] - ds[i][0] <= a.window:
                j += 1
            if j - i + 1 >= 3:
                w = ds[i:j + 1]
                r0, p0 = w[0][0], w[0][3]
                before = by_round.get(max(rounds[0], r0 - 1), [])
                early = by_round.get(max(rounds[0], r0 - 10), [])
                mine = [u for u in before if u[1] == team and u[6] and u[3] is not None]
                theirs = [u for u in before if u[1] != team and u[6] and u[3] is not None]
                n_mine = sum(cheb((u[3], u[4]), p0) <= 8 for u in mine)
                n_theirs = sum(cheb((u[3], u[4]), p0) <= 8 for u in theirs)
                dead_ids = {x[2] for x in w}
                walked_in = sum(1 for u in mine if u[0] in dead_ids and u[0] != w[0][2] and cheb((u[3], u[4]), p0) > 8)
                other_deaths = sum(1 for x in deaths if x[1] != team and r0 - 2 <= x[0] <= w[-1][0] + 2)
                own_c, opp_c = cen.get(team), cen.get(1 - team)
                side = "own" if own_c and opp_c and cheb(p0, own_c) < cheb(p0, opp_c) else "enemy"
                rows.append(dict(who="us" if team == us else "them", result=mt["us"].get("result"), map=mt.get("map"),
                                 version=mt["version"], round=r0, deaths=len(w), dur=w[-1][0] - r0, near_mine=n_mine,
                                 near_theirs=n_theirs, alive_mine=len(mine), alive_theirs=len(theirs),
                                 spread_mine=spread([u for u in early if u[1] == team]),
                                 spread_theirs=spread([u for u in early if u[1] != team]), walked_in=walked_in,
                                 traded=other_deaths, side=side, gems=sum(x[4] for x in w)))
                i = j + 1
            else:
                i += 1
print(f"{games} games ({collections.Counter(m['us'].get('result') for m in matches if m.get('version') in a.versions)})")
for who in ("us", "them"):
    W = [r for r in rows if r["who"] == who]
    if not W:
        continue
    print(f"\n== wipes suffered by {who}: {len(W)} ({len(W) / max(games, 1):.2f} per game; in our losses "
          f"{sum(r['result'] == 'loss' for r in W)}, wins {sum(r['result'] == 'win' for r in W)})")
    print(f"  round: median {st.median(r['round'] for r in W):.0f}; by phase " +
          str(collections.Counter('0-199' if r['round'] < 200 else '200-499' if r['round'] < 500 else '500-999' if r['round'] < 1000 else '1000+' for r in W)))
    print(f"  local numbers at first death (within 8): victims {st.mean(r['near_mine'] for r in W):.2f} vs killers {st.mean(r['near_theirs'] for r in W):.2f}; "
          f"outnumbered {sum(r['near_theirs'] > r['near_mine'] for r in W)}/{len(W)}")
    print(f"  alive teams then: victims {st.mean(r['alive_mine'] for r in W):.2f} vs killers {st.mean(r['alive_theirs'] for r in W):.2f}")
    print(f"  spread 10 rounds before: victims {st.mean(r['spread_mine'] for r in W):.1f} vs killers {st.mean(r['spread_theirs'] for r in W):.1f} tiles")
    print(f"  dead who walked in from >8 tiles: {st.mean(r['walked_in'] for r in W):.2f} per wipe; duration {st.mean(r['dur'] for r in W):.1f} rounds")
    print(f"  traded (killers' deaths in the window): {st.mean(r['traded'] for r in W):.2f}; on the victims' own side "
          f"{sum(r['side'] == 'own' for r in W)}/{len(W)}; gems lost {st.mean(r['gems'] for r in W):.1f}")
json.dump(rows, open(os.path.join(a.cache, "wipes_" + "_".join(a.versions) + ".json"), "w"), indent=0)
