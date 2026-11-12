"""Per-game banking audit: tributed vs collected gems for our team and the opponent.

Usage: c_banking.py RUN [--seed N] [--max-margin M]
"""
import argparse
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('--seed', type=int)
    ap.add_argument('--max-margin', type=int, default=10**9)
    a = ap.parse_args()
    games = json.loads((ROOT / 'artifacts/evaluations/v67' / a.run / 'games.json').read_text())['games']
    for x in sorted(games, key=lambda g: g['margin']):
        if (a.seed and x['seed'] != a.seed) or x['margin'] > a.max_margin:
            continue
        s = json.loads((ROOT / x['folder'] / 'summary.json').read_text())
        us = 'teamA' if x['side'] == 'a' else 'teamB'
        them = 'teamB' if us == 'teamA' else 'teamA'
        sub = {t['team']: int(t['submittedGems']) for t in s['teams']}
        col = collections.Counter()
        deaths = collections.Counter()
        for c in s['champions']:
            col[c['team']] += int(c['metrics']['collectedGems'])
            deaths[c['team']] += int(c['metrics']['deaths'])
        print(f"{x['map']:22s} {x['side']} s{x['seed']} m={x['margin']:6d} tributed {sub[us]:5d}/{sub[them]:5d} "
              f"collected {col[us]:5d}/{col[them]:5d} deaths {deaths[us]:3d}/{deaths[them]:3d} "
              f"rounds {s['match']['roundsCompleted']} {x['folder'].rsplit('/', 1)[-1]}")


if __name__ == '__main__':
    main()
