"""Paired uncontested/contested comparison focused on the carry: Vesper's gold share and team gold, same map/side cells.

Usage: carry_compare.py CAND_RUN BASE_RUN [--mark 250]
Only cells where both arms drafted Vesper count for the share; team totals use all common cells. Values at the mark.
"""
import argparse
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from curves import ROOT, at, first_reach  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('cand')
ap.add_argument('base')
ap.add_argument('--mark', type=int, default=250)
a = ap.parse_args()


def load(run):
    out = {}
    for g in json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']:
        s = json.loads((ROOT / g['folder'] / 'summary.json').read_text())
        tm = 'team' + g['side'].upper()
        per = {tl['owner']['name']: at(tl['runs'], a.mark) for tl in s['championTimelines']
               if tl['metric'] == 'earnedGold' and tl['owner']['team'] == tm}
        gems = sum(at(tl['runs'], a.mark) for tl in s['championTimelines']
                   if tl['metric'] == 'collectedGems' and tl['owner']['team'] == tm)
        sub = [t for t in s['teamTimelines'] if t['metric'] == 'submittedGems' and t['owner'] == tm][0]['runs']
        out[(g['map'], g['side'])] = dict(per=per, gold=sum(per.values()), gems=gems, win=g['win'], margin=g['margin'],
                                          reach=first_reach(sub, 1000) or 2000)
    return out


c, b = load(a.cand), load(a.base)
keys = sorted(set(c) & set(b))
ves = [k for k in keys if 'Vesper Vale' in c[k]['per'] and 'Vesper Vale' in b[k]['per']]
share = lambda r: r['per']['Vesper Vale'] / max(1, r['gold'])
print(f'{a.cand} vs {a.base} at R{a.mark}: {len(keys)} cells, {len(ves)} with Vesper in both')
for name, ks in (('all', keys), ('vesper', ves)):
    if not ks:
        continue
    dg = [c[k]['gold'] - b[k]['gold'] for k in ks]
    dm = [c[k]['gems'] - b[k]['gems'] for k in ks]
    dr = [c[k]['reach'] - b[k]['reach'] for k in ks]
    print(f'  {name:6s} n{len(ks):3d} team gold {st.mean(b[k]["gold"] for k in ks):6.0f} -> {st.mean(c[k]["gold"] for k in ks):6.0f}'
          f' ({st.mean(dg):+.0f}), gems {st.mean(dm):+.1f}, reach1000 {st.mean(dr):+.1f} rounds,'
          f' wins {sum(c[k]["win"] for k in ks)}/{sum(b[k]["win"] for k in ks)}, margin {st.mean(c[k]["margin"] - b[k]["margin"] for k in ks):+.1f}')
if ves:
    print(f'  Vesper share {st.mean(share(b[k]) for k in ves):.2f} -> {st.mean(share(c[k]) for k in ves):.2f}')
