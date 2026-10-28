"""Opening comparison on one map: camp clears and gem collections in the first N rounds, ours (local runs) against
opponents (ladder loss summaries), with each team's spawn side normalised by reporting clears as (x, y, dist-from-own-
spawn). Usage: c_opening.py MAP [--rounds 300] [--local RUN ...]
"""
import argparse
import collections
import json
from pathlib import Path
import statistics as st

ROOT = Path(__file__).resolve().parents[2]


def clears(d, team, limit):
    out = []
    for e in d['events']:
        if e['kind'] != 'campClear' or e['owner'].get('team') != team:
            continue
        for x in e['entries']:
            if x['timestamp']['round'] <= limit:
                out.append((x['timestamp']['round'], x['x'], x['y'], e['owner'].get('name')))
    return sorted(out)


def gold_at(d, team, r):
    tot = 0.0
    for t in d['championTimelines']:
        if t['owner'].get('team') != team or t['metric'] != 'earnedGold':
            continue
        c = 0
        v = float(t['runs'][-1]['value']) if t['runs'] else 0
        for run in t['runs']:
            c += run['duration']
            if r < c:
                v = float(run['value'])
                break
        tot += v
    return tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('map')
    ap.add_argument('--rounds', type=int, default=300)
    ap.add_argument('--local', nargs='*', default=[])
    a = ap.parse_args()
    idx = json.loads((ROOT / 'research/v75/ranked_v67.json').read_text(encoding='utf-8'))
    allm = json.loads((ROOT / 'research/v75/matches_v67.json').read_text(encoding='utf-8'))
    sides = {m['matchId']: next(t['side'] for t in m['teams'] if t['name'] == 'DOOMSDAY') for m in allm}
    print(f'== ladder (v67 ranked) on {a.map}')
    for r in idx:
        if r['map'] != a.map:
            continue
        f = ROOT / 'artifacts/local-only/v67-ranked' / r['matchId'] / 'summary.json'
        if not f.exists():
            continue
        d = json.loads(f.read_text(encoding='utf-8'))
        us = 'teamA' if r['side'] == 'a' else 'teamB'
        them = 'teamB' if us == 'teamA' else 'teamA'
        roster = {t: [c['name'] for c in d['champions'] if c['team'] == t] for t in (us, them)}
        print(f"{r['result']} vs {r['opponent']} side {r['side']}: gold@200 {gold_at(d, us, 200):.0f}/{gold_at(d, them, 200):.0f} "
              f"@300 {gold_at(d, us, 300):.0f}/{gold_at(d, them, 300):.0f}")
        print('   us  ', roster[us], [(c[0], c[1], c[2]) for c in clears(d, us, a.rounds)])
        print('   them', roster[them], [(c[0], c[1], c[2]) for c in clears(d, them, a.rounds)])
    for run in a.local:
        games = json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']
        print(f'== local {run}')
        for g in games:
            if g['map'].replace('-', '_') != a.map:
                continue
            d = json.loads((ROOT / g['folder'] / 'summary.json').read_text())
            us = 'teamA' if g['side'] == 'a' else 'teamB'
            them = 'teamB' if us == 'teamA' else 'teamA'
            roster = {t: [c['name'] for c in d['champions'] if c['team'] == t] for t in (us, them)}
            print(f"{'win' if g['win'] else 'loss'} side {g['side']} seed {g['seed']}: gold@200 {gold_at(d, us, 200):.0f}/{gold_at(d, them, 200):.0f} "
                  f"@300 {gold_at(d, us, 300):.0f}/{gold_at(d, them, 300):.0f}")
            print('   us  ', roster[us], [(c[0], c[1], c[2]) for c in clears(d, us, a.rounds)])
            print('   them', roster[them], [(c[0], c[1], c[2]) for c in clears(d, them, a.rounds)])


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    main()
