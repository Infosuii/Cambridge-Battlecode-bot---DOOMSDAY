"""One game, champion by champion, in windows of N rounds (timeline.json from tools/v67/c_timeline.mjs).

Usage: c_rounds.py GAME_DIR [--us 1] [--window 50] [--until 600] [--side us|them|both]
Per window: alive share, start->end position, tiles walked, camp hits, champion hits, casts, recalls, gold gained,
deaths, items held at the end, nearest enemy distance (median) and allies within 4 (median).
"""
import argparse
import json
from pathlib import Path
import statistics as st

NAMES = 'ryth vesper vendetta cassi issac stellar prism marcella willow ren varg tavi heart'.split()


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('game')
    ap.add_argument('--us', type=int, default=1)
    ap.add_argument('--window', type=int, default=50)
    ap.add_argument('--until', type=int, default=600)
    ap.add_argument('--side', default='us')
    a = ap.parse_args()
    tl = json.load(open(Path(a.game) / 'timeline.json'))
    team = {c['id']: c['team'] for c in tl['champs']}
    typ = {c['id']: NAMES[c['type']] for c in tl['champs']}
    camps = {(c['x'], c['y']) for c in tl['camps']}
    frames = [f for f in tl['frames'] if f[0] <= a.until]
    sides = {'us': [a.us], 'them': [1 - a.us], 'both': [a.us, 1 - a.us]}[a.side]
    for t in sides:
        print(f'## {"us" if t == a.us else "them"}')
        for cid in [c['id'] for c in tl['champs'] if c['team'] == t]:
            print(f'  {typ[cid]} (id {cid})')
            for w0 in range(0, a.until, a.window):
                W = [f for f in frames if w0 <= f[0] < w0 + a.window]
                if not W:
                    continue
                rows = [next(x for x in f[1] if x[0] == cid) for f in W]
                alive = [r for r in rows if r[5]]
                walked = sum(cheb((r1[1], r1[2]), (r2[1], r2[2])) for r1, r2 in zip(rows, rows[1:]) if r1[5] and r2[5])
                acts = [a_ for r in rows for a_ in (r[9] if len(r) > 9 else [])]
                camp_hits = sum(1 for k in acts if k[0] in (5, 6) and (k[1], k[2]) in camps)
                champ_hits = 0
                for f, r in zip(W, rows):
                    foes = {(x[1], x[2]) for x in f[1] if team[x[0]] != t and x[5]}
                    champ_hits += sum(1 for k in (r[9] if len(r) > 9 else []) if k[0] in (5, 6) and (k[1], k[2]) in foes)
                casts = sum(1 for k in acts if k[0] == 6)
                recalls = sum(1 for k in acts if k[0] == 11)
                deaths = sum(1 for r1, r2 in zip(rows, rows[1:]) if r1[5] and not r2[5])
                gold = sum(max(0, r2[6] - r1[6]) for r1, r2 in zip(rows, rows[1:]))
                ne, al = [], []
                for f, r in zip(W, rows):
                    if not r[5]:
                        continue
                    foes = [cheb((r[1], r[2]), (x[1], x[2])) for x in f[1] if team[x[0]] != t and x[5]]
                    if foes:
                        ne.append(min(foes))
                    al.append(sum(1 for x in f[1] if team[x[0]] == t and x[0] != cid and x[5] and cheb((r[1], r[2]), (x[1], x[2])) <= 4))
                s0 = next((r for r in rows if r[5]), rows[0])
                print(f'    R{w0:4d}-{w0 + a.window - 1:4d} alive {len(alive):2d}/{len(rows)} ({s0[1]:2d},{s0[2]:2d})->({rows[-1][1]:2d},{rows[-1][2]:2d}) '
                      f'walk {walked:3d} camp {camp_hits:2d} champ {champ_hits:2d} cast {casts:2d} rec {recalls:2d} gold +{gold:4d} '
                      f'died {deaths} items {rows[-1][8]:2d} hp {rows[-1][3]:4d}/{rows[-1][4]:4d} enemy {st.median(ne) if ne else "-":>4} allies4 {st.median(al) if al else "-"}')


if __name__ == '__main__':
    main()
