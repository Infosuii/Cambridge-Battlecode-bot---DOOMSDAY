"""Paired comparison of two candidates benched against the same opponent: only (map, side, seed) games both have.

Usage: python tools/bench_paired.py <prefix A> <prefix B> [maps comma list]
"""
import glob
import json
from pathlib import Path
import sys


def load(prefix):
    out = {}
    for f in glob.glob(prefix + '-seed*-s*/summary.json'):
        seed = Path(f).parent.name.split('-seed')[-1].split('-')[0]
        for g in json.loads(Path(f).read_text(encoding='utf-8'))['per_game']:
            out[(g['map'], g['side'], seed)] = (g['win'], g['gems'] - g['opponent_gems'])
    return out


a, b = load(sys.argv[1]), load(sys.argv[2])
maps = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else None
keys = sorted(k for k in a.keys() & b.keys() if not maps or k[0] in maps)
n = len(keys)
wa, wb = sum(a[k][0] for k in keys), sum(b[k][0] for k in keys)
ma, mb = sum(a[k][1] for k in keys) / n, sum(b[k][1] for k in keys) / n
d = [a[k][1] - b[k][1] for k in keys]
sd = (sum((x - (ma - mb)) ** 2 for x in d) / max(1, n - 1)) ** 0.5
print(f'{n} paired games: A {wa:.0f} wins, {ma:+.1f}; B {wb:.0f} wins, {mb:+.1f}; margin difference {ma - mb:+.1f} '
      f'(naive s.e. {sd / n ** 0.5:.1f}; games are not independent)')
