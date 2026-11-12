"""Per-team totals for match-group games from the champion timelines (sum over each team's champions)."""
import json, glob, os
S = 'ababa'
TEAM = {'77f40880': 'Fish#1', '19e093d0': 'Univ#2', '68ec01f7': 'Mite#3', '1c07cbb3': 'newer#4', '1686b13f': 'AdAstra#5',
        '9dade66b': 'QS2isLaw', 'f6bebc8e': 'DEADBEEF'}
def at(t, r):
    n = 0
    for run in t['runs']:
        n += run['duration']
        if n > r: return float(run['value'])
    return float(t['runs'][-1]['value']) if t['runs'] else 0.0
print('opp       res banked     collected  kills   deaths  gold@R250  gold@R500  coll@R250')
for z in sorted(glob.glob('data/ladder/x1/groups/*/0*.zip')):
    i = int(os.path.basename(z)[:2]); mid = os.path.basename(z)[3:-4]
    s = json.load(open(f'data/ladder/x1/summaries2/{mid}.json')); us = 'team' + S[i - 1].upper(); them = 'teamB' if us == 'teamA' else 'teamA'
    agg = {}
    for t in s['championTimelines']:
        for r in (250, 500, 99999):
            k = (t['owner']['team'], t['metric'], r); agg[k] = agg.get(k, 0) + at(t, r)
    g = lambda tm, m, r=99999: int(agg.get((tm, m, r), 0))
    b = {t['team']: int(t['submittedGems']) for t in s['teams']}
    print(f"{TEAM[os.path.basename(os.path.dirname(z))[:8]]:9s} {'W' if s['match']['outcome']==us else 'L'}  {b[us]:4d}-{b[them]:4d}  {g(us,'collectedGems'):4d}-{g(them,'collectedGems'):4d} "
          f"{g(us,'kills'):3d}-{g(them,'kills'):3d}  {g(us,'deaths'):3d}-{g(them,'deaths'):3d}  {g(us,'earnedGold',250):4d}-{g(them,'earnedGold',250):4d}  {g(us,'earnedGold',500):4d}-{g(them,'earnedGold',500):4d}  {g(us,'collectedGems',250):3d}-{g(them,'collectedGems',250):3d}")
