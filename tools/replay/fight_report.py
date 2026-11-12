"""Summarise fight_review.mjs output for ladder games: our side vs the opponent, in losses and in wins.

Usage: python tools/replay/fight_report.py <fights.json> [listing.json]
"""
from collections import Counter, defaultdict
import json
import statistics
import sys

TYPES = {0: 'Ryth', 1: 'Vesper', 2: 'Vendetta', 3: 'Cassi', 4: 'Issac', 5: 'Stellar', 6: 'Prism', 7: 'Marcella', 8: 'Willow',
         9: 'Ren', 10: 'Varg', 11: 'Tavi', 12: 'Heart'}  # bc::champion_type order


def m(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.fmean(xs), 3) if xs else None


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    fights = json.load(open(sys.argv[1], encoding='utf8'))
    listing = {g['matchId']: g for g in json.load(open(sys.argv[2] if len(sys.argv) > 2 else 'data/ladder/v58_since_live.json', encoding='utf8'))}
    groups = defaultdict(list)
    for f in fights:
        g = listing.get(f['id'])
        if not g:
            continue
        us = next(t for t in g['teams'] if t['name'] == 'DOOMSDAY')
        k = 0 if us['side'] == 'a' else 1
        groups['win' if us['result'] == 'win' else 'loss'].append((f, k, g))
    for label in ['loss', 'win']:
        sel = groups[label]
        print(f'\n===== {label.upper()} ({len(sel)})')
        for who, idx in [('us', lambda k: k), ('them', lambda k: 1 - k)]:
            ts = [f['teams'][idx(k)] for f, k, g in sel]
            c = [t['contact'] for t in ts]
            print(f'  {who:4} contact/game {m(c)}  act-rate {m([t["contactActs"] / max(1, t["contact"]) for t in ts])}'
                  f'  outnumbered {m([t["outnumbered"] / max(1, t["contact"]) for t in ts])}  alone {m([t["alone"] / max(1, t["contact"]) for t in ts])}'
                  f'  hp-lost/contact {m([t["contactHpLost"] / max(1, t["contact"]) for t in ts])}  mean-hp {m([t["contactHpFrac"] / max(1, t["contact"]) for t in ts])}'
                  f'  hurt-share {m([t["hurtContact"] / max(1, t["contact"]) for t in ts])}')
            for r in ['200', '400', '600', '800']:
                cv = [t['curve'].get(r) for t in ts if t['curve'].get(r)]
                print(f'      R{r}: items {m([x["shards"] for x in cv])} maxHp {m([x["maxHp"] for x in cv])} carried {m([x["carried"] for x in cv])} unspent {m([x["gold"] for x in cv])} dead {m([x["dead"] for x in cv])}')
            ds = [x for f, k, g in sel for x in f['deaths'] if x['team'] == idx(k)]
            n = len(sel)
            print(f'    deaths/game {round(len(ds) / n, 2)}: '
                  f'with bag>=40 {round(sum(x["gems"] >= 40 for x in ds) / n, 2)}  gems lost/game {round(sum(x["gems"] for x in ds) / n, 1)}'
                  f'  outnumbered(e8>a8+1) {m([x["enemies8"] > x["allies8"] + 1 for x in ds])}  alone(a8=0) {m([x["allies8"] == 0 for x in ds])}'
                  f'  no-pvp-in-last5 {m([x["pvp5"] == 0 for x in ds])}  hp5 {m([x["hp5"] for x in ds])}  powerRatio {m([min(5, x["powerRatio"]) for x in ds])}'
                  f'  no-enemy-within8 {m([x["enemies8"] == 0 for x in ds])}')
            byt = Counter(TYPES.get(x['type'], x['type']) for x in ds)
            print('    deaths by hero', byt.most_common())
            early = [x for x in ds if x['round'] < 300]
            print(f'    deaths before R300/game {round(len(early) / n, 2)}')


if __name__ == '__main__':
    main()
