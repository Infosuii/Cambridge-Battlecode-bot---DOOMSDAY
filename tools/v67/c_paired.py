"""Paired verdict: candidate run against a baseline run on the same plan and seeds.

Usage: c_paired.py CANDIDATE_RUN BASELINE_RUN [--boot 2000]
Games are paired by (map, side, seed); a repeated slot counts once. Reports wins per distinct game for both, the mean
paired margin difference with a 95% bootstrap interval that resamples maps (games on one map are correlated), the
deaths and gold differences, and the maps that moved most.
"""
import argparse
import collections
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def distinct(run):
    out = {}
    for g in json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']:
        out.setdefault((g['map'], g['side'], g['seed']), g)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('candidate')
    ap.add_argument('baseline')
    ap.add_argument('--boot', type=int, default=2000)
    a = ap.parse_args()
    cand, base = distinct(a.candidate), distinct(a.baseline)
    keys = sorted(set(cand) & set(base))
    if not keys:
        raise SystemExit('no common (map, side, seed) games: use the same plan and seeds')
    if len(keys) < max(len(cand), len(base)):
        print(f'warning: {len(cand)} candidate / {len(base)} baseline distinct games, {len(keys)} in common')
    d = {k: cand[k]['margin'] - base[k]['margin'] for k in keys}
    by_map = collections.defaultdict(list)
    for k, v in d.items():
        by_map[k[0]].append(v)
    maps = sorted(by_map)
    rng = random.Random(1)
    means = []
    for _ in range(a.boot):
        sample = [v for m in (rng.choice(maps) for _ in maps) for v in by_map[m]]
        means.append(sum(sample) / len(sample))
    means.sort()
    lo, hi = means[int(0.025 * a.boot)], means[int(0.975 * a.boot)]
    n = len(keys)
    cw, bw = sum(cand[k]['win'] for k in keys), sum(base[k]['win'] for k in keys)
    print(f'{a.candidate} vs {a.baseline}: {n} distinct paired games over {len(maps)} maps')
    print(f'  wins: candidate {cw}/{n} ({cw / n:.1%}), baseline {bw}/{n} ({bw / n:.1%}), difference {cw - bw:+d}')
    print(f'  margin difference per game: {sum(d.values()) / n:+.1f} gems, 95% CI [{lo:+.1f}, {hi:+.1f}] '
          f"({'better' if lo > 0 else 'worse' if hi < 0 else 'not distinguishable'})")
    for field in ('deaths', 'gold', 'fuel'):
        dc = sum(cand[k][field] for k in keys) / n - sum(base[k][field] for k in keys) / n
        print(f'  {field} per game: {sum(cand[k][field] for k in keys) / n:.1f} vs {sum(base[k][field] for k in keys) / n:.1f} '
              f'({dc:+.1f})')
    moved = sorted(((sum(v) / len(v), m) for m, v in by_map.items()))
    print('  most worse maps:', ', '.join(f'{m} {x:+.0f}' for x, m in moved[:5]))
    print('  most better maps:', ', '.join(f'{m} {x:+.0f}' for x, m in moved[-5:][::-1]))


if __name__ == '__main__':
    main()
