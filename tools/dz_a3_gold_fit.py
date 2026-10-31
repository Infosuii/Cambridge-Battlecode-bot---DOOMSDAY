"""A3 lambda_gold fit (offline). Final margin (banked - opponent banked) regressed on our R250 / R500 gold, banked,
collected and deaths, demeaned within each (map, side, opponent) cell, so the coefficients compare DZ variants on the
same cell and map difficulty drops out. Correlational (variants differ in more than gold), but it bounds the weight.

Usage: python tools/dz_a3_gold_fit.py [--out research/dz/a3-2026-11-01/RESULTS.json]   (needs numpy)
"""
import argparse, glob, json, os
from collections import defaultdict
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument('--out'); a = ap.parse_args()
rows = []
for f in glob.glob('research/dz/runs/dz-*/results.json'):
    run = os.path.basename(os.path.dirname(f))
    if 'diag' in run or 'trace' in run: continue
    try: pg = json.load(open(f)).get('per_game') or []
    except Exception: continue
    if len(pg) < 100: continue
    for g in pg:
        c = g.get('checkpoints') or {}
        try:
            p, q = c['250'], c['500']
            if p['ended_before_checkpoint'] or q['ended_before_checkpoint'] or None in (p['gold'], q['gold'], p['banked'], q['banked']): continue
        except KeyError: continue
        rows.append((run, g['map'], g['side'], g.get('opponent_sha256', ''), g['banked'] - g['opponent_banked'],
                     [p['gold'], p['banked'], p['collected'], p['deaths']], [q['gold'], q['banked'], q['collected'], q['deaths']]))
cells = defaultdict(list)
for r in rows: cells[r[1:4]].append(r)
res = dict(games=len(rows), runs=len({r[0] for r in rows}), features=['gold', 'banked', 'collected', 'deaths'])
for k, idx in (('R250', 5), ('R500', 6)):
    X, y = [], []
    for v in cells.values():
        if len(v) < 3: continue
        M = np.array([r[idx] for r in v], float); m = np.array([r[4] for r in v], float)
        X.append(M - M.mean(0)); y.append(m - m.mean())
    X, y = np.vstack(X), np.concatenate(y)
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    rng = np.random.default_rng(0)
    bs = np.array([np.linalg.lstsq(X[i], y[i], rcond=None)[0] for i in (rng.integers(0, len(y), len(y)) for _ in range(300))])
    res[k] = dict(coef=[float(x) for x in coef], gold_ci95=[float(x) for x in np.percentile(bs[:, 0], [2.5, 97.5])],
                  gems_per_gold=float(coef[0] / coef[1]))
print(json.dumps(res, indent=1))
if a.out: open(a.out, 'w').write(json.dumps(res, indent=1))
