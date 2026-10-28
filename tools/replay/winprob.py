"""Game-separated, game-weighted symmetric logistic model; no held-out trajectories."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from deep_preflight import ROOT

STUDY = ROOT / 'research/deep-2026-10-28'
NAMES = ['banked_500', 'carried_100', 'equipment_1000', 'alive', 'health_1000',
         'income50_50', 'middle_income50_50', 'vision', 'banked_x_progress', 'equipment_x_progress']


def features(game):
    rows = game['rows']
    rounds = np.array([r['r'] for r in rows])
    x = []
    for i, row in enumerate(rows):
        a, b = row['teams']
        old = rows[max(0, int(np.searchsorted(rounds, row['r'] - 50, side='right')) - 1)]['teams']
        diff = lambda name: a[name] - b[name]
        income = diff('collected') - (old[0]['collected'] - old[1]['collected'])
        middle = diff('middle_gems') - (old[0]['middle_gems'] - old[1]['middle_gems'])
        bank, gear = diff('banked') / 500, diff('equipment_cost') / 1000
        progress = row['r'] / game['max_rounds']
        x.append([bank, diff('carried') / 100, gear, diff('alive'), diff('health') / 1000,
                  income / 50, middle / 50, diff('vision_fraction'), bank * progress, gear * progress])
    return np.array(x, dtype=float)


def sigmoid(z):
    return np.exp(-np.logaddexp(0, -np.clip(z, -700, 700)))


def fit(x, y, w, penalty):
    beta = np.zeros(x.shape[1])
    w = w / w.sum()
    objective = lambda b: float(np.sum(w * (np.logaddexp(0, x @ b) - y * (x @ b))) + penalty / 2 * (b @ b))
    for _ in range(60):
        p = sigmoid(x @ beta)
        grad = x.T @ (w * (p - y)) + penalty * beta
        hess = x.T @ ((w * p * (1 - p))[:, None] * x) + penalty * np.eye(x.shape[1])
        step = np.linalg.solve(hess, grad)
        rate, old = 1., objective(beta)
        while rate > 1e-7 and objective(beta - rate * step) > old:
            rate /= 2
        beta -= rate * step
        if np.max(np.abs(rate * step)) < 1e-7:
            break
    return beta


def metrics(y, logits, w):
    w = w / w.sum()
    p = sigmoid(logits)
    bins = []
    assignments = np.minimum(9, (p * 10).astype(int))
    for index in range(10):
        lo = index / 10
        mask = assignments == index
        mass = float(w[mask].sum())
        bins.append({'lo': round(float(lo), 1), 'weight': mass, 'snapshots': int(mask.sum()),
                     'predicted': float(np.average(p[mask], weights=w[mask])) if mass else None,
                     'observed': float(np.average(y[mask], weights=w[mask])) if mass else None})
    return {'log_loss': float(np.sum(w * (np.logaddexp(0, logits) - y * logits))),
            'brier': float(np.sum(w * (p - y) ** 2)), 'bins': bins,
            'ece10': sum(b['weight'] * abs(b['predicted'] - b['observed']) for b in bins if b['weight'])}


def temperature(logits, y, w):
    # Convex in positive inverse temperature; calibration set only, no test access.
    lo, hi = .05, 20.
    for _ in range(70):
        mid = (lo + hi) / 2
        derivative = np.sum(w * logits * (sigmoid(logits * mid) - y))
        if derivative > 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', type=Path, required=True)
    args = ap.parse_args()
    run = json.loads((args.run / 'run.json').read_text(encoding='utf-8'))
    assert run['partition'] == 'examined' and run['passed'] == 385 and not run['failed']
    split_file = STUDY / 'MODEL_SPLIT.json'
    splits = {r['match_id']: r for r in json.loads(split_file.read_text(encoding='utf-8'))['rows']}
    games, parts = {}, {s: [] for s in ('train', 'calibration', 'test')}
    for mid, spec in splits.items():
        g = json.loads((args.run / (mid + '.json')).read_text(encoding='utf-8'))
        assert g['partition'] == 'examined' and g['code_sha256'] == run['code_sha256']
        xx = features(g)
        keep = np.array([not r['terminal'] for r in g['rows']])
        n = int(keep.sum())
        y = float(g['outcome'] == 'teamA')
        assert y == spec['team_a_won']
        parts[spec['split']].append((xx[keep], np.full(n, y), np.full(n, 1 / n),
                                     np.array([r['r'] for r in g['rows']])[keep], np.full(n, mid)))
        games[mid] = g
    data = {s: tuple(np.concatenate([r[i] for r in rows]) for i in range(5)) for s, rows in parts.items()}
    tx, ty, tw, _, _ = data['train']
    cx, cy, cw, _, _ = data['calibration']
    candidates = []
    for lam in (.01, .1, 1., 10.):
        beta = fit(tx, ty, tw, lam)
        score = metrics(cy, cx @ beta, cw)
        candidates.append({'lambda': lam, 'calibration_log_loss': score['log_loss'], 'beta': beta.tolist()})
    chosen = min(candidates, key=lambda r: r['calibration_log_loss'])
    beta = np.array(chosen['beta'])
    invtemp = temperature(cx @ beta, cy, cw)
    baseline_beta = fit(tx[:, :1], ty, tw, .01)
    baseline_temp = temperature(cx[:, :1] @ baseline_beta, cy, cw)
    results = {}
    for s, (x, y, w, rounds, mids) in data.items():
        z = x @ beta * invtemp
        results[s] = {'games': len(parts[s]), 'snapshots': len(y), 'model': metrics(y, z, w),
                      'constant_half': metrics(y, np.zeros(len(y)), w),
                      'bank_only': metrics(y, x[:, :1] @ baseline_beta * baseline_temp, w), 'round_slices': {}}
        for name, mask in [('0_100', rounds <= 100), ('101_250', (rounds > 100) & (rounds <= 250)),
                           ('251_500', (rounds > 250) & (rounds <= 500)), ('501_plus', rounds > 500)]:
            if not mask.any():
                continue
            # Reweight each represented game equally within a slice.
            unique, counts = np.unique(mids[mask], return_counts=True)
            count_map = dict(zip(unique, counts))
            sw = np.array([1 / count_map[m] for m in mids[mask]])
            results[s]['round_slices'][name] = {'games': len(unique), 'snapshots': int(mask.sum()),
                'model': metrics(y[mask], z[mask], sw), 'bank_only': metrics(y[mask], (x[:, :1] @ baseline_beta * baseline_temp)[mask], sw)}
    # Internal test uncertainty: resample complete games, never individual snapshots.
    x, y, w, rounds, mids = data['test']
    z = x @ beta * invtemp
    zbank = x[:, :1] @ baseline_beta * baseline_temp
    bygame = []
    for mid in np.unique(mids):
        m = mids == mid
        bygame.append([metrics(y[m], z[m], w[m])['log_loss'], metrics(y[m], zbank[m], w[m])['log_loss']])
    a = np.array(bygame)
    boot = np.random.default_rng(20261028).integers(0, len(a), size=(2000, len(a)))
    draws = (a[:, 0] - a[:, 1])[boot].mean(axis=1)
    result = {'version': 'deep-logistic-v1', 'evidence': 'predictive association, not causal',
              'timeline_code_sha256': run['code_sha256'], 'schema_sha256': run['schema_sha256'],
              'split_sha256': hashlib.sha256(split_file.read_bytes()).hexdigest(), 'hands_off_used': 0,
              'feature_names': NAMES, 'intercept': 0, 'candidates': candidates, 'chosen_lambda': chosen['lambda'],
              'inverse_temperature': invtemp, 'coefficients': dict(zip(NAMES, (beta * invtemp).tolist())),
              'weighting': 'equal total weight per game; terminal rows excluded', 'metrics': results,
              'test_model_minus_bank_logloss_game_bootstrap95': np.quantile(draws, [.025, .975]).tolist(),
              'limits': ['Internal random split shares maps/opponents across folds; not an unseen-map estimate.',
                         'Temperature and lambda use the same calibration games.',
                         'Last-50 income uses the last retained row at or before r-50; up to four rounds extra after r300.',
                         'A probability change is not avoidable regret or causal event credit.']}
    (STUDY / 'WINPROB_MODEL.json').write_bytes((json.dumps(result, indent=2) + '\n').encode())
    pred_dir = args.run / 'predictions'
    pred_dir.mkdir(exist_ok=True)
    for mid, g in games.items():
        p = sigmoid(features(g) @ beta * invtemp)
        payload = {'match_id': mid, 'split': splits[mid]['split'], 'rows': [{'r': r['r'], 'p_team_a': float(v)} for r, v in zip(g['rows'], p)]}
        (pred_dir / (mid + '.json')).write_bytes((json.dumps(payload) + '\n').encode())
    print(json.dumps({'lambda': chosen['lambda'], 'inverse_temperature': invtemp,
                      'test': {k: v for k, v in results['test']['model'].items() if k != 'bins'},
                      'bank_only_logloss': results['test']['bank_only']['log_loss'], 'ci': result['test_model_minus_bank_logloss_game_bootstrap95']}))


if __name__ == '__main__':
    main()
