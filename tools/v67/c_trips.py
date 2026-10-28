"""Home trips per champion from timelines: arrivals on the own spawn after being at least 8 tiles away, split by the
health fraction on the last turn away (>= 0.6: a shopping trip, below: a health retreat), with the gold held then and
the turns spent away from the previous working spot. Both teams of the same games.

Usage: c_trips.py INDEX.json|local:RUN [--only loss|win|all]
"""
import argparse
import collections
import json
from pathlib import Path
import statistics as st
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/v67'))
from c_forensics import cheb  # noqa: E402


def rows_of(index, only):
    if index.startswith('local:'):
        games = json.loads((ROOT / 'artifacts/evaluations/v67' / index[6:] / 'games.json').read_text())['games']
        seen, out = set(), []
        for g in games:
            if (g['map'], g['side'], g['seed']) in seen:
                continue
            seen.add((g['map'], g['side'], g['seed']))
            out.append(dict(path=ROOT / g['folder'] / 'timeline.json', side=g['side'], result='win' if g['win'] else 'loss'))
    else:
        out = [dict(path=ROOT / 'artifacts/local-only/v67-ranked' / r['matchId'] / 'timeline.json', side=r['side'], result=r['result'])
               for r in json.loads((ROOT / index).read_text(encoding='utf-8'))]
    return [r for r in out if (only == 'all' or r['result'] == only) and r['path'].exists()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('index')
    ap.add_argument('--only', default='loss')
    a = ap.parse_args()
    stats = {k: collections.Counter() for k in ('us', 'them')}
    gold = {k: [] for k in ('us', 'them')}
    games = 0
    for r in rows_of(a.index, a.only):
        tl = json.loads(r['path'].read_text())
        team = {c['id']: c['team'] for c in tl['champs']}
        us = 0 if r['side'] == 'a' else 1
        spawn = collections.defaultdict(list)
        for row in tl['frames'][0][1]:
            spawn[team[row[0]]].append((row[1], row[2]))
        games += 1
        far = {}
        for rnd, rows, _ in tl['frames']:
            for row in rows:
                cid, x, y, hp, mhp, alive, g = row[:7]
                t = team[cid]
                k = 'us' if t == us else 'them'
                if not alive:
                    far.pop(cid, None)
                    continue
                d = min(cheb((x, y), s) for s in spawn[t])
                if d >= 8:
                    far[cid] = (hp / max(1, mhp), g)
                elif d <= 1 and cid in far:
                    frac, g0 = far.pop(cid)
                    if frac >= 0.6:
                        stats[k]['shop_trips'] += 1
                        gold[k].append(g0)
                    else:
                        stats[k]['hp_trips'] += 1
    for k in ('us', 'them'):
        print(f"{k}: per game shopping trips {stats[k]['shop_trips'] / games:.1f}, health trips {stats[k]['hp_trips'] / games:.1f}; "
              f"gold held on a shopping trip median {st.median(gold[k]) if gold[k] else 0:.0f}")
    print(games, 'games')


if __name__ == '__main__':
    main()
