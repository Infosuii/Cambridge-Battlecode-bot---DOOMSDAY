"""Adapt a local run for the same timeline scripts used on ladder replays.

Usage: local_index.py RUN. Timelines stay beside each game's replay; duplicate
schedule cells are counted once, just as in c_paired.py.
"""
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[3]
run = sys.argv[1]
games = json.loads((root / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']
seen, rows = set(), []
for g in games:
    key = g['map'], g['side'], g['seed']
    if key in seen:
        continue
    seen.add(key)
    rows.append(dict(matchId=g['folder'], map=g['map'], side=g['side'],
                     result='win' if g['win'] else 'draw' if g['draw'] else 'loss'))
out = root / 'research/v75' / f'{run}_index.json'
out.write_text(json.dumps(rows, indent=1) + '\n')
print(out.relative_to(root), len(rows), 'distinct games; use repo root as FOLDER')
