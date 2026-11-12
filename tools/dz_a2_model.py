"""A2 learned plan switch (offline). From the DZ branch screens (dz-a2-<plan>-r<R>-<opp>-01 vs dz-a2-base-<opp>-01),
learn which team plan to switch to at round R from the position at R, independent of map identity.

Features at R from the baseline game summary (both teams): banked, carried gems, gold earned, kills, deaths,
gems collected, plus R. Per (R, plan): ridge regression of the margin change (branch - base) on the features.
Policy at R: the plan with the highest predicted change if it is > 0, else stay. Map-grouped 5-fold CV: the policy
value is the played change of the chosen branch on held-out maps (exact, branches are counterfactuals). Bootstrap
over maps for the interval. Usage: python tools/dz_a2_model.py [--out RESULTS.json]   (needs numpy)
"""
import argparse, json, os, random, sys, zipfile
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent)); import dz

ROUNDS, PLANS = (100, 250, 500), ('home', 'fight', 'turtle', 'hoard')
ap = argparse.ArgumentParser(); ap.add_argument('--out'); ap.add_argument('--ridge', type=float, default=10.0); a = ap.parse_args()
RUNS = Path('research/dz/runs')

def margins(run):
    f = RUNS / run / 'results.json'
    if not f.exists(): return None
    return {(g['map'], g['side']): g['banked'] - g['opponent_banked'] for g in json.load(open(f))['per_game']}

def features(run):
    out = {}
    z = zipfile.ZipFile(RUNS / run / 'evidence.zip')
    for n in z.namelist():
        if not n.endswith('/summary.json') or not n.startswith('games/'): continue
        cell = n.split('/')[1]; m, side = cell.rsplit('-', 1)
        d = json.loads(z.read(n)); me = 'team' + side
        vec = {}
        for R in ROUNDS:
            v = {t: dict(banked=0., carried=0., gold=0., kills=0., deaths=0., collected=0.) for t in ('us', 'them')}
            for row in d.get('teamTimelines', []):
                if row['metric'] == 'submittedGems':
                    x = dz.sample_at(row['runs'], R); t = 'us' if row['owner'] == me else 'them'
                    if x is not None: v[t]['banked'] = x
            for row in d.get('championTimelines', []):
                key = {'gems': 'carried', 'earnedGold': 'gold', 'kills': 'kills', 'deaths': 'deaths', 'collectedGems': 'collected'}.get(row['metric'])
                if not key: continue
                x = dz.sample_at(row['runs'], R); t = 'us' if row['owner']['team'] == me else 'them'
                if x is not None: v[t][key] += x
            ended = int(d['match']['roundsStarted']) <= R
            vec[R] = None if ended else [v[t][k] for t in ('us', 'them') for k in ('banked', 'carried', 'gold', 'kills', 'deaths', 'collected')]
        out[(m, side)] = vec
    return out

rows = []  # (opp, map, side, R, x, {plan: delta})
for opp in ('v76', 'v65'):
    base = margins(f'dz-a2-base-{opp}-01'); feat = features(f'dz-a2-base-{opp}-01')
    br = {(R, p): margins(f'dz-a2-{p}-r{R}-{opp}-01') for R in ROUNDS for p in PLANS}
    for c in base:
        for R in ROUNDS:
            x = feat[c][R]
            if x is None: continue
            d = {p: br[(R, p)][c] - base[c] for p in PLANS if br[(R, p)]}
            if d: rows.append((opp, c[0], c[1], R, x, d))
maps = sorted({r[1] for r in rows}); rng = random.Random(0); rng.shuffle(maps); fold = {m: i % 5 for i, m in enumerate(maps)}

def fit(tr, R, p):
    X = np.array([r[4] + [1.0] for r in tr if r[3] == R and p in r[5]]); y = np.array([r[5][p] for r in tr if r[3] == R and p in r[5]])
    if len(y) < 10: return None
    mu, sd = X[:, :-1].mean(0), X[:, :-1].std(0) + 1e-6
    Z = np.hstack([(X[:, :-1] - mu) / sd, X[:, -1:]]); I = np.eye(Z.shape[1]); I[-1, -1] = 0
    w = np.linalg.solve(Z.T @ Z + a.ridge * I, Z.T @ y)
    return mu, sd, w

def predict(model, x):
    mu, sd, w = model; return float(np.append((np.array(x) - mu) / sd, 1.0) @ w)

res = {'samples': len(rows), 'maps': len(maps)}
for R in ROUNDS:
    played = {}  # map -> list of chosen deltas (0 = stay)
    chosen = {p: 0 for p in PLANS}; chosen['stay'] = 0
    for k in range(5):
        tr = [r for r in rows if fold[r[1]] != k]; te = [r for r in rows if fold[r[1]] == k and r[3] == R]
        models = {p: fit(tr, R, p) for p in PLANS}
        for r in te:
            preds = {p: predict(models[p], r[4]) for p in PLANS if models[p] and p in r[5]}
            best = max(preds, key=preds.get) if preds else None
            if best and preds[best] > 0: played.setdefault(r[1], []).append(r[5][best]); chosen[best] += 1
            else: played.setdefault(r[1], []).append(0.0); chosen['stay'] += 1
    vals = [x for v in played.values() for x in v]; mean = float(np.mean(vals))
    boots = []
    for _ in range(2000):
        pick = [maps[rng.randrange(len(maps))] for _ in maps]
        xs = [x for m in pick for x in played.get(m, [])]
        if xs: boots.append(np.mean(xs))
    boots.sort()
    best_fixed = max(PLANS, key=lambda p: np.mean([r[5].get(p, 0) for r in rows if r[3] == R]))
    res[f'R{R}'] = dict(cv_policy_margin_change=round(mean, 2), ci95=[round(float(boots[50]), 2), round(float(boots[-50]), 2)],
                        chosen=chosen, best_fixed=best_fixed,
                        best_fixed_change=round(float(np.mean([r[5].get(best_fixed, 0) for r in rows if r[3] == R])), 2))
print(json.dumps(res, indent=1))
if a.out: open(a.out, 'w').write(json.dumps(res, indent=1))
