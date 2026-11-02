"""Report on unranked match groups vs other teams: data/ladder/x1/groups/<group>/NN-<match>.zip + summaries2/<match>.json.
Sides follow the order the groups were created with (--sides a,b,a,b,a). Prints per game and per opponent."""
import json, glob, os, sys, collections
GROUPS = 'data/ladder/x1/groups'; SUMS = 'data/ladder/x1/summaries2'
SIDES = 'abab a'.replace(' ', '')
names = {}
for f in glob.glob(f'{GROUPS}/create_*.json'):
    names[json.load(open(f)).get('id')] = os.path.basename(f)[7:-5]
def at(tl, owner, metric, r):
    for t in tl:
        if t['owner'] == owner and t['metric'] == metric:
            n = 0
            for run in t['runs']:
                n += run['duration']
                if n > r: return int(float(run['value']))
            return int(float(t['runs'][-1]['value']))
    return None
tot = collections.defaultdict(list)
metrics = set()
for g in sorted(d for d in glob.glob(f'{GROUPS}/*') if os.path.isdir(d)):
    gid = os.path.basename(g); g += '/'
    for z in sorted(glob.glob(g + '0*.zip')):
        i = int(os.path.basename(z)[:2]); mid = os.path.basename(z)[3:-4]
        s = json.load(open(f'{SUMS}/{mid}.json')); m = s['match']
        us = 'team' + SIDES[i - 1].upper(); them = 'teamB' if us == 'teamA' else 'teamA'
        tl = s['teamTimelines']; metrics |= {t['metric'] for t in tl}
        draft = {t: [c['name'] for c in sorted(s['roster']['champions'], key=lambda c: c['draftPick']) if c['team'] == t] for t in (us, them)}
        win = m['outcome'] == us
        opp = next((c.get('teamName') for c in []), None) or gid[:8]
        b = lambda t, r: at(tl, t, 'submittedGems', r)
        tot[gid].append((win, b(us,250), b(them,250), b(us,500), b(them,500), m['roundsCompleted'], b(us,9999), b(them,9999)))
        if '-v' in sys.argv: print(f"{gid[:8]} g{i} {us[-1]} {'W' if win else 'L'} R{m['roundsCompleted']:4d} banked {b(us,9999)}-{b(them,9999)} "
              f"R250 {b(us,250)}-{b(them,250)} R500 {b(us,500)}-{b(them,500)} us {','.join(draft[us])} them {','.join(draft[them])}")


TEAM = {'77f40880': '#1 Intercontinental Fish', '19e093d0': '#2 Univardisty of Shingtonwash', '68ec01f7': '#3 Mite',
        '1c07cbb3': '#4 newer team', '1686b13f': '#5 Ad Astra', '9dade66b': '#33 QS2isLaw', 'f6bebc8e': '#50 0xDEADBEEF'}
print(f"{'opponent':32s} W/N  R250 us-them  R500 us-them  end round  final us-them")
allr = []
for g, rows in tot.items():
    allr += rows; n = len(rows); av = lambda k: sum(r[k] for r in rows) / n
    print(f"{TEAM.get(g[:8], g[:8]):32s} {sum(r[0] for r in rows)}/{n}  {av(1):4.0f}-{av(2):4.0f}     {av(3):4.0f}-{av(4):4.0f}     {av(5):5.0f}      {av(6):4.0f}-{av(7):4.0f}")
n = len(allr); av = lambda k: sum(r[k] for r in allr) / n
print(f"{'all':32s} {sum(r[0] for r in allr)}/{n}  {av(1):4.0f}-{av(2):4.0f}     {av(3):4.0f}-{av(4):4.0f}     {av(5):5.0f}      {av(6):4.0f}-{av(7):4.0f}")
