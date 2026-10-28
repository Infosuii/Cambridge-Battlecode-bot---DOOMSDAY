"""Our deaths to camps in a run: per map/side, count and the killer camp kind, plus our champion and the round.

Usage: c_camp_deaths.py RUN [--min 1.0]
"""
import argparse
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('--min', type=float, default=1.0)
    a = ap.parse_args()
    seen = set()
    per = collections.defaultdict(lambda: [0, collections.Counter(), collections.Counter(), []])
    for g in json.loads((ROOT / 'artifacts/evaluations/v67' / a.run / 'games.json').read_text())['games']:
        key = (g['map'], g['side'], g['seed'])
        if key in seen:
            continue
        seen.add(key)
        s = json.loads((ROOT / g['folder'] / 'summary.json').read_text())
        us = 'teamA' if g['side'] == 'a' else 'teamB'
        p = per[(g['map'], g['side'])]
        p[0] += 1
        for e in s['events']:
            if e['kind'] != 'death' or e['owner'].get('team') != us:
                continue
            for x in e['entries']:
                if x.get('context') == 'champion':
                    continue
                p[1][x.get('context')] += 1
                p[2][e['owner'].get('name')] += 1
                p[3].append(x['timestamp']['round'])
    rows = sorted(per.items(), key=lambda kv: -sum(kv[1][1].values()) / kv[1][0])
    total = sum(sum(v[1].values()) for v in per.values())
    games = sum(v[0] for v in per.values())
    print(f'camp deaths per game overall: {total / games:.2f}')
    for (m, side), (n, ctx, who, rounds) in rows:
        k = sum(ctx.values()) / n
        if k < a.min:
            break
        rounds.sort()
        print(f'{m:24s} {side} {k:5.1f}/game  by {dict(ctx)}  victims {dict(who.most_common(3))}  '
              f'rounds p10/50/90 {rounds[len(rounds) // 10]}/{rounds[len(rounds) // 2]}/{rounds[9 * len(rounds) // 10]}')


if __name__ == '__main__':
    main()
