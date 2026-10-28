"""List deaths (round, champion, position, killer) for one game folder, both teams, in order.

Usage: c_deaths.py GAME_FOLDER [--until ROUND]
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder')
    ap.add_argument('--until', type=int, default=10**9)
    a = ap.parse_args()
    s = json.loads((ROOT / a.folder / 'summary.json').read_text())
    rows = []
    for e in s['events']:
        if e['kind'] != 'kill':
            continue
        killer = e['owner']
        for x in e['entries']:
            t = x['target']
            if t.get('kind') != 'champion':
                continue
            rows.append((x['timestamp']['round'], t['team'], t['name'], x['x'], x['y'], killer['team'], killer['name']))
    for e in s['events']:
        if e['kind'] != 'death':
            continue
        for x in e['entries']:
            if x.get('context') not in (None, '0') or True:
                pass
    print('spawns/draft:', [(c['team'], c['champion']) for c in s['roster']['draft']])
    for r in sorted(rows):
        if r[0] <= a.until:
            print(f'r{r[0]:5d} {r[1]} {r[2]:14s} died at ({r[3]:2d},{r[4]:2d}) by {r[5]} {r[6]}')


if __name__ == '__main__':
    main()
