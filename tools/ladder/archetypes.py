"""Strategy archetypes of the teams that beat us (research/x3/losses48/summary_rows.json from summary_profile.py).

Each winner's game becomes a strategy vector (their side of the board, aggression, banking rhythm, farming pace,
items, utility); k-means (pure Python, k by silhouette) groups them into archetypes, each described by what sets it
apart from the other winners and from our own play in the same games. Reported per map category
(research/x3/atlas/categories.json) and per opponent.
  python tools/ladder/archetypes.py [--k 4-8] [--out research/x3/losses48]
"""
import argparse, json, math, random, statistics as st
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]


def frac(grid, phases, col):
    tot = sum(sum(grid[p]) for p in phases); return sum(grid[p][col] for p in phases) / tot if tot else 0.0


def vec(t):
    """Strategy features of one team's game."""
    dep = t['deposits']; nd300 = dep[0][0] + dep[1][0]; g300 = dep[0][1] + dep[1][1]
    s300 = {}
    for d in t['shards_by_phase'][:2]:
        for k, v in d.items(): s300[k] = s300.get(k, 0) + v
    first_fams = [f.split(' ')[0] for _, f in t['item_order'][:2]]
    cons = t['consumables']
    return {
        'clears_300': sum(sum(t['clears'][p]) for p in (0, 1)),
        'clears_enemy_early': frac(t['clears'], (0, 1), 2), 'clears_enemy_mid': frac(t['clears'], (2, 3), 2), 'clears_enemy_late': frac(t['clears'], (4,), 2),
        'clears_contested_early': frac(t['clears'], (0, 1), 1),
        'pickups_enemy': frac(t['pickups'], (0, 1, 2, 3, 4), 2),
        'kills_300': sum(sum(t['kills'][p]) for p in (0, 1)), 'kills_enemy_side': frac(t['kills'], (0, 1, 2, 3, 4), 2),
        'first_kill': (t['kills_first'][0][0] if t['kills_first'] else 2000),
        'deaths_300': sum(sum(t['deaths'][p]) for p in (0, 1)),
        'deposits_300': nd300, 'deposit_size_300': g300 / nd300 if nd300 else 0, 'first_deposit': t['first_deposit'] if t['first_deposit'] is not None else 2000,
        'deposits_total': sum(d[0] for d in dep), 'deposit_size': sum(d[1] for d in dep) / max(1, sum(d[0] for d in dep)),
        'bruiser_300': s300.get('Bruiser', 0), 'treasure_300': s300.get('Treasure', 0), 'power_300': s300.get('Power', 0),
        'shards_300': sum(s300.values()),
        'opens_treasure': float('Treasure' in first_fams), 'opens_jungle': float('Jungle' in first_fams), 'opens_bruiser': float('Bruiser' in first_fams),
        'teleports': cons.get('Teleport Crystal', [0])[0], 'locks': cons.get('Altar Lock', [0])[0], 'wards': sum(sum(p) for p in t['wards']),
        'gems_lost_300': sum(t['gems_lost'][:2]),
    }


def kmeans(X, k, seed, iters=80):
    rng = random.Random(seed); n = len(X); d2 = lambda a, b: sum((x - y) ** 2 for x, y in zip(a, b))
    C = [X[rng.randrange(n)]]
    for _ in range(1, k):
        d = [min(d2(x, c) for c in C) for x in X]; t = rng.random() * sum(d); acc = 0
        for i, v in enumerate(d):
            acc += v
            if acc >= t: C.append(X[i]); break
    for _ in range(iters):
        lab = [min(range(k), key=lambda j: d2(x, C[j])) for x in X]
        nc = [[sum(c) / len(m) for c in zip(*m)] if (m := [X[i] for i in range(n) if lab[i] == j]) else C[j] for j in range(k)]
        if all(d2(a, b) < 1e-12 for a, b in zip(nc, C)): break
        C = nc
    return lab, C, sum(d2(X[i], C[lab[i]]) for i in range(n))


def silhouette(X, lab, sample=400):
    idx = list(range(len(X)))[:sample]; d = lambda a, b: math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b))); s = []
    for i in idx:
        same = [j for j in idx if lab[j] == lab[i] and j != i]
        if not same: s.append(0); continue
        a = sum(d(X[i], X[j]) for j in same) / len(same)
        b = min(sum(d(X[i], X[j]) for j in idx if lab[j] == c) / max(1, sum(1 for j in idx if lab[j] == c)) for c in set(lab) if c != lab[i])
        s.append((b - a) / max(a, b))
    return sum(s) / len(s)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--k', default='4-8'); ap.add_argument('--out', default='research/x3/losses48')
    a = ap.parse_args()
    rows = json.loads((ROOT / 'research/x3/losses48/summary_rows.json').read_text(encoding='utf-8'))
    cats = json.loads((ROOT / 'research/x3/atlas/categories.json').read_text())
    for r in rows: r['cat'] = cats.get(r['map'].replace('_', '-'), '?')
    V = [vec(r['them']) for r in rows]; U = [vec(r['us']) for r in rows]
    names = list(V[0])
    mu = [st.mean(v[n] for v in V) for n in names]; sd = [st.pstdev([v[n] for v in V]) + 1e-9 for n in names]
    X = [[(v[n] - m) / s for n, m, s in zip(names, mu, sd)] for v in V]
    lo, hi = map(int, a.k.split('-')); best = None
    for k in range(lo, hi + 1):
        cand = min((kmeans(X, k, s) for s in range(8)), key=lambda t: t[2]); sil = silhouette(X, cand[0])
        print(f'k={k} silhouette {sil:.3f}', flush=True)
        if best is None or sil > best[0]: best = (sil, k, cand)
    sil, k, (lab, C, _) = best
    lines = ['# Strategy archetypes of the teams that beat us (last 48 h, teams rated >= 2000)', '',
             f'{len(rows)} distinct losses, {len(set(r["opponent"] for r in rows))} opponents, {len(set(r["map"] for r in rows))} maps. '
             f'k-means on {len(names)} strategy features chose k={k} (silhouette {sil:.3f}). For each archetype: the features '
             'that set it apart (z-score vs all winners), its values next to ours in the same games, where it beats us and who uses it.', '']
    arche = []
    for j in range(k):
        idx = [i for i in range(len(rows)) if lab[i] == j]
        if not idx: continue
        z = {n: C[j][q] for q, n in enumerate(names)}
        top = sorted(names, key=lambda n: -abs(z[n]))[:7]
        mt = {n: st.mean(V[i][n] for i in idx) for n in names}; mu_ = {n: st.mean(U[i][n] for i in idx) for n in names}
        cats_c = Counter(rows[i]['cat'] for i in idx); opp_c = Counter(rows[i]['opponent'] for i in idx); maps_c = Counter(rows[i]['map'] for i in idx)
        champs = Counter(c for i in idx for c in rows[i]['their_names'])
        arche.append(dict(id=f'A{j + 1}', n=len(idx), top=top, them=mt, us=mu_, cats=cats_c.most_common(), opps=opp_c.most_common(8), maps=maps_c.most_common(10)))
        lines += [f'## A{j + 1}: {len(idx)} losses', '', '| feature | z | them | us (same games) |', '|---|---|---|---|']
        lines += [f'| {n} | {z[n]:+.2f} | {mt[n]:.2f} | {mu_[n]:.2f} |' for n in top]
        lines += ['', 'Categories: ' + ', '.join(f'{c} {v}' for c, v in cats_c.most_common()),
                  'Opponents: ' + ', '.join(f'{o} {v}' for o, v in opp_c.most_common(8)),
                  'Maps: ' + ', '.join(f'{m} {v}' for m, v in maps_c.most_common(10)),
                  'Their champions: ' + ', '.join(f'{c} {v}' for c, v in champs.most_common(8)), '']
    # per category: winners vs us, all features
    lines += ['## Winners vs us by map category (means over losses)', '']
    for c in sorted(set(r['cat'] for r in rows)):
        idx = [i for i, r in enumerate(rows) if r['cat'] == c]
        lines += [f'### {c}: {len(idx)} losses', '', '| feature | them | us |', '|---|---|---|']
        lines += [f'| {n} | {st.mean(V[i][n] for i in idx):.2f} | {st.mean(U[i][n] for i in idx):.2f} |' for n in names]
        lines += ['']
    out = ROOT / a.out
    (out / 'ARCHETYPES.md').write_text('\n'.join(lines), encoding='utf-8')
    (out / 'archetypes.json').write_text(json.dumps(dict(k=k, silhouette=sil, archetypes=arche, labels={rows[i]['matchId']: f'A{lab[i] + 1}' for i in range(len(rows))}), ensure_ascii=False, indent=1), encoding='utf-8')
    for x in arche: print(x['id'], x['n'], ', '.join(f"{n} {x['them'][n]:.2f} (us {x['us'][n]:.2f})" for n in x['top'][:5]))


if __name__ == '__main__':
    main()
