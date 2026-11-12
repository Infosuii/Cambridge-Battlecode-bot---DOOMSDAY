"""Compact per-game metrics for new v117 ladder matches + aggregate loss mechanisms."""
from pathlib import Path
import sys, json, gzip, collections
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import ladder_loss_analysis as L
from project import save

def series(t):
    out = []; rd = 0
    for run in t['runs']: out.append((rd, float(run['value']))); rd += run['duration']
    return out
def at(s, rd):
    v = 0.0
    for a, b in s:
        if a <= rd: v = b
    return v

rows = []
for m in json.load(open(HERE / 'matches.json')):
    p = HERE / 'matches' / m['matchId'] / 'native.json.gz'
    if not p.exists(): continue
    n = json.load(gzip.open(p, 'rt', encoding='utf-8'))
    o = L.own(m); us = 'team' + o['side'].upper(); them = 'teamB' if us == 'teamA' else 'teamA'
    tt = {(t['owner'], t['metric']): series(t) for t in n['teamTimelines']}
    ct = collections.defaultdict(list)
    for t in n['championTimelines']: ct[(t['owner']['team'], t['metric'])].append(series(t))
    R = n['match']['roundsCompleted']
    def team(metric, team, rd): return sum(at(s, rd) for s in ct[(team, metric)])
    fuel = lambda team: sum(len(e['entries']) for e in n['events'] if e['kind'] == 'fuelExhausted' and e['owner'].get('team') == team)
    row = {'id': m['matchId'], 'kind': m['kind'], 'opp': L.rival(m).get('name'), 'map': m['map'],
           'side': o['side'], 'result': o['result'], 'rounds': R,
           'bank': [at(tt[(us, 'submittedGems')], R), at(tt[(them, 'submittedGems')], R)],
           'held_end': [team('gems', us, R), team('gems', them, R)],
           'collected': [team('collectedGems', us, R), team('collectedGems', them, R)],
           'deaths': [team('deaths', us, R), team('deaths', them, R)],
           'gold350': [team('earnedGold', us, 350), team('earnedGold', them, 350)],
           'col350': [team('collectedGems', us, 350), team('collectedGems', them, 350)],
           'fuel': [fuel(us), fuel(them)], 'faults': n['diagnostics']['botFaults'][us]}
    rows.append(row)
save(HERE / 'games.json', rows)
loss = [r for r in rows if r['result'] == 'loss']; win = [r for r in rows if r['result'] == 'win']
print('games', len(rows), 'W', len(win), 'L', len(loss), 'kinds', collections.Counter((r['kind'], r['result']) for r in rows))
by = collections.defaultdict(lambda: [0, 0])
for r in rows: by[r['opp']][0 if r['result'] == 'win' else 1] += 1
print('by opp', dict(by))
med = lambda xs: sorted(xs)[len(xs) // 2] if xs else None
for name, rs in (('loss', loss), ('win', win)):
    print(name, 'median collected gap', med([r['collected'][0] - r['collected'][1] for r in rs]), 'death gap', med([r['deaths'][0] - r['deaths'][1] for r in rs]),
          'gold350 gap', med([r['gold350'][0] - r['gold350'][1] for r in rs]), 'col350 gap', med([r['col350'][0] - r['col350'][1] for r in rs]))
cls = collections.Counter()
for r in loss:
    if r['held_end'][0] >= r['bank'][1] - r['bank'][0] and r['held_end'][0] > 0: cls['bag_would_cover'] += 1
    if r['collected'][0] >= r['collected'][1]: cls['outcollected_but_lost'] += 1
    if r['deaths'][0] - r['deaths'][1] >= 4: cls['died_4plus_more'] += 1
    if r['col350'][0] - r['col350'][1] <= -50: cls['early_economy_-50'] += 1
    if r['rounds'] >= 1999: cls['round_cap'] += 1
print('loss classes', dict(cls))
mp = collections.defaultdict(lambda: [0, 0])
for r in rows: mp[r['map']][0 if r['result'] == 'win' else 1] += 1
print('worst maps', sorted(mp.items(), key=lambda kv: kv[1][0] - kv[1][1])[:14])
print('faults', sum(r['faults'] for r in rows), 'our fuel/game', round(sum(r['fuel'][0] for r in rows) / max(1, len(rows)), 2))
