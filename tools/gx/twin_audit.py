"""Count coupled deaths and lost bags with authoritative paired event timestamps."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

TWIN={'Cassi','Issac'}


def read(p):
    d=json.loads(p.read_text())
    team='team'+p.parent.name[-1]
    bodies={r['id']:r['name'] for r in d['roster']['champions'] if r['team']==team}
    twin={k for k,v in bodies.items() if v in TWIN}
    loss=Counter()
    pairs=defaultdict(dict)
    for e in d['events']:
        who=e['owner']
        if who.get('team')!=team or who.get('id') not in twin:
            continue
        for row in e['entries']:
            t=row['timestamp']
            if e['kind']=='gemLoss':
                loss[t['input'],who['id']]+=int(row['value'])
            elif e['kind']=='death':
                pairs[t['input']][who['id']]=row
    out=Counter(games=1,with_twins=len(twin)==2,rounds=d['match']['roundsStarted'],
        twin_body_rounds=len(twin)*d['match']['roundsStarted'],
        non_twin_body_rounds=(len(bodies)-len(twin))*d['match']['roundsStarted'])
    examples=[]
    for clock, victims in pairs.items():
        if len(victims)!=2:
            out['unpaired_death_records']+=len(victims)
            continue
        out['incidents']+=1
        a,b=sorted(victims,key=lambda k:victims[k]['timestamp']['ordinal'])
        u,v=victims[a],victims[b]
        x,y=loss[clock,a],loss[clock,b]
        source=u.get('context','unknown')
        if source!=v.get('context'):
            source='mixed'
        if not all(isinstance(row.get(k),int) for row in (u,v) for k in ('x','y')):
            raise ValueError((p,clock))
        distance=max(abs(u['x']-v['x']),abs(u['y']-v['y']))
        out[source+'_incidents']+=1
        out[source+'_gems_lost']+=x+y
        out[source+'_max_bag_ge25']+=max(x,y)>=25
        out[source+'_split_ge6']+=distance>=6
        out[source+'_split_ge10']+=distance>=10
        out[source+'_split_ge6_bag_ge25']+=distance>=6 and max(x,y)>=25
        if distance>=6 and max(x,y)>=40:
            examples.append(dict(cell=p.parent.name,round=u['timestamp']['round'],cause=source,
                separation=distance,first=bodies[a],second=bodies[b],bags=[x,y]))
    return d['match']['outcome']==team,out,examples


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('scratch',type=Path)
    a=p.parse_args()
    results={}
    for o in ('v92','v86h','x1bru'):
        root=a.scratch/f'gx-base-pool-{o}'/'games'
        sums=defaultdict(Counter)
        examples=[]
        for f in sorted(root.glob('*/summary.json')):
            won,stats,cases=read(f)
            sums['all'].update(stats)
            sums['win' if won else 'nonwin'].update(stats)
            examples.extend(cases)
        if sums['all']['games']!=172: raise ValueError(root)
        results[o]=dict(sets=sums,examples=examples)
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    main()
