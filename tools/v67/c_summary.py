"""Compact per-run summary from summaries: wins, margin, our/their deaths, kills, earned gold, gems collected/lost.

Usage: c_summary.py RUN [RUN ...]   (distinct map/side/seed games only)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    print(f"{'run':24s} {'games':>5s} {'wins':>5s} {'margin':>7s} {'deaths':>11s} {'kills':>11s} {'gold':>11s} {'collected':>11s}")
    for run in sys.argv[1:]:
        games = json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']
        wins = sum(g['win'] for g in games)
        margin = sum(g['margin'] for g in games) / len(games)
        seen, tot = set(), {}
        for g in games:
            key = (g['map'], g['side'], g['seed'])
            if key in seen:
                continue
            seen.add(key)
            s = json.loads((ROOT / g['folder'] / 'summary.json').read_text())
            us = 'teamA' if g['side'] == 'a' else 'teamB'
            for c in s['champions']:
                side = 'us' if c['team'] == us else 'them'
                for m in ('deaths', 'kills', 'earnedGold', 'collectedGems'):
                    tot[(side, m)] = tot.get((side, m), 0) + float(c['metrics'][m])
        n = len(seen)
        f = lambda m: f"{tot[('us', m)] / n:5.1f}/{tot[('them', m)] / n:<5.1f}" if m in ('deaths', 'kills') \
            else f"{tot[('us', m)] / n:5.0f}/{tot[('them', m)] / n:<5.0f}"
        print(f"{run:24s} {len(games):5d} {wins:5d} {margin:+7.1f} {f('deaths'):>11s} {f('kills'):>11s} "
              f"{f('earnedGold'):>11s} {f('collectedGems'):>11s}")


if __name__ == '__main__':
    main()
