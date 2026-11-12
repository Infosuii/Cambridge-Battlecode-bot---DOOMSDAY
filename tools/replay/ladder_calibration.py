"""Opponent-adjusted ladder performance of each live version, to check what the local bench predicted.

Usage: python tools/replay/ladder_calibration.py --ladder data/ladder/ladder_20261026_p*.json
       --period v57=data/ladder/v57_games_20261026.json@2026-10-25T21:25:28Z..2026-10-26T13:31:14Z
       --period v58=data/ladder/v58_since_live.json@2026-10-26T13:31:14Z..
For each period: ranked record, the Elo-expected score against those opponents at our current rating, the residual
(actual - expected) with its binomial standard error, and the implied performance-rating offset. A local bench that
says one version is far stronger than another should show up here as a residual gap; v58 beat v57 64% locally
(+153 gems) yet its ladder residual was 4.7 points lower.
"""
import argparse
import glob
import json
import math

ME = 'fcf5f666-ea55-4da0-b8d4-97c64bb37236'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ladder', nargs='+', required=True)
    ap.add_argument('--period', action='append', required=True, help='name=listing.json@since..until (until optional)')
    a = ap.parse_args()
    rating = {}
    for pattern in a.ladder:
        for path in glob.glob(pattern):
            for t in json.load(open(path, encoding='utf8'))['teams']:
                rating[t['teamId']] = t['rating']
    ours = rating[ME]
    print(f'our current rating {ours:.0f}; {len(rating)} rated teams')
    for spec in a.period:
        name, rest = spec.split('=', 1)
        path, window = rest.split('@')
        since, until = window.split('..')
        games = [m for m in json.load(open(path, encoding='utf8')) if m['status'] == 'finished' and m['kind'] == 'ranked'
                 and all(t.get('engineVersion') == '2.0.0' for t in m['teams'])
                 and m['createdAt'] >= since and (not until or m['createdAt'] < until)]
        n = wins = 0
        expected = 0.0
        for m in games:
            us = next(t for t in m['teams'] if t['teamId'] == ME)
            them = next(t for t in m['teams'] if t['teamId'] != ME)
            if them['teamId'] not in rating:
                continue
            n += 1
            wins += us['result'] == 'win'
            expected += 1 / (1 + 10 ** ((rating[them['teamId']] - ours) / 400))
        if not n:
            print(f'{name}: no rated ranked games')
            continue
        score, exp = wins / n, expected / n
        se = math.sqrt(max(score * (1 - score), 1e-6) / n)
        clamp = min(max(score, 0.01), 0.99)
        offset = 400 * math.log10(clamp / (1 - clamp)) - 400 * math.log10(exp / (1 - exp))
        print(f'{name}: ranked {wins}/{n} = {score:.3f}; expected {exp:.3f}; residual {score - exp:+.3f} +/- {se:.3f}; '
              f'performance {offset:+.0f} Elo vs current rating')


if __name__ == '__main__':
    main()
