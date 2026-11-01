"""Geometric config selector (C3 priority 7; makes per-map plans transfer to unseen maps, so G6 can judge them).

Usage: python tools/dz_geo_select.py --configs SPEC.json --features RUN [--ridge 3] [--margin 0] [--out TABLE.inc]
                                     [--results RESULTS.json]   (needs numpy)
SPEC: a z14b/z14c spec whose runs are uniform-table screens (exact: a map replays its screened game). RUN: a trace
capsule with DZ_MAPFEAT lines (tools/dz.py smoke --trace; draft.cpp prints them). For every config, ridge-regress
the per-map margin change (config - base, summed over opponents and sides) on standardised map features. Policy:
the config with the highest predicted change if above --margin, else base. Map-grouped 5-fold CV over development
maps scores the policy on held-out maps with their played changes. --out trains on all development maps and writes
a 70-row table for every map, holdout included (its rows come from geometry only), for a G6 holdout check.
"""
import argparse, json, random, re, sys, zipfile
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dz_plan_select as sel

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument('--configs', required=True); ap.add_argument('--features', required=True)
ap.add_argument('--ridge', type=float, default=3.0); ap.add_argument('--margin', type=float, default=0.0)
ap.add_argument('--out'); ap.add_argument('--results')
a = ap.parse_args()
spec = json.loads(Path(a.configs).read_text())
opps = sorted(spec['baseline'])

feat = {}
z = zipfile.ZipFile(ROOT / 'research/dz/runs' / a.features / 'evidence.zip')
for n in z.namelist():
    if n.endswith('/candidate.stdout') and n.startswith('games/'):
        m = n.split('/')[1].rsplit('-', 1)[0]
        line = re.search(r'DZ_MAPFEAT (.*)', z.read(n).decode(errors='replace'))
        if line and m not in feat:
            kv = dict(x.split('=') for x in line.group(1).split())
            f = {k: float(v) for k, v in kv.items()}
            area = f['w'] * f['h']
            feat[m] = [area, f['walls'] / area, f['holes'] / area, f['bushes'] / area, f['altars'], f['altar_min'], f['spawn_d'],
                       f['groups'], f['big'], f['camps'], f['gems'], f['gold'], f['hp'] / max(1, f['camps']),
                       f['near_ally'] / max(1, f['groups']), f['mid'] / max(1, f['groups']), f['gems'] / max(1, f['groups'])]
NAMES = ['area', 'wall_frac', 'hole_frac', 'bush_frac', 'altars', 'altar_min', 'spawn_d', 'groups', 'big_groups', 'camps',
         'gems', 'gold', 'hp_per_camp', 'ally_half_share', 'mid_share', 'gems_per_group']
pool = sorted(p.stem for p in (ROOT / 'maps/local-benchmarks').glob('*.map26a'))
held = set(pool[4::5]); dev = [m for m in pool if m not in held]
missing = [m for m in pool if m not in feat]
if missing: raise SystemExit(f'no DZ_MAPFEAT for {missing}')

base = {o: sel.per_map(spec['baseline'][o]) for o in opps}
delta, bad = {}, {}
for name, c in spec['configs'].items():
    if any(not (ROOT / 'research/dz/runs' / c['runs'][o] / 'results.json').exists() for o in opps): continue
    runs = {o: sel.per_map(c['runs'][o]) for o in opps}
    delta[name] = {m: sum(runs[o][0][m] - base[o][0][m] for o in opps) for m in pool}
    bad[name] = {m for o in opps for m in runs[o][1]}
names = sorted(delta)
X = np.array([feat[m] for m in pool]); idx = [pool.index(m) for m in dev]
mu, sd = X[idx].mean(0), X[idx].std(0) + 1e-9  # Development maps only: the holdout never informs the scaling.
Z = {m: (np.array(feat[m]) - mu) / sd for m in pool}

def train(maps):
    models = {}
    for n in names:
        A = np.array([np.append(Z[m], 1.0) for m in maps]); y = np.array([delta[n][m] for m in maps])
        I = np.eye(A.shape[1]); I[-1, -1] = 0
        models[n] = np.linalg.solve(A.T @ A + a.ridge * I, A.T @ y)
    return models

def choose(models, m):
    pred = {n: float(np.append(Z[m], 1.0) @ w) for n, w in models.items()}
    best = max(pred, key=pred.get)
    return (best if pred[best] > a.margin else None), pred

rng = random.Random(0); order = dev[:]; rng.shuffle(order); fold = {m: i % 5 for i, m in enumerate(order)}
played, picks = {}, {}
for k in range(5):
    models = train([m for m in dev if fold[m] != k])
    for m in dev:
        if fold[m] != k: continue
        c, _ = choose(models, m)
        if c and m in bad[c]: c = None  # never assign a config with faults or fuel-outs on that map
        picks[m] = c or 'base'; played[m] = delta[c][m] if c else 0.0
cells = 2 * len(opps)
vals = np.array([played[m] / cells for m in dev])
boot = sorted(np.mean(rng.choices(list(vals), k=len(vals))) for _ in range(4000))
best_fixed = max(names, key=lambda n: sum(delta[n][m] for m in dev))
res = dict(configs=len(names), dev_maps=len(dev), features=NAMES,
           cv_margin_change_per_cell=round(float(vals.mean()), 1), ci95=[round(float(boot[100]), 1), round(float(boot[-100]), 1)],
           best_fixed=best_fixed, best_fixed_change_per_cell=round(sum(delta[best_fixed][m] for m in dev) / len(dev) / cells, 1),
           cv_picks={n: sum(1 for v in picks.values() if v == n) for n in set(picks.values())})
print(json.dumps(res, indent=1))
if a.results: Path(a.results).write_text(json.dumps(res, indent=1), encoding='utf-8')
if a.out:
    models = train(dev); sig = sel.signatures(); lines = [f'// Geometric selector (tools/dz_geo_select.py, ridge {a.ridge}, trained on development maps only).']
    for m in pool:
        c, _ = choose(models, m)
        if c and m in bad[c]: c = None
        conf = spec['configs'][c] if c else {'draft': -1, 'bits': []}
        lines.append(f"    {sel.row(sig[m], conf)}, // {m}: {c or 'base'}{' (holdout)' if m in held else ''}")
    Path(a.out).write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
