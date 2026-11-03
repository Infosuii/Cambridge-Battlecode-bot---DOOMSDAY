"""Winners vs us from the loss replays (research/x3/losses48/rows.json, tools/ladder/loss_study.py): territory,
invasion depth, grouping, first contact, opening route, recalls and gold, per map category and overall.
  python research/x3/losses48/replay_compare.py > research/x3/losses48/REPLAY_FINDINGS.md
"""
import json, statistics as st
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
rows = json.loads((ROOT / 'research/x3/losses48/rows.json').read_text(encoding='utf-8'))
cats = json.loads((ROOT / 'research/x3/atlas/categories.json').read_text())
PH = ['0-150', '150-400', '400-800', '800+']


def m(xs):
    xs = [x for x in xs if x is not None]
    return st.mean(xs) if xs else float('nan')


def feats(p):
    fc = p.get('first_contact') or {}
    route = p.get('route') or []
    return {
        **{f'own_half_{PH[i]}': (p['terr'][i] if p['terr'][i] is not None else None) for i in range(4)},
        **{f'deep_{PH[i]}': p['near_enemy_spawn'][i] for i in range(4)},
        **{f'grouped_{PH[i]}': p['grouped'][i] for i in range(4)},
        **{f'spread_{PH[i]}': p['spread'][i] for i in range(4)},
        'first_contact': fc.get('round'), 'contact_allies': fc.get('allies4'), 'contact_enemies': fc.get('enemies6'),
        'contact_own_side': (1.0 if fc.get('own_side') else 0.0) if fc else None, 'contact_hp': fc.get('hp'),
        'first_group_round': route[0]['round'] if route else None,
        'route3_own_side': (sum(1 for x in route[:3] if x['own_side']) / max(1, len(route[:3]))) if route else None,
        'route3_workers': m([x['workers'] for x in route[:3]]) if route else None,
        'route3_dist': m([x['dist_own'] for x in route[:3]]) if route else None,
        'workers_together': p.get('workers_together'),
        **{f'recalls_{PH[i]}': p['recalls'][i] for i in range(4)},
        **{f'gold_{r}': p['gold'].get(str(r), p['gold'].get(r)) for r in (100, 200, 400, 600)},
        **{f'clears_{PH[i]}': p['clears'][i] for i in range(4)},
    }


def table(rs, title):
    T = [feats(r['them']['profile']) for r in rs]; U = [feats(r['us']['profile']) for r in rs]
    out = [f'### {title} ({len(rs)} losses)', '', '| feature | winners | us |', '|---|---|---|']
    for k in T[0]:
        a, b = m([t[k] for t in T]), m([u[k] for u in U])
        out.append(f'| {k} | {a:.2f} | {b:.2f} |')
    return out + ['']


def main():
    lines = ['# Winners vs us from the loss replays (898 losses to teams rated >= 2000, 48 h)', '',
             'own_half = share of alive champion-rounds nearer the own spawn; deep = share within 10 tiles of the enemy '
             'spawn; grouped = share of champion-rounds with an ally within 4; spread = mean distance to the nearest ally; '
             'first_contact = first round a champion more than 4 tiles off its spawn has an enemy within 6 (allies within 4 '
             'counting itself, enemies within 6, own side = on its own half); route3 = the first three camp groups worked '
             '(own-side share, team members working them together, distance from spawn); recalls = jumps onto the own '
             'spawn; gold = team gold held at that round (not earned); clears by phase.', '']
    lines += table(rows, 'All categories')
    for c in sorted(set(cats.values()), key=lambda x: int(x[1:])):
        rs = [r for r in rows if cats.get(r['map'].replace('_', '-')) == c]
        if rs: lines += table(rs, c)
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
