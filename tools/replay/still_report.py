"""Classify stationary no-attack stretches (still_runs.mjs output) by context, ours vs opponents (offline analysis).

Usage: python tools/replay/still_report.py <still.json> [ledger.json]
Categories (first match): fuel stall (engine fuel-exhausted turns in the run), enemy within 6, capture (on a dead camp
tile, run <= 6), respawn wait (within 1 of a dead camp tile), staging next to an awake/alive camp (within 5), other.
"""
from collections import defaultdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ledger_report import load_meta, TYPES  # noqa: E402

CAMP = ['wolf', 'elk', 'gem', 'gold', 'monolith', 'golem']


def category(r):
    c = r['ctx']
    if r['fuel'] > 0:
        return 'fuel stall'
    if c['enemies'] > 0:
        return 'enemy within 6'
    if c['camp_dist'] == 0 and not c['camp_alive'] and r['len'] <= 6:
        return 'capture'
    if c['camp_dist'] <= 1 and not c['camp_alive']:
        return 'respawn wait at dead camp'
    if c['camp_alive'] and c['camp_dist'] <= 5:
        return 'beside live camp, not attacking'
    return 'other'


def main():
    still = json.loads(Path(sys.argv[1]).read_text())
    meta, latest, tids = load_meta()
    latest_ids = {m['matchId'] for m in latest}
    agg = {k: defaultdict(lambda: [0, 0]) for k in ['v53 losses', 'v53 wins', 'pure-economy losses']}
    pure = {'a3e51d17-9947-4049-a32a-cc04af7eefcf', '8c0ac9b6-7b22-41ea-8c6d-a62f9c1e4d96'}
    detail = defaultdict(list)
    for g in still:
        m = meta.get(g['id'])
        if not m or 'DOOMSDAY' not in [t['name'] for t in m['teams']]:
            continue
        if g['id'] not in latest_ids and g['id'] not in tids:
            continue
        me = next(t for t in m['teams'] if t['name'] == 'DOOMSDAY')
        us = 'ab'.index(me['side'])
        cohort = 'v53 wins' if me['result'] == 'win' else 'v53 losses'
        # Team of an actor: indices below the first opponent index are team 0 (draft order); use the ledger convention.
        n0 = len(m['teams'][0]['draftPicks']) + (1 if 3 in m['teams'][0]['draftPicks'] else 0)
        for r in g['runs']:
            team = 0 if r['actor'] < n0 else 1
            side = 0 if team == us else 1
            cat = category(r)
            agg[cohort][cat][side] += r['len']
            if g['id'] in pure:
                agg['pure-economy losses'][cat][side] += r['len']
                if side == 0 and r['len'] >= 8:
                    detail[g['id']].append((r['start'], TYPES[r['type']], r['len'], cat, r['ctx']))
    for k, d in agg.items():
        print(f'## {k}: stationary no-attack champion-rounds by R500, us / opponent')
        for cat, (a, b) in sorted(d.items(), key=lambda x: -x[1][0]):
            print(f'  {cat:34s} {a:6d} {b:6d}')
    for gid, rows in detail.items():
        print('\n#', gid, meta[gid]['map'])
        for row in sorted(rows)[:40]:
            print('  ', row)


if __name__ == '__main__':
    main()
