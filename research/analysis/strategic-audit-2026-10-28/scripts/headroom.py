"""Farming headroom: our uncontested local collection vs ladder contested collection, same maps.

Usage: headroom.py IDLE_ROWS.json TIMELINE_DATA.json [--out FILE]
IDLE_ROWS comes from curves.py on a run against bots/idle81. TIMELINE_DATA.json is the deep-analysis examined
set (research/deep-2026-10-28 on analysis/deep-2026-10-28; examined games only, no hands-off data).
Prints per-mark means over maps present in both, and per-map rows sorted by the opponent's contested lead.
"""
import argparse
import json
import statistics as st
from collections import defaultdict

ap = argparse.ArgumentParser()
ap.add_argument('idle')
ap.add_argument('timeline')
ap.add_argument('--out')
a = ap.parse_args()
norm = lambda m: m.replace('_', '-')
idle = defaultdict(list)
for r in json.load(open(a.idle)):
    idle[norm(r['map'])].append(r)
lad = defaultdict(list)
for r in json.load(open(a.timeline))['rows']:
    lad[norm(r['map'])].append(r)
maps = sorted(set(idle) & set(lad))
out = dict(maps=len(maps), marks={}, per_map=[])
for m in ('100', '250', '500'):
    keys = []
    for mp in maps:
        lr = [r for r in lad[mp] if m in r['curve']]
        if not lr:
            continue
        keys.append(dict(map=mp, idle=st.mean(r['us'][m]['collected'] for r in idle[mp]),
                         idle_gold=st.mean(r['us'][m]['gold'] for r in idle[mp]),
                         them=st.mean(r['curve'][m]['them']['collected'] for r in lr),
                         them_gold=st.mean(r['curve'][m]['them']['earned_gold'] for r in lr),
                         us=st.mean(r['curve'][m]['us']['collected'] for r in lr),
                         us_gold=st.mean(r['curve'][m]['us']['earned_gold'] for r in lr),
                         them_loss=st.mean([r['curve'][m]['them']['collected'] for r in lr if r['result'] == 'loss'] or [float('nan')]),
                         n=len(lr)))
    g = lambda k: st.mean(x[k] for x in keys)
    beat = sum(x['them'] > x['idle'] for x in keys)
    beat_gold = sum(x['them_gold'] > x['idle_gold'] for x in keys)
    out['marks'][m] = dict(maps=len(keys), idle=g('idle'), them_contested=g('them'), us_contested=g('us'),
                           idle_gold=g('idle_gold'), them_gold=g('them_gold'), us_gold=g('us_gold'),
                           maps_opp_contested_beats_our_uncontested=beat, maps_opp_gold_beats_idle=beat_gold)
    print(f"R{m}: {len(keys)} maps | collected gems: ours idle {g('idle'):.0f}, ours ladder {g('us'):.0f}, opp ladder {g('them'):.0f}"
          f" | opp contested > our uncontested on {beat} maps | gold: idle {g('idle_gold'):.0f} ladder us {g('us_gold'):.0f} opp {g('them_gold'):.0f}"
          f" (opp>idle on {beat_gold})")
    if m == '500':
        for x in sorted(keys, key=lambda x: x['idle'] - x['them']):
            out['per_map'].append(x)
if a.out:
    json.dump(out, open(a.out, 'w'), indent=1)
print('worst maps at R500 (idle - opp contested):')
for x in out['per_map'][:15]:
    print(f"  {x['map']:24s} n{x['n']:3d} idle {x['idle']:6.0f} opp {x['them']:6.0f} us {x['us']:6.0f}  gold idle {x['idle_gold']:5.0f} opp {x['them_gold']:5.0f}")
