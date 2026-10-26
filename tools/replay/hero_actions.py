"""Per-hero action use in ladder games from fight_review.mjs output: ours vs the opponent's same hero, losses and wins.

Usage: python tools/replay/hero_actions.py <fights.json> [listing.json] [--summaries <root>]
inReach = rounds starting with an enemy champion in basic-attack reach; acted = a PvP attack or cast that round.
With --summaries, champion damage per PvP action uses each game's native championDamageDone.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

T = ['Ryth', 'Vesper', 'Vendetta', 'Cassi', 'Issac', 'Stellar', 'Prism', 'Marcella', 'Willow', 'Ren', 'Varg', 'Tavi', 'Heart']
NAMES = {'Vesper Vale': 'Vesper', 'Heart of Ruin': 'Heart'}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('fights')
    ap.add_argument('listing', nargs='?', default='data/ladder/v58_since_live.json')
    ap.add_argument('--summaries', default='artifacts/local-only/v58-ladder')
    a = ap.parse_args()
    listing = {g['matchId']: g for g in json.load(open(a.listing, encoding='utf8'))}
    agg = defaultdict(lambda: defaultdict(float))
    for f in json.load(open(a.fights, encoding='utf8')):
        g = listing.get(f['id'])
        if not g:
            continue
        us = next(t for t in g['teams'] if t['name'] == 'DOOMSDAY')
        k = 0 if us['side'] == 'a' else 1
        res = 'win' if us['result'] == 'win' else 'loss'
        dmg = {}
        sp = Path(a.summaries) / f['id'] / 'summary.json'
        if sp.exists():
            s = json.loads(sp.read_text(encoding='utf8'))
            for c in s['champions']:
                dmg[(0 if c['team'] == 'teamA' else 1, NAMES.get(c['name'], c['name']))] = float(c['metrics']['championDamageDone'])
        for hk, h in f['heroes'].items():
            team, typ = map(int, hk.split(':'))
            side = 'us' if team == k else 'them'
            row = agg[(res, T[typ], side)]
            row['games'] += 1
            for key, v in h.items():
                row[key] += v
            row['dmg'] += dmg.get((team, T[typ]), 0.0)
    for res in ['loss', 'win']:
        print(f'===== {res.upper()}')
        print(f'{"hero":9} {"side":4} {"games":>5} {"contact/g":>9} {"inReach/g":>9} {"acted%":>7} {"pvpAtk/g":>8} {"pvpCast/g":>9} {"casts/alive":>11} {"dmg/pvpAct":>10}')
        for hero in ['Vesper', 'Marcella', 'Vendetta', 'Heart', 'Varg', 'Ren', 'Ryth', 'Willow', 'Tavi']:
            for side in ['us', 'them']:
                r = agg.get((res, hero, side))
                if not r or r['games'] < 5:
                    continue
                n = r['games']
                acts = r['pvpAtk'] + r['pvpCast']
                print(f'{hero:9} {side:4} {int(n):5} {r["contact"] / n:9.1f} {r["inReach"] / n:9.1f} {100 * r["inReachActed"] / max(1, r["inReach"]):6.1f}% '
                      f'{r["pvpAtk"] / n:8.1f} {r["pvpCast"] / n:9.1f} {r["casts"] / max(1, r["alive"]):11.3f} {r["dmg"] / max(1, acts):10.1f}')


if __name__ == '__main__':
    main()
