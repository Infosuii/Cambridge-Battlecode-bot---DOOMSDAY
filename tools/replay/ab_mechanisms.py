"""Mechanism comparison for a paired ladder A/B: per-game deaths, kills, gold and gems lost on death, candidate vs v58,
on the same match-group sets (V59_LADDER_AB_PLAN.json).

Usage: python tools/replay/ab_mechanisms.py --cand-listing <json> --cand-root <dir> --since <ISO> [--until <ISO>]
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]


def stats(path, side):
    g = json.loads(path.read_text(encoding='utf8'))
    us = 'team' + side.upper()
    them = 'teamB' if us == 'teamA' else 'teamA'
    out = {}
    for label, team in [('us', us), ('them', them)]:
        cs = [c for c in g['champions'] if c['team'] == team]
        out[label] = dict(deaths=sum(float(c['metrics']['deaths']) for c in cs), kills=sum(float(c['metrics']['kills']) for c in cs),
                          gold=sum(float(c['metrics']['earnedGold']) for c in cs),
                          lost=sum(float(x['value']) for e in g['events'] if e['kind'] == 'gemLoss' and e['owner'].get('team') == team
                                   for x in e['entries'] if x['context'] == 'champion'))
    return out


def collect(listing, root, since, until, keys):
    rows = []
    for m in listing:
        if m['kind'] != 'unranked' or m['createdAt'] < since or (until and m['createdAt'] >= until):
            continue
        us = next(t for t in m['teams'] if t['name'] == 'DOOMSDAY')
        them = next(t for t in m['teams'] if t['name'] != 'DOOMSDAY')
        if (them['name'], m['map'], us['side']) not in keys:
            continue
        p = root / m['matchId'] / 'summary.json'
        if p.exists():
            s = stats(p, us['side'])
            s['win'] = us['result'] == 'win'
            rows.append(s)
    return rows


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--cand-listing', required=True)
    ap.add_argument('--cand-root', required=True)
    ap.add_argument('--since', required=True)
    ap.add_argument('--until')
    a = ap.parse_args()
    plan = json.loads((ROOT / 'research/v59/V59_LADDER_AB_PLAN.json').read_text(encoding='utf8'))['sets']
    keys = {(s['opponent'], mp, sd) for s in plan for mp, sd in zip(s['maps'], s['sides'])}
    base = collect(json.load(open(ROOT / 'data/ladder/v58_since_live.json', encoding='utf8')), ROOT / 'artifacts/local-only/v58-ladder',
                   '2026-10-26T13:31:14Z', None, keys)
    cand = collect(json.load(open(ROOT / a.cand_listing, encoding='utf8')), ROOT / a.cand_root, a.since, a.until, keys)
    m = lambda rows, f: statistics.fmean(f(r) for r in rows) if rows else float('nan')
    for name, rows in [('v58', base), ('candidate', cand)]:
        print(f"{name:9} games {len(rows):3} win {m(rows, lambda r: r['win']):.3f}  deaths {m(rows, lambda r: r['us']['deaths']):5.2f}/{m(rows, lambda r: r['them']['deaths']):5.2f}"
              f"  kills {m(rows, lambda r: r['us']['kills']):5.2f}/{m(rows, lambda r: r['them']['kills']):5.2f}"
              f"  gold {m(rows, lambda r: r['us']['gold']):6.0f}/{m(rows, lambda r: r['them']['gold']):6.0f}"
              f"  gems lost on death {m(rows, lambda r: r['us']['lost']):6.1f}/{m(rows, lambda r: r['them']['lost']):6.1f}")


if __name__ == '__main__':
    main()
