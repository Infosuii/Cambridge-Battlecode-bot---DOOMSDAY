"""Champion time use over the opening, per map: share of champion-rounds dead, at home, idle (no action, away from
home), walking only, hitting camps, hitting champions, banking. Ours from local runs (our side), theirs from the
opponents in ladder losses (research/v75/ranked_v67.json, the other side), so top-ish play is compared on the same map.

Usage: c_activity.py MAP [MAP...] --local RUN [--until 500]
"""
import argparse
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def tally(tl, team_of_interest, until, out):
    team = {c['id']: c['team'] for c in tl['champs']}
    camps = {(c['x'], c['y']) for c in tl['camps']}
    spawn = collections.defaultdict(list)
    for row in tl['frames'][0][1]:
        spawn[team[row[0]]].append((row[1], row[2]))
    for rnd, rows, _ in tl['frames']:
        if rnd > until:
            break
        pos = {r[0]: (r[1], r[2]) for r in rows if r[5]}
        for r in rows:
            if team[r[0]] != team_of_interest:
                continue
            out['n'] += 1
            if not r[5]:
                out['dead'] += 1
                continue
            p = (r[1], r[2])
            acts = r[9] if len(r) > 9 else []
            kinds = {a[0] for a in acts}
            enemy_tiles = {pos[q] for q in pos if team[q] != team_of_interest}
            hit_champ = any(a[0] in (5, 6) and (a[1], a[2]) in enemy_tiles for a in acts)
            hit_camp = any(a[0] in (5, 6) and (a[1], a[2]) in camps and (a[1], a[2]) not in enemy_tiles for a in acts)
            if min(cheb(p, s) for s in spawn[team_of_interest]) <= 1:
                out['home'] += 1
            elif hit_champ:
                out['pvp'] += 1
            elif hit_camp:
                out['camp'] += 1
            elif kinds & {12, 18}:
                out['bank'] += 1
            elif kinds & {11}:
                out['recall'] += 1
            elif kinds & {4, 23}:
                out['walk'] += 1
            else:
                out['idle'] += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('maps', nargs='+')
    ap.add_argument('--local', required=True)
    ap.add_argument('--until', type=int, default=500)
    a = ap.parse_args()
    ladder = json.loads((ROOT / 'research/v75/ranked_v67.json').read_text(encoding='utf-8'))
    games = json.loads((ROOT / 'artifacts/evaluations/v67' / a.local / 'games.json').read_text())['games']
    keys = ['dead', 'home', 'idle', 'walk', 'camp', 'pvp', 'bank', 'recall']
    print('map'.ljust(22) + 'who'.ljust(10) + ''.join(k.rjust(8) for k in keys) + '   n')
    for mp in a.maps:
        ours, theirs, mine_ladder = collections.Counter(), collections.Counter(), collections.Counter()
        for g in games:
            if g['map'].replace('-', '_') != mp:
                continue
            f = ROOT / g['folder'] / 'timeline.json'
            if f.exists():
                tally(json.loads(f.read_text()), 0 if g['side'] == 'a' else 1, a.until, ours)
        for r in ladder:
            f = ROOT / 'artifacts/local-only/v67-ranked' / r['matchId'] / 'timeline.json'
            if r['map'] != mp or not f.exists():
                continue
            tl = json.loads(f.read_text())
            us = 0 if r['side'] == 'a' else 1
            tally(tl, 1 - us, a.until, theirs)
            tally(tl, us, a.until, mine_ladder)
        for who, c in (('v74 local', ours), ('v67 ladder', mine_ladder), ('opponents', theirs)):
            if c['n']:
                print(mp[:22].ljust(22) + who.ljust(10) + ''.join(f"{c[k] / c['n']:8.2f}" for k in keys) + f"   {c['n']}")


if __name__ == '__main__':
    main()


def pooled(index, folder, until=500):
    """Both teams of every game in a downloaded index, all maps pooled: returns (ours, theirs) counters."""
    ours, theirs = collections.Counter(), collections.Counter()
    for r in json.loads((ROOT / index).read_text(encoding='utf-8')):
        f = ROOT / folder / r['matchId'] / 'timeline.json'
        if not f.exists():
            continue
        tl = json.loads(f.read_text())
        us = 0 if r['side'] == 'a' else 1
        tally(tl, us, until, ours)
        tally(tl, 1 - us, until, theirs)
    return ours, theirs
