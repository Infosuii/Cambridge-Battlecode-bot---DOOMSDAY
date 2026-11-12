"""Exact native earnedGold at R300/R500/R700, on common completed game windows.

Usage: native_windows.py CAND BASE. Income includes kills and passive bonuses.
"""
from collections import defaultdict
import json
from pathlib import Path
import random
import statistics as st
import sys

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / 'tools/replay'))
from review_v57_latest import value_at

def games(run):
    d = {}
    for g in json.loads((root / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']:
        key = g['map'], g['side'], g['seed']
        if key not in d:
            d[key] = g, json.loads((root / g['folder'] / 'summary.json').read_text())
    return d

cand, base = games(sys.argv[1]), games(sys.argv[2])
print(sys.argv[1], 'vs', sys.argv[2], 'exact native team income (kills and passives included)')
for rnd in (300, 500, 700):
    cells = defaultdict(list)
    for key in sorted(set(cand) & set(base)):
        if min(cand[key][1]['match']['roundsCompleted'], base[key][1]['match']['roundsCompleted']) < rnd:
            continue
        values = []
        for tab in (cand, base):
            g, native = tab[key]
            team = 'team' + g['side'].upper()
            values.append(sum(value_at(t['runs'], rnd) for t in native['championTimelines']
                              if t['owner']['team'] == team and t['metric'] == 'earnedGold'))
        cells[key[0]].append(values)
    values = [v for vs in cells.values() for v in vs]
    if not values:
        continue
    rng = random.Random(1)
    maps = sorted(cells)
    boot = []
    for _ in range(2000):
        sample = [c-b for m in (rng.choice(maps) for _ in maps) for c,b in cells[m]]
        boot.append(st.mean(sample))
    boot.sort()
    print(f'R{rnd}: n={len(values)} income {st.mean(v[0] for v in values):.1f} vs {st.mean(v[1] for v in values):.1f}, '
          f'delta {st.mean(v[0]-v[1] for v in values):+.1f} [{boot[50]:+.1f},{boot[1950]:+.1f}]; '
          f'excluded short games={len(set(cand)&set(base))-len(values)}')
