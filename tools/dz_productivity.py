"""Summarise DZ_STUCK and DZ_PROD trace lines of a trace-build run.

Usage: python tools/dz_productivity.py RUN [ROUND]
ROUND (default 1000) picks the cumulative DZ_PROD snapshot per body.
"""
import collections, glob, os, re, sys

run = sys.argv[1]; at = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
stuck = collections.Counter(); kinds = collections.Counter(); prod = collections.Counter(); games = 0
for g in glob.glob(f'artifacts/tmp/dz/{run}/games/*'):
    games += 1
    text = open(os.path.join(g, 'candidate.stdout'), encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'DZ_STUCK round=\d+ slot=\d+ kind=(\d+) index=-?\d+ pos=\S+ .*? dist=(-?\d+) state=(-?\d+)', text):
        stuck[os.path.basename(g)] += 1; kinds[(m[1], m[3])] += 1
    for m in re.finditer(r'DZ_TIME round=(\d+) slot=\d+[^\n]*? prod (\d+) (\d+) (\d+) (\d+) (\d+)', text):
        if int(m[1]) == at:
            for k, v in zip(('work', 'progress', 'stall', 'idle', 'other'), map(int, m.group(2, 3, 4, 5, 6))): prod[k] += v
total = sum(prod.values()) or 1
print(f'{run}: games={games} stuck_episodes={sum(stuck.values())} by (goal kind, group state)={dict(kinds)}')
print(f'body-turns to R{at}: ' + ' '.join(f'{k}={100 * v / total:.1f}%' for k, v in prod.items()))
print('worst maps', stuck.most_common(6))
