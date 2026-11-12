"""F1 value model (offline): from the position at round R (both teams), predict the final margin and the win.

Usage: python tools/dz_f1_value.py [--runs N] [--out RESULTS.json]   (needs numpy, scikit-learn)
Data: stored full-pool capsules (evidence summaries). Features per team at R (us = DZ, them = opponent): banked,
carried gems, gold earned, gold spent, kills, deaths, assists, collected gems, champion damage done/taken, monster
damage taken, healing received, camp clears so far; plus R and the differences. Targets: final margin (banked -
opponent banked) and DZ win. Models: banked-difference baseline (linear), ridge on all features, gradient-boosted
trees; map-grouped 5-fold CV (a map never appears in both train and test). Permutation importance on the trees
says which parts of the position matter most (the papers' gold-rate and assist findings, checked on our data).
"""
import argparse, glob, json, os, random, sys, zipfile
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
sys.path.insert(0, str(Path(__file__).resolve().parent)); import dz

ap = argparse.ArgumentParser(); ap.add_argument('--runs', type=int, default=40); ap.add_argument('--out'); a = ap.parse_args()
ROUNDS = (100, 200, 300)
METRICS = ('gems', 'earnedGold', 'spentGold', 'kills', 'deaths', 'assists', 'collectedGems', 'championDamageDone',
           'championDamageTaken', 'monsterDamageTaken', 'healingReceived')
NAMES = ['banked'] + list(METRICS) + ['clears']
runs = sorted((p for p in glob.glob('research/dz/runs/dz-*/evidence.zip')
               if 'diag' not in p and 'smoke' not in p and 'idle' not in p and 'check' not in p),
              key=os.path.getmtime, reverse=True)
rows = []; used = 0
for path in runs:
    if used >= a.runs: break
    try:
        z = zipfile.ZipFile(path); cells = [n for n in z.namelist() if n.endswith('/summary.json') and n.startswith('games/')]
    except (zipfile.BadZipFile, OSError):
        continue  # A run still being written, or a placeholder.
    if len(cells) < 100: continue
    used += 1
    for n in cells:
        cell = n.split('/')[1]; m, side = cell.rsplit('-', 1); me = 'team' + side
        try: d = json.loads(z.read(n))
        except Exception: continue
        sub = d.get('teamTimelines', []); champ = d.get('championTimelines', [])
        final = {'us': 0.0, 'them': 0.0}
        for r in sub:
            if r['metric'] == 'submittedGems': final['us' if r['owner'] == me else 'them'] = float(r['runs'][-1]['value']) if r['runs'] else 0.0
        clears = {'us': [], 'them': []}
        for e in d['events']:
            if e['kind'] == 'campClear':
                clears['us' if e['owner'].get('team') == me else 'them'] += [x['timestamp']['round'] for x in e['entries']]
        for R in ROUNDS:
            if int(d['match']['roundsStarted']) <= R: continue
            v = {t: dict.fromkeys(NAMES, 0.0) for t in ('us', 'them')}
            for r in sub:
                if r['metric'] == 'submittedGems':
                    x = dz.sample_at(r['runs'], R); v['us' if r['owner'] == me else 'them']['banked'] = x or 0.0
            for r in champ:
                if r['metric'] in METRICS:
                    x = dz.sample_at(r['runs'], R); v['us' if r['owner']['team'] == me else 'them'][r['metric']] += x or 0.0
            for t in ('us', 'them'): v[t]['clears'] = sum(1 for c in clears[t] if c <= R)
            x = [R] + [v['us'][k] for k in NAMES] + [v['them'][k] for k in NAMES] + [v['us'][k] - v['them'][k] for k in NAMES]
            rows.append((m, R, x, final['us'] - final['them'], final['us'] > final['them']))
feat = ['R'] + [f'us_{k}' for k in NAMES] + [f'them_{k}' for k in NAMES] + [f'diff_{k}' for k in NAMES]
maps = sorted({r[0] for r in rows}); rng = random.Random(0); rng.shuffle(maps); fold = {m: i % 5 for i, m in enumerate(maps)}
res = {'samples': len(rows), 'maps': len(maps), 'runs_read': used}
for R in ROUNDS:
    S = [r for r in rows if r[1] == R]
    X = np.array([r[2] for r in S]); y = np.array([r[3] for r in S]); G = np.array([fold[r[0]] for r in S])
    base_col = feat.index('diff_banked')
    pred = {k: np.zeros(len(y)) for k in ('baseline', 'ridge', 'trees')}
    for k in range(5):
        tr, te = G != k, G == k
        pred['baseline'][te] = Ridge(1.0).fit(X[tr][:, [base_col]], y[tr]).predict(X[te][:, [base_col]])
        pred['ridge'][te] = Ridge(10.0).fit(X[tr], y[tr]).predict(X[te])
        pred['trees'][te] = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_leaf_nodes=31).fit(X[tr], y[tr]).predict(X[te])
    out = {}
    for k, p in pred.items():
        out[k] = dict(mae=round(float(np.mean(np.abs(p - y))), 1), r2=round(float(1 - np.mean((p - y) ** 2) / np.var(y)), 3),
                      win_sign_acc=round(float(np.mean((p > 0) == (y > 0))), 3))
    model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_leaf_nodes=31).fit(X, y)
    imp = permutation_importance(model, X, y, n_repeats=3, random_state=0)
    top = sorted(zip(feat, imp.importances_mean), key=lambda t: -t[1])[:12]
    out['top_features'] = [(f, round(float(v), 1)) for f, v in top]
    res[f'R{R}'] = dict(n=len(y), **out)
print(json.dumps(res, indent=1))
if a.out: Path(a.out).write_text(json.dumps(res, indent=1), encoding='utf-8')
