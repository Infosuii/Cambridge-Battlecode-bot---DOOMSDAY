"""Flee verdicts by source from an A2_MICLOG run of bots/v80+ (MT lines carry dsrc, x, y).

Usage: c_fleesrc.py RUN [RUN ...]
dsrc bits: 1 time-to-die formula, 2 low health, 4 burst, 16 search run, 32 search fight, 64 formula winning,
128 team-ratio engage. For contact turns (enemy within 4) ending in a flee mode: share by source, and the same for
flees beside a teammate (another of ours within 3 this round, from the logged positions) at 50%+ health.
"""
import collections
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def label(d):
    if d & 16:
        return 'search run'
    if d & 4:
        return 'burst'
    if d & 2:
        return 'low health'
    if d & 1:
        return 'ttd formula'
    return 'other'


def main():
    C = collections.Counter()
    G = collections.Counter()
    for run in sys.argv[1:]:
        games = json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']
        seen = set()
        for g in games:
            key = (g['map'], g['side'], g['seed'])
            if key in seen:
                continue
            seen.add(key)
            b = next((ROOT / g['folder']).glob('*.repl26a'))
            with zipfile.ZipFile(b) as z:
                t = z.read(f"team-{g['side']}.stdout").replace(b'\0', b'').decode('utf8', 'replace')
            by_round = collections.defaultdict(list)
            for l in t.splitlines():
                if l.startswith('MT '):
                    p = l.split()
                    if len(p) >= 22:
                        by_round[int(p[1])].append(p)
            for rnd, L in by_round.items():
                for p in L:
                    if int(p[5]) > 4 or not p[8].startswith('flee'):
                        continue
                    d = int(p[19])
                    x, y = int(p[20]), int(p[21])
                    C[label(d)] += 1
                    C['all'] += 1
                    mate = any(q is not p and max(abs(int(q[20]) - x), abs(int(q[21]) - y)) <= 3 for q in L)
                    if mate and float(p[4]) >= 0.5:
                        G[label(d)] += 1
                        G['all'] += 1
    for name, K in (('all contact flees', C), ('beside a teammate at 50%+ health', G)):
        n = K['all']
        print(f'{name}: {n} turns; ' + ', '.join(f'{k} {100 * v / n:.0f}%' for k, v in K.most_common() if k != 'all'))


if __name__ == '__main__':
    main()
