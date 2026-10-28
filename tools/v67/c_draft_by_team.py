"""Top-vs-top draft statistics from a meta crawl's matches.json: per team, games, win rate, and how often each
champion is picked; and the win rate of a pick split by the team that made it.

Usage: c_draft_by_team.py artifacts/local-only/meta/20261027 [--pick 3]
Pick ids follow bc::champion_draft: 0 ryth, 1 vesper, 2 vendetta, 3 cassi_and_issac, 4 stellar, 5 prism,
6 marcella, 7 tavi, 8 willow, 9 ren, 10 varg, 11 heart.
"""
import argparse
import collections
import json
from pathlib import Path

NAMES = ['ryth', 'vesper', 'vendetta', 'C&I', 'stellar', 'prism', 'marcella', 'tavi', 'willow', 'ren', 'varg', 'heart']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('crawl')
    ap.add_argument('--pick', type=int, default=3)
    a = ap.parse_args()
    rows = json.loads((Path(a.crawl) / 'matches.json').read_text(encoding='utf-8-sig'))
    team = collections.defaultdict(lambda: {'g': 0, 'w': 0, 'picks': collections.Counter(), 'pg': 0, 'pw': 0})
    for m in rows:
        if m.get('status') != 'finished' or len(m['teams']) != 2:
            continue
        for t in m['teams']:
            s = team[t['name']]
            s['g'] += 1
            win = t['result'] == 'win'
            s['w'] += win
            picks = t.get('draftPicks') or []
            for p in picks:
                s['picks'][p] += 1
            if a.pick in picks:
                s['pg'] += 1
                s['pw'] += win
    print(f"{'team':34s} {'games':>5s} {'win':>5s}  {NAMES[a.pick]}: games win   top picks")
    for name, s in sorted(team.items(), key=lambda kv: -kv[1]['w'] / max(1, kv[1]['g'])):
        top = ', '.join(f'{NAMES[p]} {c / s["g"]:.2f}' for p, c in s['picks'].most_common(5))
        pw = f"{s['pg']:5d} {s['pw'] / s['pg']:.2f}" if s['pg'] else '    0    -'
        print(f"{name:34s} {s['g']:5d} {s['w'] / s['g']:.2f}  {pw}   {top}")


if __name__ == '__main__':
    main()
