"""How well do early-game differentials predict the result?

Usage: c_snowball.py RUN [RUN ...]
For checkpoints R, reports how often the side ahead on champion kills (and on gold earned) at R wins.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKS = (100, 150, 250, 400, 600)


def team_timeline(s, metric, team, r):
    total = 0
    for t in s['championTimelines']:
        if t['metric'] != metric or t['owner'].get('team') != team:
            continue
        at, value = 0, 0
        for run in t['runs']:
            if at > r:
                break
            value = float(run['value'])
            at += run['duration']
        total += value
    return total


def main():
    stats = defaultdict(lambda: [0, 0, 0])
    seen = set()
    for run in sys.argv[1:]:
        for g in json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']:
            key = (run, g['map'], g['side'], g['seed'])
            if key in seen:
                continue
            seen.add(key)
            s = json.loads((ROOT / g['folder'] / 'summary.json').read_text())
            us = 'teamA' if g['side'] == 'a' else 'teamB'
            them = 'teamB' if us == 'teamA' else 'teamA'
            for r in CHECKS:
                for metric in ('kills', 'earnedGold', 'collectedGems'):
                    d = team_timeline(s, metric, us, r) - team_timeline(s, metric, them, r)
                    st = stats[(metric, r)]
                    if abs(d) < (1 if metric == 'kills' else 20):
                        st[2] += 1
                    elif (d > 0) == g['win']:
                        st[0] += 1
                    else:
                        st[1] += 1
    print(f'{len(seen)} distinct games')
    for (metric, r), (agree, disagree, tie) in sorted(stats.items()):
        print(f'{metric:14s} R{r:4d}: leader wins {agree}/{agree + disagree} ({agree / max(1, agree + disagree):.2f}), ties {tie}')


if __name__ == '__main__':
    main()
