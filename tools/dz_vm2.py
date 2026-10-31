"""V-M2 (VALIDATION_PLAN.md): does a stat-aware engagement estimate predict 4-round death better than the
HP-and-numbers logistic baseline? Offline, game-grouped 5-fold cross-validation on tools/dz_contacts.mjs samples.

Usage: python tools/dz_vm2.py CONTACT_DIR [CONTACT_DIR ...] [--out RESULTS.json]
Models: (0) DZ's current heuristic as is (death predicted when the bots/dz/src/fight.h simulation is lost; binary);
(1) baseline logistic on hp fraction, ally/enemy counts and nearest enemy distance; (2) EE logistic = baseline plus the
fight.h simulation outcome and strength-weighted force ratios. Pass: EE Brier below the baseline's with the
game-clustered 95% interval of the difference below zero. Writes coefficients for the bot when it passes.
"""
import argparse
import json
import random
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression


def simulate(ours, theirs, max_rounds=40):
    """bots/dz/src/fight.h simulate_fight: simultaneous focus fire on the weakest; (won, self_alive, rounds)."""
    a = [max(0.0, h) for h, _ in ours]
    b = [max(0.0, h) for h, _ in theirs]
    r = 0
    while r < max_rounds and any(x > 0 for x in a) and any(x > 0 for x in b):
        to_b = sum(d for (h, d), x in zip(ours, a) if x > 0)
        to_a = sum(d for (h, d), x in zip(theirs, b) if x > 0)
        tb = min((i for i, x in enumerate(b) if x > 0), key=lambda i: b[i])
        ta = min((i for i, x in enumerate(a) if x > 0), key=lambda i: a[i])
        b[tb] -= to_b
        a[ta] -= to_a
        r += 1
    won = not any(x > 0 for x in b) and a[0] > 0
    return won, a[0] > 0, r


def features(s):
    me, allies, enemies = s['me'], s['allies'], s['enemies']
    hpf = me['hp'] / max(1.0, me['max_hp'])
    near = min(e['d'] for e in enemies)
    base = [hpf, len(allies), len(enemies), near / 8.0]
    ours = [(me['hp'], me['strength'])] + [(a['hp'], a['strength']) for a in allies]
    theirs = [(1.25 * e['hp'], e['strength']) for e in enemies]
    won, alive, rounds = simulate(ours, theirs)
    power = lambda units: sum(h * d for h, d in units)
    po, pt = power(ours), power([(e['hp'], e['strength']) for e in enemies])
    ratio = po / (po + pt) if po + pt > 0 else .5  # Share form: the bot avoids libm log.
    reach = sum(e['strength'] for e in enemies if e['d'] <= 2)
    ttd = min(me['hp'] / reach, 20.0) / 20.0 if reach > 0 else 1.0
    top = max(e['strength'] for e in enemies)
    str_ratio = me['strength'] / (me['strength'] + top) if me['strength'] + top > 0 else .5
    ee = base + [float(won), float(alive), rounds / 40.0, ratio, ttd, str_ratio]
    return base, ee, 0.0 if won else 1.0


def load(dirs):
    games = {}
    for d in dirs:
        for p in sorted(Path(d).glob('*.json')):
            games[f'{Path(d).name}/{p.stem}'] = json.loads(p.read_text())
    return games


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dirs', nargs='+')
    ap.add_argument('--out')
    ap.add_argument('--header', help='write bots/dz/src/ee_model.h coefficients (only when V-M2 passes)')
    a = ap.parse_args()
    games = load(a.dirs)
    names = sorted(games)
    rng = random.Random(0)
    rng.shuffle(names)
    fold = {g: i % 5 for i, g in enumerate(names)}
    X0, X1, H, y, G = [], [], [], [], []
    for g in names:
        for s in games[g]:
            b, e, h = features(s)
            X0.append(b); X1.append(e); H.append(h); y.append(1.0 if s['dies4'] else 0.0); G.append(g)
    X0, X1, H, y = map(np.array, (X0, X1, H, y))
    p0, p1 = np.zeros(len(y)), np.zeros(len(y))
    for k in range(5):
        tr = np.array([fold[g] != k for g in G]); te = ~tr
        p0[te] = LogisticRegression(max_iter=2000).fit(X0[tr], y[tr]).predict_proba(X0[te])[:, 1]
        p1[te] = LogisticRegression(max_iter=2000).fit(X1[tr], y[tr]).predict_proba(X1[te])[:, 1]
    sq = lambda p: (p - y) ** 2
    per_game = {}
    eh, e0, e1 = sq(H), sq(p0), sq(p1)  # Once: indexing a fresh array per sample is quadratic.
    for i, g in enumerate(G):
        r = per_game.setdefault(g, [0.0, 0.0, 0.0, 0])
        r[0] += eh[i]; r[1] += e0[i]; r[2] += e1[i]; r[3] += 1
    diffs = []
    for _ in range(2000):
        pick = [names[rng.randrange(len(names))] for _ in names]
        n = sum(per_game[g][3] for g in pick)
        diffs.append((sum(per_game[g][2] for g in pick) - sum(per_game[g][1] for g in pick)) / n)
    diffs.sort()
    res = dict(games=len(names), samples=int(len(y)), deaths4=int(y.sum()), base_rate=float(y.mean()),
               brier_heuristic=float(sq(H).mean()), brier_baseline=float(sq(p0).mean()), brier_ee=float(sq(p1).mean()),
               ee_minus_baseline=float(sq(p1).mean() - sq(p0).mean()), ci95=[diffs[50], diffs[1949]])
    res['pass'] = bool(res['ci95'][1] < 0)
    full = LogisticRegression(max_iter=2000).fit(X1, y)
    res['ee_coefficients'] = dict(intercept=float(full.intercept_[0]), weights=[float(w) for w in full.coef_[0]],
        features=['hp_fraction', 'allies6', 'enemies8', 'nearest/8', 'sim_won', 'sim_self_alive', 'sim_rounds/40',
                  'power_share', 'time_to_die/20', 'strength_share'])
    print(json.dumps(res, indent=1))
    if a.header and res['pass']:
        c = res['ee_coefficients']
        lines = ['#pragma once',
                 '// Generated by tools/dz_vm2.py (V-M2 pass: EE Brier %.5f vs baseline %.5f, %d games, %d samples).'
                 % (res['brier_ee'], res['brier_baseline'], res['games'], res['samples']),
                 '// Logit of dying within 4 rounds; features in tools/dz_vm2.py order: %s.' % ', '.join(c['features']),
                 'namespace dz::ee_model {',
                 'inline constexpr float intercept = %.6ff;' % c['intercept'],
                 'inline constexpr float weights[%d] = {%s};' % (len(c['weights']), ', '.join('%.6ff' % w for w in c['weights'])),
                 '}', '']
        Path(a.header).write_text('\n'.join(lines), encoding='utf-8', newline='\n')
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
