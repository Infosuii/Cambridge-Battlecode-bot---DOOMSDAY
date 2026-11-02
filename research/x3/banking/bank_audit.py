"""Gem conversion audit from ladder summaries: where collected gems go (banked, lost on death, still carried at the
end), deposit sizes and timing, ours vs the opponent's, per game.
  python research/x3/banking/bank_audit.py data/ladder/x1c1 data/ladder/v92 > research/x3/banking/audit.txt"""
import json, os, sys, statistics as st
from pathlib import Path

def series(runs):
    out, t = [], 0
    for r in runs:
        out.append((t, float(r['value']))); t += r['duration']
    return out, t

def at(ser, t):
    v = 0.0
    for s, x in ser:
        if s > t: break
        v = x
    return v

def team_of(match, name='DOOMSDAY'):
    for tm in match['teams']:
        if tm['name'] == name: return 'team' + tm['side'].upper(), tm['result']
    return None, None

rows = []
for d in sys.argv[1:]:
    d = Path(d)
    mf = next((p for p in [d / 'matches_x1c1.json', d / 'matches_v92.json'] if p.exists()), None)
    matches = {m['matchId']: m for m in json.load(open(mf))} if mf else {}
    for f in sorted((d / 'summaries').glob('*.json')):
        mid = f.stem; m = matches.get(mid)
        if not m: continue
        us, res = team_of(m)
        if not us: continue
        s = json.load(open(f, encoding='utf-8'))
        rec = dict(src=d.name, match=mid, map=m['map'], res=res, rounds=s['match']['roundsCompleted'],
                   opp=[t['name'] for t in m['teams'] if t['name'] != 'DOOMSDAY'][0])
        for side, tag in [(us, 'us'), ('teamB' if us == 'teamA' else 'teamA', 'them')]:
            coll = sub = carried = lost = 0.0; deps = []; first_dep = None; bag_rounds = 0; deaths_w_gems = 0
            for tl in s['championTimelines']:
                if tl['owner']['team'] != side: continue
                ser, T = series(tl['runs'])
                if tl['metric'] == 'collectedGems': coll += ser[-1][1]
                if tl['metric'] == 'submittedGems':
                    sub += ser[-1][1]
                    prev = 0.0
                    for t, v in ser:
                        if v > prev: deps.append(v - prev); first_dep = t if first_dep is None else min(first_dep, t)
                        prev = v
                if tl['metric'] == 'gems':
                    carried += ser[-1][1]
                    prev = 0.0
                    for i, (t, v) in enumerate(ser):
                        if v >= 30: bag_rounds += (ser[i + 1][0] if i + 1 < len(ser) else T) - t
                        prev = v
            # gems lost on death: per champion, the carried bag in the run just before each death
            for tl in s['championTimelines']:
                if tl['owner']['team'] != side or tl['metric'] != 'deaths': continue
                g = next(x for x in s['championTimelines'] if x['owner'] == tl['owner'] and x['metric'] == 'gems')
                gser, _ = series(g['runs']); dser, _ = series(tl['runs']); prev = 0.0
                for t, v in dser:
                    if v > prev:
                        bag = at(gser, t - 1); lost += bag; deaths_w_gems += bag >= 10
                    prev = v
            rec.update({f'{tag}_coll': coll, f'{tag}_sub': sub, f'{tag}_end_carry': carried, f'{tag}_death_lost': lost,
                        f'{tag}_deps': len(deps), f'{tag}_dep_med': st.median(deps) if deps else 0,
                        f'{tag}_first_dep': first_dep if first_dep is not None else -1, f'{tag}_bag30_rounds': bag_rounds,
                        f'{tag}_deaths_w_gems': deaths_w_gems})
        rows.append(rec)

def pr(rs, label):
    if not rs: return
    def med(k): return st.median(r[k] for r in rs)
    def tot(k): return sum(r[k] for r in rs)
    print(f'## {label}: {len(rs)} games')
    for tag in ['us', 'them']:
        c = tot(f'{tag}_coll')
        print(f"  {tag:4s} collected {c:8.0f}  banked {tot(f'{tag}_sub') / c:5.1%}  lost on death {tot(f'{tag}_death_lost') / c:5.1%}  "
              f"carried at end {tot(f'{tag}_end_carry') / c:5.1%}  | deposits/game {med(f'{tag}_deps'):4.0f}  median deposit "
              f"{med(f'{tag}_dep_med'):4.0f}  first deposit round {med(f'{tag}_first_dep'):5.0f}  champ-rounds with bag>=30 "
              f"{med(f'{tag}_bag30_rounds'):5.0f}  deaths with bag>=10 {med(f'{tag}_deaths_w_gems'):3.0f}")

pr([r for r in rows if r['res'] == 'loss'], 'losses')
pr([r for r in rows if r['res'] == 'win'], 'wins')
print('\n## lowest-banking games (ours)')
for r in sorted(rows, key=lambda r: r['us_sub'] / max(1, r['us_coll']))[:15]:
    print(f"  {r['src']:5s} {r['map']:20s} {r['opp'][:14]:14s} {r['res']:4s} coll {r['us_coll']:5.0f} banked {r['us_sub']:5.0f} "
          f"death-lost {r['us_death_lost']:5.0f} end-carry {r['us_end_carry']:4.0f} deps {r['us_deps']:3d} first {r['us_first_dep']:5.0f} | "
          f"them coll {r['them_coll']:5.0f} banked {r['them_sub']:5.0f}")
json.dump(rows, open(Path(__file__).parent / 'audit.json', 'w'), indent=0)
