"""Compare early team resources on the same layout and side."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from statistics import median


def until(series, at):
    for r in series['runs']:
        at -= r['duration']
        if at < 0:
            return int(r['value'])
    return int(series['runs'][-1]['value']) if series['runs'] else 0


def read(path, rounds):
    d = json.loads(path.read_text())
    me = 'team'+path.parent.name[-1]
    enemy = 'team'+('B' if me=='teamA' else 'A')
    roster = tuple(x['champion'] for x in d['roster']['draft'] if x['team']==me)
    teams = {t:Counter() for t in (me,enemy)}
    per_champion = {t:Counter() for t in teams}
    first_camp = {t:rounds+1 for t in teams}
    first_emblem = {t:rounds+1 for t in teams}
    for row in d['championTimelines']:
        t = row['owner']['team']
        if t in teams and row['metric']=='earnedGold':
            n = until(row,rounds)
            teams[t]['earned_gold'] += n
            per_champion[t][row['owner']['id']] = n
    for t in teams:
        gold = per_champion[t]
        teams[t]['max_earned_gold'] = max(gold.values(),default=0)
        teams[t]['bodies_gold_150'] = sum(n>=150 for n in gold.values())
    for row in d['events']:
        t = row['owner'].get('team')
        if t not in teams:
            continue
        out = teams[t]
        kind = row['kind']
        for e in row['entries']:
            r = e['timestamp']['round']
            if r>rounds:
                continue
            if kind=='gemCollection' and e.get('context')=='campGroup':
                out['camp_gems'] += int(e['value'])
                out['camp_captures'] += 1
                first_camp[t] = min(r,first_camp[t])
            elif kind=='gemSubmission':
                out['banked'] += int(e['value'])
            elif kind=='itemCombination':
                out['emblems'] += 1
                first_emblem[t] = min(r,first_emblem[t])
            elif kind=='death':
                out['champion_deaths' if e.get('context')=='champion' else 'other_deaths'] += 1
            elif kind=='fuelExhausted':
                out['fuel_outs'] += 1
    for t,c in teams.items():
        c['first_camp_within_horizon'] = first_camp[t]<=rounds
        c['first_emblem_within_horizon'] = first_emblem[t]<=rounds
        c['first_camp_or_horizon_plus_one'] = first_camp[t]
        c['first_emblem_or_horizon_plus_one'] = first_emblem[t]
    game = d['match']
    return (game['engineBuildHash'],game['mapHash'],game['seed']),roster,teams[me],teams[enemy],game['outcome']==me


def compare(base, test, rounds, subset):
    files = {f.parent.name:f for f in base.glob('games/*/summary.json')}
    other = {f.parent.name:f for f in test.glob('games/*/summary.json')}
    if subset:
        files = {k:v for k,v in files.items() if k in other}
    if not files or files.keys()!=other.keys():
        raise ValueError(f'Mismatched match cells: {base.name}, {test.name}')
    strata = defaultdict(list)
    for key,p in sorted(files.items()):
        a,b = read(p,rounds),read(other[key],rounds)
        if a[0]!=b[0]:
            raise ValueError((key,a[0],b[0]))
        row = {'cell':key,'roster_change':a[1]!=b[1],
               'base_roster':a[1],'candidate_roster':b[1],
               'base_won':a[-1],'candidate_won':b[-1],
               'base_ours':dict(a[2]),'ours':dict(b[2]),
               'base_enemy':dict(a[3]),'enemy':dict(b[3])}
        strata['all'].append(row)
        strata['changed_roster' if row['roster_change'] else 'same_roster'].append(row)
    return {name:describe(rows) for name,rows in strata.items()},strata['all']


def describe(rows):
    res={'games':len(rows),'base_wins':sum(x['base_won'] for x in rows),
         'candidate_wins':sum(x['candidate_won'] for x in rows)}
    for our,theirs in [('ours','base_ours'),('enemy','base_enemy')]:
        keys=sorted({k for row in rows for label in (our,theirs) for k in row[label]})
        out={}
        for k in keys:
            b=[x[theirs].get(k,0) for x in rows]
            c=[x[our].get(k,0) for x in rows]
            delta=[x-y for x,y in zip(c,b)]
            out[k]={'base_mean':round(sum(b)/len(b),4),'candidate_mean':round(sum(c)/len(c),4),
                    'median_paired_delta':median(delta),'higher':sum(x>0 for x in delta),
                    'lower':sum(x<0 for x in delta)}
        res[our]=out
    return res


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('base',type=Path)
    p.add_argument('candidate',type=Path)
    p.add_argument('--rounds',type=int,default=150)
    p.add_argument('--subset',action='store_true')
    p.add_argument('--cells',action='store_true')
    a=p.parse_args()
    data,rows=compare(a.base,a.candidate,a.rounds,a.subset)
    output=dict(base=a.base.name,candidate=a.candidate.name,rounds=a.rounds,strata=data)
    if a.cells:
        output['cells']=rows
    print(json.dumps(output,indent=2))


if __name__=='__main__':
    main()
