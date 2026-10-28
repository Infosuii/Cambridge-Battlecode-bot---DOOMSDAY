"""Per champion type: our deaths, kills, gold and gems lost, in won vs lost games (distinct games only).

Usage: c_by_type.py RUN [RUN ...]
"""
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    acc = collections.defaultdict(lambda: collections.Counter())
    for run in sys.argv[1:]:
        seen = set()
        for g in json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']:
            key = (g['map'], g['side'], g['seed'])
            if key in seen:
                continue
            seen.add(key)
            s = json.loads((ROOT / g['folder'] / 'summary.json').read_text())
            us = 'teamA' if g['side'] == 'a' else 'teamB'
            res = 'win' if g['win'] else 'loss'
            for c in s['champions']:
                if c['team'] != us:
                    continue
                a = acc[(c['name'], res)]
                a['n'] += 1
                for m in ('deaths', 'kills', 'earnedGold', 'collectedGems', 'submittedGems'):
                    a[m] += float(c['metrics'][m])
                a['champDmg'] += float(c['metrics']['championDamageDone'])
                a['champTaken'] += float(c['metrics']['championDamageTaken'])
    print(f"{'champion':16s} {'res':4s} {'n':>4s} {'deaths':>6s} {'kills':>6s} {'gold':>6s} {'gems':>6s} {'banked':>6s} {'dmg':>7s} {'taken':>7s}")
    for (name, res), a in sorted(acc.items()):
        n = a['n']
        print(f"{name:16s} {res:4s} {n:4d} {a['deaths'] / n:6.1f} {a['kills'] / n:6.1f} {a['earnedGold'] / n:6.0f} "
              f"{a['collectedGems'] / n:6.0f} {a['submittedGems'] / n:6.0f} {a['champDmg'] / n:7.0f} {a['champTaken'] / n:7.0f}")


if __name__ == '__main__':
    main()
