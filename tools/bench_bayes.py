"""Bayesian comparison of bench runs: hierarchical map effects with heavy-tailed game noise (numpy only).

    python tools/bench_bayes.py <prefix A> [<prefix B>] [--maps a,b] [--seeds 1,2,3] [--draws 6000] [--json out.json]

Same inputs as bench_compare.py: two prefixes compare A - B on identical (map, side, seed) games (two candidates
benched against the same opponent); one prefix reports a candidate against its own opponent.

Model, fitted separately to per-game gem-margin differences and to win differences:
    y_g = mu + b_map(g) + e_g,   b_m ~ Normal(0, tau^2),   e_g ~ Student-t(nu, 0, sigma)
with a Gibbs sampler (t errors as a scale mixture of normals). nu = 4 for gems (blowouts of +/-1000 are common),
nu = 30 (near normal) for wins. Weak priors: mu ~ N(0, 300^2) gems / N(0, 1) wins; sigma^2 and tau^2 inverse-gamma
with scales set from the data's spread, so the prior does not decide anything at our sample sizes.

Why this and not only the bootstrap: (1) per-map effects are pooled toward the overall effect, so a map that moved by
an inert-change amount (about +/-100 gems, +/-4 wins in 12) is not read as a real effect; (2) it states decisions as
probabilities, P(mu > 0) and P(mu > delta); (3) it supports sequential screening: stop a variant early when the
posterior is already decisive. Seeds are policy perturbations of the same map/opponent, which the map random effect
absorbs; games are still not a random sample of the ladder.

Decision rule printed (adjust with --accept/--reject): accept when P(mu_gems > 0) >= 0.95 and the posterior mean is
at least --min-gain gems; reject when P(mu_gems > 0) <= 0.05 or P(mu_gems > -25) <= 0.10; otherwise continue
(add seeds).
"""
import argparse
from collections import defaultdict
import glob
import json
from pathlib import Path
from bench_provenance import require_compatible

import numpy as np


def load(prefix, maps, seeds):
    out = {}
    for f in glob.glob(prefix + '-seed*-s*/summary.json'):
        seed = Path(f).parent.name.split('-seed')[-1].split('-')[0]
        if seeds and seed not in seeds:
            continue
        for g in json.loads(Path(f).read_text(encoding='utf-8'))['per_game']:
            if maps and g['map'] not in maps:
                continue
            out[(g['map'], g['side'], seed)] = (float(g['win']), float(g['gems'] - g['opponent_gems']))
    return out


def gibbs(y, groups, n_groups, nu, mu_sd, draws, burn, seed):
    """Posterior draws of mu, tau, sigma and per-group effects b for y = mu + b[group] + t_nu(sigma) noise."""
    rng = np.random.default_rng(seed)
    n = len(y)
    spread = float(np.std(y)) or 1.0
    a_s, b_s = 2.0, spread ** 2       # sigma^2 ~ InvGamma(2, spread^2): prior mean spread^2, weak
    a_t, b_t = 2.0, (0.5 * spread) ** 2  # tau^2 ~ InvGamma(2, (spread/2)^2)
    mu, b = float(np.mean(y)), np.zeros(n_groups)
    sig2, tau2, lam = spread ** 2, (0.5 * spread) ** 2, np.ones(n)
    out = {'mu': [], 'tau': [], 'sigma': [], 'b': []}
    counts = np.bincount(groups, minlength=n_groups)
    for it in range(draws + burn):
        # latent precisions of the t errors
        r = y - mu - b[groups]
        lam = rng.gamma((nu + 1) / 2, 2.0 / (nu + r * r / sig2))
        # group effects
        w = lam / sig2
        sw = np.bincount(groups, weights=w, minlength=n_groups)
        sr = np.bincount(groups, weights=w * (y - mu), minlength=n_groups)
        prec = sw + 1.0 / tau2
        b = rng.normal(sr / prec, 1.0 / np.sqrt(prec))
        b[counts == 0] = rng.normal(0.0, np.sqrt(tau2), int(np.sum(counts == 0)))
        # overall effect
        prec_mu = float(np.sum(w)) + 1.0 / mu_sd ** 2
        mu = rng.normal(float(np.sum(w * (y - b[groups]))) / prec_mu, 1.0 / np.sqrt(prec_mu))
        # variances
        r = y - mu - b[groups]
        sig2 = 1.0 / rng.gamma(a_s + n / 2, 1.0 / (b_s + float(np.sum(lam * r * r)) / 2))
        tau2 = 1.0 / rng.gamma(a_t + n_groups / 2, 1.0 / (b_t + float(np.sum(b * b)) / 2))
        if it >= burn:
            out['mu'].append(mu); out['tau'].append(np.sqrt(tau2)); out['sigma'].append(np.sqrt(sig2)); out['b'].append(b.copy())
    return {k: np.array(v) for k, v in out.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('a'); ap.add_argument('b', nargs='?')
    ap.add_argument('--maps'); ap.add_argument('--seeds'); ap.add_argument('--draws', type=int, default=6000)
    ap.add_argument('--min-gain', type=float, default=25.0, help='posterior mean gems required to accept')
    ap.add_argument('--json')
    args = ap.parse_args()
    maps = set(args.maps.split(',')) if args.maps else None
    seeds = set(args.seeds.split(',')) if args.seeds else None
    require_compatible(args.a, args.b)
    A = load(args.a, maps, seeds)
    B = load(args.b, maps, seeds) if args.b else None
    keys = sorted(A.keys() & B.keys()) if B else sorted(A)
    if len(keys) < 4:
        raise SystemExit('too few (paired) games')
    mlist = sorted({k[0] for k in keys})
    gi = np.array([mlist.index(k[0]) for k in keys])
    gem = np.array([A[k][1] - (B[k][1] if B else 0.0) for k in keys])
    win = np.array([A[k][0] - (B[k][0] if B else 0.5) for k in keys])  # single run: win rate minus 0.5
    burn = max(500, args.draws // 5)
    pg = gibbs(gem, gi, len(mlist), 4.0, 300.0, args.draws, burn, 1)
    pw = gibbs(win, gi, len(mlist), 30.0, 1.0, args.draws, burn, 2)
    mu, muw = pg['mu'], pw['mu']
    q = lambda x, p: float(np.quantile(x, p))
    p_pos = float(np.mean(mu > 0))
    seeds_used = sorted({k[2] for k in keys}, key=int)
    what = 'A - B (paired)' if B else 'candidate vs its opponent'
    print(f'{what}: {len(keys)} games, {len(mlist)} maps, seeds {",".join(seeds_used)}')
    print(f'  gems per game: posterior mean {mu.mean():+.1f}, 95% credible [{q(mu, .025):+.1f}, {q(mu, .975):+.1f}]; '
          f'P(>0) {p_pos:.3f}, P(>25) {np.mean(mu > 25):.3f}, P(>50) {np.mean(mu > 50):.3f}, P(>100) {np.mean(mu > 100):.3f}')
    base = 'difference in win probability' if B else 'win rate'
    off = 0.0 if B else 0.5
    print(f'  {base}: posterior mean {muw.mean() + off:+.3f}, 95% credible [{q(muw, .025) + off:+.3f}, {q(muw, .975) + off:+.3f}]; '
          f'P({"A better" if B else "> 0.5"}) {np.mean(muw > 0):.3f}')
    print(f'  between-map sd tau {pg["tau"].mean():.0f} gems, game noise sigma {pg["sigma"].mean():.0f} gems (t, nu=4)')
    if p_pos >= 0.95 and mu.mean() >= args.min_gain:
        verdict = 'ACCEPT: better with posterior probability >= 0.95'
    elif p_pos <= 0.05 or np.mean(mu > -25) <= 0.10:
        verdict = 'REJECT: worse, or a gain is very unlikely'
    else:
        verdict = 'CONTINUE: not decisive; add seeds (or treat as neutral)'
    print(f'  decision: {verdict}')
    print(f'  incomplete-loop check: mean >= -25 {bool(mu.mean() >= -25)}; P(> -50) {np.mean(mu > -50):.3f}')
    eff = pg['mu'][:, None] + pg['b']
    raw = defaultdict(list)
    for k, v in zip(keys, gem):
        raw[k[0]].append(v)
    print(f'  {"map":24s} {"games":>5s} {"raw":>8s} {"pooled":>8s} {"95% credible":>18s}  P(>0)  flag')
    rows = []
    for j, m in enumerate(mlist):
        e = eff[:, j]
        p = float(np.mean(e > 0))
        flag = 'likely gain' if p >= 0.9 else 'likely loss' if p <= 0.1 else ''
        print(f'  {m:24s} {len(raw[m]):5d} {np.mean(raw[m]):+8.1f} {e.mean():+8.1f} [{q(e, .025):+7.1f}, {q(e, .975):+7.1f}]  {p:.2f}  {flag}')
        rows.append({'map': m, 'games': len(raw[m]), 'raw': float(np.mean(raw[m])), 'pooled': float(e.mean()),
                     'ci95': [q(e, .025), q(e, .975)], 'p_gain': p, 'flag': flag})
    if args.json:
        Path(args.json).write_text(json.dumps({'a': args.a, 'b': args.b, 'games': len(keys), 'maps': len(mlist), 'seeds': seeds_used,
            'gems_mean': float(mu.mean()), 'gems_ci95': [q(mu, .025), q(mu, .975)], 'p_gain': p_pos,
            'p_gain_25': float(np.mean(mu > 25)), 'p_gain_50': float(np.mean(mu > 50)), 'win_mean': float(muw.mean() + off),
            'p_gain_neg50': float(np.mean(mu > -50)), 'p_gain_neg25': float(np.mean(mu > -25)),
            'win_ci95': [q(muw, .025) + off, q(muw, .975) + off], 'tau': float(pg['tau'].mean()), 'sigma': float(pg['sigma'].mean()),
            'decision': verdict, 'per_map': rows}, indent=1) + '\n')


if __name__ == '__main__':
    main()
