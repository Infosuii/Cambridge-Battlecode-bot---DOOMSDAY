"""Compare specific events on each identical map, side and opponent."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path


def read(path, kind):
    d=json.loads(path.read_text())
    team='team'+path.parent.name[-1]
    match=d['match']
    events=Counter()
    for row in d['events']:
        if row['kind']!=kind or row['owner'].get('team')!=team:
            continue
        for e in row['entries']:
            key=e['timestamp']['round'],row['owner']['id'],e.get('x'),e.get('y'),e.get('context'),str(e.get('value'))
            events[key]+=1
    return (match['engineBuildHash'],match['mapHash'],match['seed']),match['outcome']==team,events


def audit(base, candidate, kind):
    names={f.parent.name:f for f in base.glob('games/*/summary.json')}
    other={f.parent.name:f for f in candidate.glob('games/*/summary.json')}
    if names.keys()!=other.keys() or not names:
        raise ValueError((base,candidate,'Unpaired cells'))
    cells={}
    totals=defaultdict(Counter)
    for name,p in sorted(names.items()):
        key,bwin,b=read(p,kind)
        akey,awin,a=read(other[name],kind)
        if key!=akey:
            raise ValueError((name,key,akey))
        earlier=min((r[0] for r in ((b-a)+(a-b))),default=None)
        label='gain' if awin and not bwin else 'loss' if bwin and not awin else 'same'
        row=dict(outcome=label,first_event_difference=earlier,base=b.total(),candidate=a.total(),
                 base150=sum(n for e,n in b.items() if e[0]<=150),
                 candidate150=sum(n for e,n in a.items() if e[0]<=150))
        cells[name]=row
        for tag in ('all',label):
            totals[tag].update(games=1,changed=earlier is not None,
                base=row['base'],candidate=row['candidate'],base150=row['base150'],candidate150=row['candidate150'])
    return dict(totals=totals,cells=cells)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('scratch',type=Path)
    p.add_argument('candidate')
    p.add_argument('event')
    p.add_argument('opponents',nargs='+')
    p.add_argument('--baseline',default='base')
    p.add_argument('--divergence',type=Path)
    a=p.parse_args()
    out={}
    for o in a.opponents:
        out[o]=audit(*(a.scratch/f'gx-{t}-pool-{o}' for t in (a.baseline,a.candidate)),a.event)
    if a.divergence:
        for x in json.loads(a.divergence.read_text())['cells']:
            opponent,name=x['name'].split(':',1)
            cell=out[opponent]['cells'][f"{name}-{x['side']}"]
            first=x['first']
            event=cell['first_event_difference']
            cell['first_observable_divergence']=first['round'] if first else None
            cell['state_diff_precedes_event_change']=(event is None or first['round'] <= event) if first else None
    print(json.dumps(out,indent=2))


if __name__=='__main__':
    main()
