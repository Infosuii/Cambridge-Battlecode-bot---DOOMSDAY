"""Collection gap over time (ladder): collected gems, monster damage, earned gold and deaths per team at rounds
50 / 100 / 150 / 200 / 300, ours / theirs, median over losses and over wins.
  python research/x3/banking/collect_gap.py [ROUNDS e.g. 300,500,700,900] data/ladder/x1c1 data/ladder/v92"""
import json, sys, statistics as st
from pathlib import Path

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

T = tuple(int(x) for x in (sys.argv.pop(1).split(",") if sys.argv[1][0].isdigit() else "50,100,150,200,300".split(",")))
MET = tuple(sys.argv.pop(1).split(',')) if not Path(sys.argv[1]).exists() else ('collectedGems', 'monsterDamageDone', 'earnedGold', 'deaths', 'championDamageDone')
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
        them = 'teamB' if us[0] == 'teamA' else 'teamA'
        v = {}
        for side, tag in ((us[0], 'us'), (them, 'them')):
            for mt in MET:
                for t in T:
                    v[tag, mt, t] = sum(at(series(tl['runs']), t) for tl in s['championTimelines']
                                        if tl['owner']['team'] == side and tl['metric'] == mt)
        rows.append((us[1], s['match']['roundsCompleted'], v))
for res in ('loss', 'win'):
    g = [r for r in rows if (r[0] == 'win') == (res == 'win')]
    print(f'{res}: {len(g)} games, median rounds {st.median(r[1] for r in g)}')
    for mt in MET:
        print(f'  {mt:20s}', '  '.join(f'r{t}: {st.median(r[2]["us", mt, t] for r in g):6.0f} / '
                                       f'{st.median(r[2]["them", mt, t] for r in g):6.0f}' for t in T))
