"""Compare completed benchmark runs per map/side and across seeds.

Usage: c_compare.py RUN [RUN ...]
Prints each run's totals, seed-to-seed agreement of (map, side) outcomes, and
map/side cells ordered by mean margin across all given runs.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(run):
    return json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text(encoding='utf8'))['games']


def main():
    runs = sys.argv[1:]
    cells = defaultdict(list)
    for run in runs:
        games = load(run)
        wins = sum(g['win'] for g in games)
        margin = sum(g['margin'] for g in games) / len(games)
        by = defaultdict(dict)
        for g in games:
            by[(g['map'], g['side'], g['slot'])][g['seed']] = g
            cells[(g['map'], g['side'])].append(g['margin'])
        seeds = sorted({g['seed'] for g in games})
        agree = total = 0
        for v in by.values():
            if len(v) == 2:
                a, b = (v[s]['win'] for s in seeds[:2])
                agree += a == b
                total += 1
        print(f'{run}: {wins}/{len(games)} margin {margin:+.1f} seed agreement {agree}/{total}')
    rows = sorted(cells.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))
    print('\nworst map/side cells (mean margin, wins/games):')
    for (m, s), ms in rows[:30]:
        print(f'  {m:28s} {s} {sum(ms)/len(ms):+8.1f} {sum(x > 0 for x in ms)}/{len(ms)}')
    lost = sum(1 for _, ms in rows if sum(x > 0 for x in ms) == 0)
    won = sum(1 for _, ms in rows if all(x > 0 for x in ms))
    print(f'\ncells always lost {lost}, always won {won}, of {len(rows)}')


if __name__ == '__main__':
    main()
