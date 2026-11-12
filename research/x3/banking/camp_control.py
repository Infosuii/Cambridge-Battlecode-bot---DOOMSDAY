"""Camp clears by side and territory in ladder games: how many camps each team clears, when, and how many of the
opponent's clears are on our side of the map (closer to the centroid of our own clears than to theirs).
  python research/x3/banking/camp_control.py data/ladder/x1c1 data/ladder/v92"""
import json, sys, statistics as st
from pathlib import Path

seen, rows = set(), []
for d in map(Path, sys.argv[1:]):
    mf = next((p for p in sorted(d.glob('matches_*.json')) if 'raw' not in p.name and 'all' not in p.name), None)
    matches = {m['matchId']: m for m in json.load(open(mf))} if mf else {}
    for f in sorted(((d / 'summaries') if (d / 'summaries').is_dir() else (d.parent / 'summaries')).glob('*.json')):
        m = matches.get(f.stem)
        if not m or f.stem in seen: continue
        us = next((('team' + t['side'].upper(), t['result']) for t in m['teams'] if t['name'] == 'DOOMSDAY'), None)
        if not us: continue
        seen.add(f.stem)
        s = json.load(open(f, encoding='utf-8'))
        clears = {'us': [], 'them': []}
        for e in s['events']:
            if e['kind'] != 'campClear': continue
            tag = 'us' if e['owner']['team'] == us[0] else 'them'
            for x in e['entries']: clears[tag].append((x['timestamp']['round'], x['x'], x['y']))
        rows.append((us[1], m['map'], clears))
def cen(c): return (st.mean(x for _, x, _ in c), st.mean(y for _, _, y in c)) if c else None
for res in ('loss', 'win'):
    g = [r for r in rows if (r[0] == 'win') == (res == 'win')]
    for lo, hi in ((0, 300), (300, 600), (600, 900), (900, 2000)):
        u = st.mean(sum(lo <= t < hi for t, _, _ in r[2]['us']) for r in g)
        th = st.mean(sum(lo <= t < hi for t, _, _ in r[2]['them']) for r in g)
        print(f'{res:4s} rounds {lo:4d}-{hi:4d}: camp clears us {u:5.1f}  them {th:5.1f}')
    inv_us = inv_them = n = 0
    for _, _, c in g:
        cu, ct = cen(c['us']), cen(c['them'])
        if not cu or not ct: continue
        d2 = lambda p, q: (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
        inv_them += sum(d2((x, y), cu) < d2((x, y), ct) for _, x, y in c['them'])
        inv_us += sum(d2((x, y), ct) < d2((x, y), cu) for _, x, y in c['us']); n += 1
    print(f'{res}: per game, their clears nearer our centroid {inv_them / n:.1f}; ours nearer theirs {inv_us / n:.1f}')
