"""Leave-one-map-out test of deterministic draft rules on the saved v70 draft league (no new games).

Usage: lomo_draft.py [--out data/lomo_draft.json]
Data: research/v70/draft_table_league.json names the base and option runs (6 lineups x 4 opponents x 70 maps, already
played for v70). gain(map, lineup) = mean over opponents of (option margin - base margin) on that map.
Each policy picks a lineup for a held-out map using only the other 69 maps, then scores the held-out map's realised
gain. 'oracle' picks with the held-out map's own data: an in-sample upper bound, biased upward by selection noise.
Features are what a draft can compute (area, aspect, team size) plus one proxy for resource density measured on the
base run (total gems collected by both teams per game), marked as such.
"""
import argparse
import collections
import json
import math
import random
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EV = ROOT / 'artifacts/evaluations/v67'
ap = argparse.ArgumentParser()
ap.add_argument('--out', default='research/strategic-audit-2026-10-28/data/lomo_draft.json')
a = ap.parse_args()


def per_map(run):
    out = collections.defaultdict(list)
    for g in json.loads((EV / run / 'games.json').read_text())['games']:
        out[g['map']].append(g['margin'])
    return {m: st.mean(v) for m, v in out.items()}


lg = json.loads((ROOT / 'research/v70/draft_table_league.json').read_text())
base = {b.split('=')[0]: per_map(b.split('=')[1]) for b in lg['base']}
opts = collections.defaultdict(dict)
for o in lg['options']:
    spec, run = o.split('=')
    li, opp = spec.split(':')
    opts[int(li)][opp] = per_map(run)
maps = sorted(set.intersection(*(set(v) for v in base.values())))
L = sorted(opts)
gain = {m: {li: st.mean(opts[li][o][m] - base[o][m] for o in base) for li in L} for m in maps}

keys = {k.replace('_', '-'): v for k, v in json.loads((ROOT / 'research/proxy/map_keys.json').read_text()).items()}
dens = collections.defaultdict(list)  # base-run proxy: total gems collected by both teams per game
for g in json.loads((EV / 'g01-v69/games.json').read_text())['games']:
    s = json.loads((ROOT / g['folder'] / 'summary.json').read_text())
    dens[g['map']].append(sum(float(tl['runs'][-1]['value']) for tl in s['teamTimelines'] if tl['metric'] == 'submittedGems'))
feat = {}
for m in maps:
    k = keys[m]
    feat[m] = (math.log(k['width'] * k['height']), k['width'] / k['height'], k['size'], math.log(1 + st.mean(dens[m])))
sd = [st.pstdev(feat[m][i] for m in maps) or 1.0 for i in range(4)]


def dist(x, y, size_weight=3.0):
    w = (1.0, 0.5, size_weight, 1.0)
    return math.sqrt(sum(w[i] * ((feat[x][i] - feat[y][i]) / sd[i]) ** 2 for i in range(4)))


def pick_global(train):
    return max(L, key=lambda li: st.mean(gain[m][li] for m in train))


def pick_size(train, m):
    same = [t for t in train if keys[t]['size'] == keys[m]['size']] or train
    return pick_global(same)


def pick_knn(train, m, k=7, floor=50.0):
    nb = sorted(train, key=lambda t: dist(m, t))[:k]
    best = max(L, key=lambda li: st.mean(gain[t][li] for t in nb))
    return best if st.mean(gain[t][best] for t in nb) > floor else None


def pick_guard(train, m, k=7):
    """kNN, but only when the chosen lineup also beats base on the majority of neighbours (robustness guard)."""
    nb = sorted(train, key=lambda t: dist(m, t))[:k]
    best = max(L, key=lambda li: st.mean(gain[t][li] for t in nb))
    return best if sum(gain[t][best] > 0 for t in nb) >= (k + 1) // 2 + 1 else None


pol = collections.defaultdict(dict)
for m in maps:
    train = [t for t in maps if t != m]
    pol['base'][m] = None
    pol['global'][m] = pick_global(train)
    pol['by_size'][m] = pick_size(train, m)
    pol['knn7'][m] = pick_knn(train, m)
    pol['knn7_guard'][m] = pick_guard(train, m)
    pol['oracle_in_sample'][m] = max(L, key=lambda li: gain[m][li])
res = {}
rng = random.Random(1)
for name, choice in pol.items():
    g = [gain[m][choice[m]] if choice[m] is not None else 0.0 for m in maps]
    boot = sorted(st.mean(rng.choice(g) for _ in g) for _ in range(2000))
    res[name] = dict(mean_gain=round(st.mean(g), 1), ci95=[round(boot[50], 1), round(boot[1950], 1)],
                     changed_maps=sum(c is not None for c in choice.values()),
                     worse_than_base_maps=sum(1 for x in g if x < 0))
    print(f'{name:18s} mean gain {st.mean(g):+7.1f} gems/game  95% [{boot[50]:+.1f},{boot[1950]:+.1f}]  '
          f'maps changed {res[name]["changed_maps"]:2d}  maps worse {res[name]["worse_than_base_maps"]:2d}')
print('per-lineup mean gain over all maps:', {li: round(st.mean(gain[m][li] for m in maps), 1) for li in L})
out = ROOT / a.out
out.write_text(json.dumps(dict(note=__doc__, lineups=L, results=res, gain=gain,
                               features={m: feat[m] for m in maps}), indent=1))
print('->', out.relative_to(ROOT))
