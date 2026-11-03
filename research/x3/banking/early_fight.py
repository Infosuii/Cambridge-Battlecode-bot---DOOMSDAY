"""Early fights vs result in ladder games: deaths per side by round 40 / 80 / 120 and the outcome.
  python research/x3/banking/early_fight.py data/ladder/x1c1 data/ladder/v92"""
import json, sys
from pathlib import Path
from collections import defaultdict

def series(runs):
    out, t = [], 0
    for r in runs:
        out.append((t, float(r['value']))); t += r['duration']
    return out

def at(ser, t):
    v = 0.0
    for s, x in ser:
        if s > t: break
        v = x
    return v

seen, rows = set(), []
for d in map(Path, sys.argv[1:]):
    mf = next((p for p in [d / 'matches_x1c1.json', d / 'matches_v92.json'] if p.exists()), None)
    matches = {m['matchId']: m for m in json.load(open(mf))} if mf else {}
    for f in sorted((d / 'summaries').glob('*.json')):
        m = matches.get(f.stem)
        if not m or f.stem in seen: continue
        us = next((('team' + t['side'].upper(), t['result']) for t in m['teams'] if t['name'] == 'DOOMSDAY'), None)
        if not us: continue
        seen.add(f.stem)
        s = json.load(open(f, encoding='utf-8'))
        dd = {}
        for side in ('teamA', 'teamB'):
            for T in (40, 80, 120, 200):
                dd[side, T] = sum(at(series(tl['runs']), T) for tl in s['championTimelines']
                                  if tl['owner']['team'] == side and tl['metric'] == 'deaths')
        them = 'teamB' if us[0] == 'teamA' else 'teamA'
        rows.append(dict(map=m['map'], res=us[1], **{f'd{T}': dd[us[0], T] - dd[them, T] for T in (40, 80, 120, 200)},
                         **{f'u{T}': dd[us[0], T] for T in (40, 80, 120, 200)}))
print(len(rows), 'games;', sum(r['res'] == 'win' for r in rows), 'wins')
for T in (40, 80, 120, 200):
    b = defaultdict(lambda: [0, 0])
    for r in rows:
        k = 'behind' if r[f'd{T}'] > 0 else 'level' if r[f'd{T}'] == 0 else 'ahead'
        b[k][0] += r['res'] == 'win'; b[k][1] += 1
    print(f'deaths by round {T}:', ', '.join(f'{k} {w}/{n} won' for k, (w, n) in sorted(b.items())))
lost_behind = [r for r in rows if r['res'] != 'win' and r['d80'] > 0]
print('losses behind on deaths by round 80:', len(lost_behind), 'of', sum(r['res'] != 'win' for r in rows))
