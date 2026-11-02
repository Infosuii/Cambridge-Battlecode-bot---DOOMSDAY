"""Evolution-strategy knob search for x3 (antithetic ES over lab knob deltas, X1_KD).

Each candidate is an x3 build with X1_KD_ON=1, X1_KD="i,d,i,d,..." (deltas on top of v92's knobs, ladder tables and
per-map fit) and X1_KD_SCOPE. It plays a map subset (the same subset for every candidate of an iteration, so the
comparison is paired), both sides, against each opponent. Fitness per game = win + margin / 2000 (margin = our
banked - theirs). The mean moves along the antithetic differences; the best evaluated mean is kept.

  python tools/x3_knob_es.py --name fight1 --knobs 22,23,24,25,26,27,28,29,30,31,41,59 --map-dir maps/ladder-pool \
      --opps v92,v86h,x1bru --scope 0 --iters 8 --pairs 4 --sigma 0.4 --maps-per-iter 20 --workers 6

State and every evaluation go to research/x3/es/<name>.json (resumable: rerun the same command).
"""
import argparse, json, os, random, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def maps_in(d):
    return sorted(p.stem for p in (ROOT / d).glob('*.map26a'))


def play(tag, kd, scope, map_dir, maps, opps, workers):
    """Total fitness and per-game rows for one candidate (cached by run name)."""
    total, rows = 0.0, []
    kd_s = ','.join(f'{i},{d:.4f}' for i, d in kd) if kd else '0,0'
    for opp in opps:
        name = f'es-{tag}-{opp}'
        res = ROOT / 'artifacts/tmp/dz' / name / 'results.json'
        if not res.exists():
            cmd = [sys.executable, 'tools/dz.py', 'smoke', '--name', name, '--map-dir', map_dir, '--maps', *maps,
                   '--opponent', opp, '--candidate-bot', 'x3', '--workers', str(workers),
                   '--set', 'X1_KD_ON=1', '--set', f'X1_KD={kd_s}', '--set', f'X1_KD_SCOPE={scope}']
            subprocess.run(cmd, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not res.exists():
            raise RuntimeError(f'run {name} produced no results (see artifacts/tmp/{name}.log)')
        for g in json.loads(res.read_text())['per_game']:
            win = g['outcome'] == ('teamA' if g['side'] == 'A' else 'teamB')
            f = float(win) + (g['banked'] - g['opponent_banked']) / 2000.0
            total += f
            rows.append(dict(opp=opp, map=g['map'], side=g['side'], win=win, f=round(f, 4), deaths=g['deaths'],
                             fuel_outs=g['fuel_outs']))
    return total, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True)
    ap.add_argument('--knobs', required=True, help='comma-separated lab knob indices to search')
    ap.add_argument('--map-dir', default='maps/ladder-pool')
    ap.add_argument('--maps', default='', help='comma-separated subset (default: every map in --map-dir)')
    ap.add_argument('--opps', default='v92,v86h,x1bru')
    ap.add_argument('--scope', type=int, default=0)
    ap.add_argument('--iters', type=int, default=8)
    ap.add_argument('--pairs', type=int, default=4)
    ap.add_argument('--sigma', type=float, default=0.4)
    ap.add_argument('--lr', type=float, default=0.6)
    ap.add_argument('--maps-per-iter', type=int, default=20)
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args()

    idx = [int(x) for x in a.knobs.split(',')]
    pool = a.maps.split(',') if a.maps else maps_in(a.map_dir)
    opps = a.opps.split(',')
    out = ROOT / 'research/x3/es' / f'{a.name}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    st = json.loads(out.read_text()) if out.exists() else dict(args=vars(a), mean=[0.0] * len(idx), iters=[],
                                                                 best=dict(fit=None, kd=[0.0] * len(idx), iter=-1))
    rng = random.Random(a.seed)
    for it in range(a.iters):
        # The random stream is replayed from the seed so a resumed run draws the same subsets and noise.
        maps = rng.sample(pool, min(a.maps_per_iter, len(pool)))
        eps = [[rng.gauss(0, 1) for _ in idx] for _ in range(a.pairs)]
        if it < len(st['iters']):
            continue
        mean = st['mean']
        base_f, base_rows = play(f'{a.name}-i{it}-mean', list(zip(idx, mean)), a.scope, a.map_dir, maps, opps, a.workers)
        diffs, evals = [], []
        for k, e in enumerate(eps):
            plus = [m + a.sigma * x for m, x in zip(mean, e)]
            minus = [m - a.sigma * x for m, x in zip(mean, e)]
            fp, _ = play(f'{a.name}-i{it}-p{k}', list(zip(idx, plus)), a.scope, a.map_dir, maps, opps, a.workers)
            fm, _ = play(f'{a.name}-i{it}-m{k}', list(zip(idx, minus)), a.scope, a.map_dir, maps, opps, a.workers)
            diffs.append((fp - fm, e))
            evals.append(dict(k=k, plus=fp, minus=fm))
        # Rank-free antithetic gradient, normalised by the number of games so lr is independent of the subset size.
        games = max(1, len(base_rows))
        grad = [sum(d * e[j] for d, e in diffs) / (2 * a.pairs * a.sigma * games) for j in range(len(idx))]
        new_mean = [m + a.lr * g for m, g in zip(mean, grad)]
        rec = dict(iter=it, maps=maps, mean=mean, mean_fit=base_f, games=games, evals=evals, grad=grad,
                   wins=sum(r['win'] for r in base_rows), deaths=sum(r['deaths'] for r in base_rows),
                   fuel_outs=sum(r['fuel_outs'] for r in base_rows))
        st['iters'].append(rec)
        if st['best']['fit'] is None or base_f / games > st['best']['fit']:
            st['best'] = dict(fit=base_f / games, kd=mean, iter=it)
        st['mean'] = new_mean
        out.write_text(json.dumps(st, indent=1))
        print(f'iter {it}: mean fit/game {base_f / games:.3f} wins {rec["wins"]}/{games} '
              f'best iter {st["best"]["iter"]} grad |{max(abs(g) for g in grad):.3f}|', flush=True)
    kd = ','.join(f'{i},{d:.4f}' for i, d in zip(idx, st['best']['kd']))
    print(f'BEST X1_KD={kd} scope {a.scope} (fit/game {st["best"]["fit"]:.3f}, iter {st["best"]["iter"]})')


if __name__ == '__main__':
    main()
