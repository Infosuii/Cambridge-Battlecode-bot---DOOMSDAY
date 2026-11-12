"""Observed gold multipliers on isolated camp captures, excluding kills, shopping and tribute.

Usage: capture_bonus.py INDEX FOLDER. Derives passives from replay payouts rather
than guessing the meaning of the Prospector metadata.
"""
import json
from collections import defaultdict
from pathlib import Path
import statistics as st
import sys

rows = json.loads(Path(sys.argv[1]).read_text())
cells = defaultdict(list)
for r in rows:
    folder = Path(sys.argv[2]) / r['matchId']
    d = json.loads((folder / 'audit500.json').read_text())
    tl = json.loads((folder / 'timeline.json').read_text())
    typ = {c['id']: c['type'] for c in tl['champs']}
    turns = defaultdict(list)
    for t in d['turns']:
        turns[t['round']].append(t)
    for prev, nxt in zip(d['frames'], d['frames'][1:]):
        captures = [gi for gi, (p, n) in enumerate(zip(prev[2], nxt[2]))
                    if p['rewardAvailable'] and not n['rewardAvailable']]
        if len(captures) != 1:
            continue
        gi = captures[0]
        team = prev[2][gi]['captureTeam']
        if team not in (0, 1):
            continue
        P, N = {x[0]: x for x in prev[1]}, {x[0]: x for x in nxt[1]}
        if any(P[c][4] and not N[c][4] for c in P):
            continue
        if any(act[0] == 12 for t in turns[prev[0]] for act in t['acts']):
            continue
        rises = [(c, N[c][5]-P[c][5]) for c in P if P[c][1] == team and N[c][5] > P[c][5]]
        if len(rises) != 1:
            continue
        c, gold = rises[0]
        if P[c][6] != N[c][6]:
            continue
        items = P[c][6]
        treasure = any(items[k] for k in (19, 21, 23))
        prospector = any(items[k] for k in (55, 57, 59))
        g = d['groups'][gi]
        if not g['gold']:
            continue
        cells[(typ[c] == 1, treasure, prospector, g['camps'][0]['type'])].append(gold/g['gold'])
print('isolated capture payout / base gold; spectator snapshots, no death, tribute or item change in the round')
for key, values in sorted(cells.items()):
    if len(values) >= 3:
        print(f'vesper={key[0]} treasure={key[1]} prospector={key[2]} camp={key[3]} '
              f'n={len(values):4} median={st.median(values):.3f} mean={st.mean(values):.3f} '
              f'range=[{min(values):.3f},{max(values):.3f}]')
