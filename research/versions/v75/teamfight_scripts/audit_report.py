"""Report exact-turn spell opportunities and camp capture throughput. Uses audit500.json.

Usage: audit_report.py INDEX FOLDER [--result loss|win]. Range is geometric;
does not claim every ground/dash tile is legal. Recalls may be cancelled first.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('index')
p.add_argument('folder')
p.add_argument('--result', default='loss')
a = p.parse_args()
rows = [r for r in json.loads(Path(a.index).read_text()) if r['result'] == a.result]
S, F = defaultdict(Counter), defaultdict(Counter)
examples = []
for r in rows:
    d = json.loads((Path(a.folder) / r['matchId'] / 'audit500.json').read_text())
    us = 0 if r['side'] == 'a' else 1
    side = lambda t: 'us' if t == us else 'them'
    groups = d['groups']
    tile_group = {(c['x'], c['y']): gi for gi, g in enumerate(groups) for c in g['camps']}
    hits = defaultdict(Counter)
    for t in d['turns']:
        sh = side(t['team'])
        touched = {tile_group[tuple(act[1:3])] for act in t['acts']
                   if act[0] in (5, 6) and tuple(act[1:3]) in tile_group}
        for gi in touched:
            hits[(t['round'], gi)][t['team']] += 1
            F[sh]['hits'] += 1
            F[(sh, groups[gi]['camps'][0]['type'])]['hits'] += 1
        if t['nd'] > 4 or t['round'] >= 300:
            continue
        kit = d['kits'][str(t['type'])]
        for k in (S[sh], S[(sh, t['type'])]):
            k['n'] += 1
            cast = any(x[0] == 6 for x in t['acts'])
            k['cast'] += cast
            k['move_no_cast'] += any(x[0] == 4 for x in t['acts']) and not cast
            k['recall'] += bool(t['state'] & 2)
            reset_ready = any(sp and sp['type'] == 1 and t['cds'][s] == 0 for s, sp in enumerate(kit))
            dash_ready = any(sp and sp['type'] == 6 and t['cds'][s] == 0 for s, sp in enumerate(kit))
            k['reset_after_hit'] += reset_ready and not dash_ready and not cast and any(x[0] == 5 for x in t['acts'])
            hostile = [s for s, sp in enumerate(kit) if sp and
                       (sp.get('target', 0) & 2 or (sp['type'] == 6 and sp.get('modifier', 0) > 0))]
            ready = [s for s in hostile if t['cds'][s] == 0]
            inrange = [s for s in ready if t['nd'] <= kit[s].get('range', 0) +
                       (kit[s].get('radius', 0) if kit[s]['type'] in (3, 6) else 0)]
            k['offensive'] += bool(hostile)
            k['ready'] += bool(ready)
            k['inrange'] += bool(inrange)
            k['unused'] += bool(inrange) and not cast
            k['unused_can_cast'] += bool(inrange) and not cast and bool(t['state'] & (1 << 11))
            k['miss_walk'] += bool(inrange) and not cast and any(x[0] == 4 for x in t['acts'])
            k['camp_cd'] += bool(hostile) and not ready and any(
                t['recent'][s] and t['recent'][s][1] == 'camp' and t['round'] - t['recent'][s][0] <= 8
                for s in hostile)
    cycle_hits = defaultdict(Counter)
    clear = {}
    for prev, nxt in zip(d['frames'], d['frames'][1:]):
        rnd = prev[0]
        for gi, g in enumerate(groups):
            cycle_hits[gi].update(hits[(rnd, gi)])
            pg, ng = prev[2][gi], nxt[2][gi]
            if not pg['rewardAvailable'] and ng['rewardAvailable']:
                clear[gi] = rnd
            if pg['rewardAvailable'] and not ng['rewardAvailable']:
                winner = pg['captureTeam']
                if winner not in (0, 1):
                    F['unknown']['captures'] += 1
                else:
                    sh = side(winner)
                    for k in (F[sh], F[(sh, g['camps'][0]['type'])]):
                        k['captures'] += 1
                        k['base_gold'] += g['gold']
                        k['gems'] += g['gems']
                        k['capture_delay'] += rnd - clear.get(gi, rnd)
                        k['own_hits_converted'] += cycle_hits[gi][winner]
                        k['opponent_hits_stolen'] += cycle_hits[gi][1-winner]
                    P, N = {x[0]: x for x in prev[1]}, {x[0]: x for x in nxt[1]}
                    rise = sum(max(0, N[c][5]-P[c][5]) for c in P if P[c][1] == winner)
                    F[sh]['gold_on_capture_round'] += rise
                cycle_hits[gi].clear()

names = 'ryth vesper vendetta cassi issac stellar prism marcella willow ren varg tavi heart'.split()
print(len(rows), a.result, 'games; spells before R300, farming before R500')
for sh in ('us', 'them'):
    for typ in [None, *range(13)]:
        k = S[sh if typ is None else (sh, typ)]
        if not k['n']:
            continue
        n = k['n']
        print(f'{sh:4} {"all" if typ is None else names[typ]:9} n={n:6} cast={k["cast"]/n:5.1%} '
              f'off-ready={k["ready"]/n:5.1%} ready-inrange={k["inrange"]/n:5.1%} '
              f'unused={k["unused"]/n:5.1%} unused-walk={k["miss_walk"]/n:5.1%} '
              f'unused-can-cast={k["unused_can_cast"]/n:5.1%} '
              f'camp-cd={k["camp_cd"]/n:5.1%} recalling={k["recall"]/n:5.1%}')
        if k['reset_after_hit']:
            print(f'     unused reset after a basic hit, no ready dash: {k["reset_after_hit"]} ({k["reset_after_hit"]/n:.1%})')
print('Farming: base capture gold excludes item/champion bonuses; unconverted hits include unfinished, stolen and denied clears.')
for sh in ('us', 'them'):
    for typ in [None, *sorted({key[1] for key in F if isinstance(key, tuple)})]:
        k = F[sh if typ is None else (sh, typ)]
        if not k['hits']:
            continue
        print(f'{sh:4} camp={str(typ):4} hits={k["hits"]:6} captures={k["captures"]:5} '
              f'base-gold/hit={k["base_gold"]/k["hits"]:.3f} '
              f'base-gold/game={k["base_gold"]/len(rows):.1f} '
              f'converted-hits={k["own_hits_converted"]/k["hits"]:.1%} '
              f'capture-delay={k["capture_delay"]/max(1,k["captures"]):.1f} '
              f'gold-on-cap-round={k["gold_on_capture_round"]/max(1,k["base_gold"]):.2f}x')
print('Unattributed capture transitions', F['unknown']['captures'])
