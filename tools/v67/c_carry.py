"""Carry-economy mechanisms for our side of a run: per hero, earned gold at R250/R500, deaths, kills, and Bruiser
shards bought by R300. Top-team reference (research/v58/V58_CLAUDUS_FINDINGS.md): Claudus Vesper 466 capture gold at
R250; Fish Vesper 36 strength shards by R192.

Usage: c_carry.py RUN [RUN ...]
"""
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def value_at(runs, r):
    at, value = 0, 0.0
    for run in runs:
        if at > r:
            break
        value = float(run['value'])
        at += run['duration']
    return value


def main():
    for run in sys.argv[1:]:
        acc = collections.defaultdict(collections.Counter)
        seen = set()
        for g in json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']:
            key = (g['map'], g['side'], g['seed'])
            if key in seen:
                continue
            seen.add(key)
            s = json.loads((ROOT / g['folder'] / 'summary.json').read_text())
            us = 'teamA' if g['side'] == 'a' else 'teamB'
            ours = {c['id']: c['name'] for c in s['champions'] if c['team'] == us}
            for c in s['champions']:
                if c['team'] == us:
                    a = acc[c['name']]
                    a['n'] += 1
                    a['deaths'] += float(c['metrics']['deaths'])
                    a['kills'] += float(c['metrics']['kills'])
            for t in s['championTimelines']:
                cid = t['owner'].get('id')
                if t['metric'] == 'earnedGold' and t['owner'].get('team') == us and cid in ours:
                    acc[ours[cid]]['g250'] += value_at(t['runs'], 250)
                    acc[ours[cid]]['g500'] += value_at(t['runs'], 500)
            for e in s['events']:
                if e['kind'] != 'buyItem' or e['owner'].get('team') != us or e['owner'].get('id') not in ours:
                    continue
                for x in e['entries']:
                    if 'Bruiser' in x['target']['name'] and int(x['timestamp']['round']) <= 300:
                        acc[ours[e['owner']['id']]]['bru300'] += 1
        print(f'== {run} ({len(seen)} games)')
        print(f"   {'hero':16s} {'n':>4s} {'gold@250':>9s} {'gold@500':>9s} {'deaths':>7s} {'kills':>6s} {'bruiser<=300':>13s}")
        for name, a in sorted(acc.items(), key=lambda kv: -kv[1]['n']):
            n = a['n']
            print(f"   {name:16s} {n:4d} {a['g250'] / n:9.0f} {a['g500'] / n:9.0f} {a['deaths'] / n:7.1f} {a['kills'] / n:6.1f} "
                  f"{a['bru300'] / n:13.1f}")


if __name__ == '__main__':
    main()
