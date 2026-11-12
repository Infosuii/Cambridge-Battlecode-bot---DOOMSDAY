"""Pool several runs of comparable bots and classify each schedule slot by its pooled win rate.

Usage: c_cells.py RUN [RUN ...]
Slots are (map, side); every run contributes its games for that slot. Prints the number of schedule games
(per 240) that fall in structural-loss (<20% wins), coin-flip and structural-win (>80%) slots.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    runs = sys.argv[1:]
    pooled = defaultdict(list)
    per_run_slots = None
    for run in runs:
        games = json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']
        slots = defaultdict(int)
        for g in games:
            pooled[(g['map'], g['side'])].append((g['win'], g['margin']))
            slots[(g['map'], g['side'])] += 1
        per_run_slots = slots
    buckets = {'loss': [], 'flip': [], 'win': []}
    for key, rs in pooled.items():
        rate = sum(w for w, _ in rs) / len(rs)
        b = 'loss' if rate < 0.2 else 'win' if rate > 0.8 else 'flip'
        buckets[b].append((key, rate, sum(m for _, m in rs) / len(rs), len(rs)))
    for b, rows in buckets.items():
        n = sum(per_run_slots[k] for k, *_ in rows)
        print(f'{b}: {len(rows)} cells, {n} games per 240')
    print('\nstructural losses:')
    for key, rate, margin, n in sorted(buckets['loss'], key=lambda r: r[2]):
        print(f'  {key[0]:24s} {key[1]} rate {rate:.2f} margin {margin:+7.1f} n={n} sched={per_run_slots[key]}')
    print('\ncoin flips (most negative first):')
    for key, rate, margin, n in sorted(buckets['flip'], key=lambda r: r[2])[:40]:
        print(f'  {key[0]:24s} {key[1]} rate {rate:.2f} margin {margin:+7.1f} n={n} sched={per_run_slots[key]}')


if __name__ == '__main__':
    main()
