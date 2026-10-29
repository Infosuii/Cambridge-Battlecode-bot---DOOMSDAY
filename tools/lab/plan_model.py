"""Learn when to switch team plan, from branch-farm rows (tools/lab/branch_farm.py).

Usage: python tools/lab/plan_model.py ROWS.jsonl [ROWS.jsonl ...] [--out artifacts/evaluations/plan_model.json]

A group is (seed, opponent, map, side). Its baseline row carries the position at each branch round ('feat'); its branch
rows give the result of switching to plan p at round R and keeping it. Plan 0 at R is the baseline itself. For each round
R and plan p a logistic model predicts the win from the position at R. A policy switches at the first round where some
plan's predicted win beats staying by a margin. It is scored by map-grouped cross-validation, using only played results:
the value of a (group, R) decision is the played result of the chosen plan, otherwise the baseline. Prints the policy's
overall win rate next to the baseline's, the oracle (best played plan) and every fixed plan, with map-clustered intervals.
"""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

FEAT = ('submittedGems', 'gems', 'gold', 'kills', 'deaths', 'collectedGems', 'earnedGold', 'championDamageDone')
PLANS = (0, 1, 2, 3, 4, 5)


def load(paths):
    base, branch = {}, defaultdict(dict)
    for path in paths:
        for line in Path(path).read_text(encoding='utf-8').splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            g = (r['seed'], r['opp'], r['map'], r['side'])
            if r['round'] < 0:
                if 'feat' in r:
                    base[g] = r
            elif 'win' in r:
                branch[g][(r['round'], r['plan'])] = r['win']
            elif 'skipped' in r:
                branch[g][(r['round'], r['plan'])] = None  # game already over: the baseline result stands
    return base, branch


def x_of(f, rd):
    """Position features: our and their values, plus leads (ours minus theirs) and the round."""
    n = len(FEAT)
    us, them = np.array(f[:n], float), np.array(f[n:], float)
    bank = us[0] + us[1] - them[0] - them[1]  # submitted + carried gems
    return np.concatenate([[rd / 1000.0, bank / 100.0], (us - them) / np.array([100, 100, 100, 1, 1, 100, 1000, 10000]),
                           us / np.array([100, 100, 100, 1, 1, 100, 1000, 10000])])


def table(base, branch, rounds):
    """rows: (group, R, x, {plan: win}) for every group and round with a baseline position."""
    out = []
    for g, b in base.items():
        for rd in rounds:
            f = b['feat'].get(str(rd))
            if f is None or rd >= b['rounds']:
                continue
            res = {0: b['win']}
            for p in PLANS[1:]:
                w = branch.get(g, {}).get((rd, p), 'missing')
                if w is None:
                    res[p] = b['win']
                elif w != 'missing':
                    res[p] = w
            out.append((g, rd, x_of(f, rd), res))
    return out


def fit(rows, rounds):
    models = {}
    for rd in rounds:
        for p in PLANS:
            d = [(x, res[p]) for g, r, x, res in rows if r == rd and p in res]
            if len(d) < 40 or len({w for _, w in d}) < 2:
                continue
            X, y = np.array([x for x, _ in d]), np.array([w >= 0.5 for _, w in d])
            models[(rd, p)] = LogisticRegression(C=0.5, max_iter=2000).fit(X, y)
    return models


def decide(models, rd, x, margin):
    probs = {p: models[(rd, p)].predict_proba([x])[0, 1] for p in PLANS if (rd, p) in models}
    if 0 not in probs:
        return 0
    best = max(probs, key=probs.get)
    return best if probs[best] > probs[0] + margin else 0


def policy_value(rows_by_group, models, rounds, margin):
    """Per group: walk the rounds in time order; switch at the first round whose decision is not 0. Returns {group: win}
    or None for groups whose chosen branch was not played."""
    out = {}
    for g, by_round in rows_by_group.items():
        win = by_round['base']
        for rd in sorted(rounds):
            if rd not in by_round:
                continue
            x, res = by_round[rd]
            p = decide(models, rd, x, margin)
            if p:
                win = res.get(p)
                break
        if win is not None:
            out[g] = win
    return out


def ci_by_map(vals):
    by_map = defaultdict(list)
    for g, w in vals.items():
        by_map[g[2]].append(w)
    maps = list(by_map)
    rng = random.Random(1)
    boots = []
    for _ in range(1000):
        s = [w for m in (rng.choice(maps) for _ in maps) for w in by_map[m]]
        boots.append(sum(s) / len(s))
    boots.sort()
    return sum(vals.values()) / len(vals), boots[25], boots[974]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rows', nargs='+')
    ap.add_argument('--rounds', type=int, nargs='+', default=[150, 300, 450, 600, 750, 900, 1050, 1200])
    ap.add_argument('--margins', type=float, nargs='+', default=[0.0, 0.05, 0.1, 0.15, 0.2])
    ap.add_argument('--folds', type=int, default=5)
    ap.add_argument('--out', default='artifacts/evaluations/plan_model.json')
    a = ap.parse_args()
    base, branch = load(a.rows)
    rows = table(base, branch, a.rounds)
    print(f'{len(base)} baselines, {len(rows)} (group, round) positions, '
          f'{sum(len(r[3]) - 1 for r in rows)} played or settled branches')
    groups = defaultdict(dict)
    for g, rd, x, res in rows:
        groups[g][rd] = (x, res)
    for g in groups:
        groups[g]['base'] = base[g]['win']
    maps = sorted({g[2] for g in groups})
    random.Random(0).shuffle(maps)
    fold = {m: i % a.folds for i, m in enumerate(maps)}
    report = {}
    for margin in a.margins:
        vals = {}
        for k in range(a.folds):
            train = [r for r in rows if fold[r[0][2]] != k]
            test = {g: v for g, v in groups.items() if fold[g[2]] == k}
            vals.update(policy_value(test, fit(train, a.rounds), a.rounds, margin))
        bvals = {g: groups[g]['base'] for g in vals}
        wr, lo, hi = ci_by_map(vals)
        bw = sum(bvals.values()) / len(bvals)
        diff = {g: vals[g] - bvals[g] + 0.5 for g in vals}
        _, dlo, dhi = ci_by_map(diff)
        report[margin] = dict(groups=len(vals), policy=wr, ci=[lo, hi], baseline=bw, gain=wr - bw, gain_ci=[dlo - .5, dhi - .5])
        print(f'margin {margin:.2f}: policy {wr:.3f} ({lo:.3f}-{hi:.3f}) vs baseline {bw:.3f} on {len(vals)} groups; '
              f'gain {wr - bw:+.3f} ({dlo - .5:+.3f}..{dhi - .5:+.3f})')
    for rd in a.rounds:
        r_rows = [r for r in rows if r[1] == rd and len(r[3]) == len(PLANS)]
        if not r_rows:
            continue
        fixed = {p: np.mean([r[3][p] for r in r_rows]) for p in PLANS}
        oracle = np.mean([max(r[3].values()) for r in r_rows])
        print(f'round {rd:4d}: n={len(r_rows):5d} oracle {oracle:.3f} | ' + ' '.join(f'p{p} {v:.3f}' for p, v in fixed.items()))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({str(k): v for k, v in report.items()}, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
