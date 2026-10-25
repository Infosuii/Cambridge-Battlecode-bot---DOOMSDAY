"""Compare bench runs with uncertainty that respects how the games are correlated.

    python tools/bench_compare.py <prefix A> [<prefix B>] [--maps a,b,c] [--boot 4000] [--json out.json]

With two prefixes (two candidates benched against the same opponent) only identical (map, side, seed) games are
paired, and the difference A - B is reported. With one prefix, the candidate's own result against its opponent is
reported. Games on one map are strongly correlated (same terrain, same opponent policy, seeds are perturbations), so
the 95% interval is a cluster bootstrap that resamples maps, not games. A naive per-game interval is printed for
contrast. The per-map table flags maps whose paired mean change exceeds the inert-change noise band measured for
this bot (about +/-100 gems per map; +/-4 wins in 12), so single-map "effects" inside it are not over-read.
"""
import argparse
from collections import defaultdict
import glob
import json
from pathlib import Path
import random
import statistics as st

NOISE_GEMS = 100.0


def load(prefix, maps):
    out = {}
    for f in glob.glob(prefix + '-seed*-s*/summary.json'):
        seed = Path(f).parent.name.split('-seed')[-1].split('-')[0]
        for g in json.loads(Path(f).read_text(encoding='utf-8'))['per_game']:
            if maps and g['map'] not in maps:
                continue
            out[(g['map'], g['side'], seed)] = (float(g['win']), g['gems'] - g['opponent_gems'], g.get('faults', 0))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('a'); ap.add_argument('b', nargs='?')
    ap.add_argument('--maps'); ap.add_argument('--boot', type=int, default=4000); ap.add_argument('--json')
    args = ap.parse_args()
    maps = set(args.maps.split(',')) if args.maps else None
    A = load(args.a, maps)
    B = load(args.b, maps) if args.b else None
    keys = sorted(A.keys() & B.keys()) if B else sorted(A)
    if not keys:
        raise SystemExit('no games (or no paired games)')
    # Per-game values: the difference A - B when paired, else A's own result.
    win = {k: A[k][0] - (B[k][0] if B else 0.0) for k in keys}
    gem = {k: A[k][1] - (B[k][1] if B else 0.0) for k in keys}
    by_map = defaultdict(list)
    for k in keys:
        by_map[k[0]].append(k)
    mlist = sorted(by_map)
    n = len(keys)
    mean_w, mean_g = sum(win.values()) / n, sum(gem.values()) / n
    rng = random.Random(12345)
    bw, bg = [], []
    for _ in range(args.boot):
        ks = [k for m in (rng.choice(mlist) for _ in mlist) for k in by_map[m]]
        bw.append(sum(win[k] for k in ks) / len(ks)); bg.append(sum(gem[k] for k in ks) / len(ks))
    bw.sort(); bg.sort()
    lo, hi = int(0.025 * args.boot), int(0.975 * args.boot) - 1
    sd_g = st.pstdev(gem.values()) if n > 1 else 0.0
    faults = sum(A[k][2] for k in keys) + (sum(B[k][2] for k in keys) if B else 0)
    seeds = sorted({k[2] for k in keys}, key=int)
    what = 'A - B (paired)' if B else 'candidate vs its opponent'
    print(f'{what}: {n} games, {len(mlist)} maps, seeds {",".join(seeds)}, faults {faults}')
    if B:
        print(f'  wins: A {sum(A[k][0] for k in keys):.0f}, B {sum(B[k][0] for k in keys):.0f}  (difference {mean_w:+.3f} per game)')
    else:
        print(f'  record {sum(A[k][0] for k in keys):.0f}-{n - sum(A[k][0] for k in keys):.0f}, win rate {mean_w:.3f}')
    print(f'  mean gem margin {"difference " if B else ""}{mean_g:+.1f}; 95% map-cluster bootstrap [{bg[lo]:+.1f}, {bg[hi]:+.1f}]; '
          f'naive per-game +/-{1.96 * sd_g / n ** 0.5:.1f}')
    print(f'  win {"difference" if B else "rate"} 95% map-cluster bootstrap [{bw[lo]:+.3f}, {bw[hi]:+.3f}]')
    verdict = 'better' if bg[lo] > 0 else 'worse' if bg[hi] < 0 else 'not distinguishable from zero'
    print(f'  margin verdict: {verdict} at 95% (map clusters)')
    print(f'  {"map":24s} {"games":>5s} {"win d" if B else "wins":>6s} {"gem d" if B else "margin":>8s}  flag')
    rows = []
    for m in mlist:
        ks = by_map[m]
        w, g = sum(win[k] for k in ks), sum(gem[k] for k in ks) / len(ks)
        flag = ('beyond noise' if abs(g) > NOISE_GEMS else '') if B else ''
        print(f'  {m:24s} {len(ks):5d} {w:+6.0f} {g:+8.1f}  {flag}')
        rows.append({'map': m, 'games': len(ks), 'win': w, 'gem': g, 'flag': flag})
    if args.json:
        Path(args.json).write_text(json.dumps({'a': args.a, 'b': args.b, 'games': n, 'maps': len(mlist), 'win_mean': mean_w,
            'gem_mean': mean_g, 'gem_ci95': [bg[lo], bg[hi]], 'win_ci95': [bw[lo], bw[hi]], 'faults': faults, 'per_map': rows}, indent=1) + '\n')


if __name__ == '__main__':
    main()
