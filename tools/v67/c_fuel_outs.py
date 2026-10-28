"""Fuel-exhaustion events in one game: per champion, count, first and last round, and positions.

Usage: c_fuel_outs.py GAME_FOLDER
"""
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    s = json.loads((ROOT / sys.argv[1] / 'summary.json').read_text())
    rows = collections.defaultdict(list)
    for e in s['events']:
        if e['kind'] != 'fuelExhausted':
            continue
        o = e['owner']
        for x in e['entries']:
            rows[(o.get('team'), o.get('name'))].append((x['timestamp']['round'], x.get('x'), x.get('y')))
    for k, v in sorted(rows.items(), key=lambda kv: -len(kv[1])):
        v.sort()
        pos = collections.Counter((x, y) for _, x, y in v).most_common(3)
        print(f'{k[0]} {k[1]:14s} {len(v):4d} fuel-outs, rounds {v[0][0]}..{v[-1][0]}, positions {pos}')


if __name__ == '__main__':
    main()
