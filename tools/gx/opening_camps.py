"""Audit actual early capture choices against static walking access from both spawns."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path

from map_audit import Engine, bfs, group_distance, mirror, read_map


def geometry(m,runtime):
    w,h=m['w'],m['h']
    xa,ya,xb,yb=m['spawn']
    spawn_a={(x,y) for y in range(ya,yb+1) for x in range(xa,xb+1)}
    spawn_b={mirror(p,w,h,m['symmetry']) for p in spawn_a}
    static={(x,y) for x in range(w) for y in range(h)} - set(m['walls']) - set(m['holes']) - set(m['altars'])
    field_a, field_b=bfs(static-spawn_b,spawn_a),bfs(static-spawn_a,spawn_b)
    out={}
    for g in runtime['groups']:
        cells=[tuple(p) for p in g['tiles']]
        a,b=group_distance(cells,field_a),group_distance(cells,field_b)
        out[int(g['id'])] = (a,b,int(g['gems']),int(g['gold']))
    return out


def match(path,g,limit):
    data=json.loads(path.read_text())
    side=path.parent.name[-1]
    counters={t:Counter() for t in ('teamA','teamB')}
    mid_first={t:None for t in counters}
    for event in data['events']:
        who=event['owner'].get('team')
        if who not in counters or event['kind']!='gemCollection':
            continue
        for e in event['entries']:
            r=e['timestamp']['round']
            if r>limit or e.get('context')!='campGroup':
                continue
            target=e.get('target')
            if not isinstance(target,dict) or target.get('kind')!='campGroup':
                raise ValueError((path,target))
            a,b,gems,gold=g[int(target['id'])]
            if who=='teamB':
                a,b=b,a
            side_type='cut'
            if a is not None and b is not None:
                side_type='centre' if abs(a-b) <= max(3,0.18*(a+b)) else 'home' if a<b else 'enemy'
            elif a is not None:
                side_type='home'
            c=counters[who]
            c[f'{side_type}_gems']+=int(e['value'])
            c[f'{side_type}_listed_gold']+=gold
            c[f'{side_type}_captures']+=1
            if side_type=='centre' and int(e['value'])>0:
                old=mid_first[who]
                mid_first[who]=r if old is None else min(r,old)
    me='team'+side
    them='team'+('B' if side=='A' else 'A')
    result=Counter(games=1)
    lead=mid_first[me]
    trail=mid_first[them]
    result['us_first_centre']+=lead is not None and (trail is None or lead<trail)
    result['them_first_centre']+=trail is not None and (lead is None or trail<lead)
    result['same_centre_round']+=lead is not None and lead==trail
    result['no_centre_gems']+=lead is None and trail is None
    for label,owner in (('ours',me),('theirs',them)):
        for k,v in counters[owner].items():
            result[f'{label}_{k}'] += v
    return data['match']['outcome']==me,result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('engine',type=Path)
    p.add_argument('maps',type=Path)
    p.add_argument('groups',type=Path)
    p.add_argument('scratch',type=Path)
    p.add_argument('tag')
    p.add_argument('--rounds',type=int,default=150)
    a=p.parse_args()
    os.environ['BC_ENGINE_WASM']=str(a.engine.resolve())
    E=Engine()
    recorded=json.loads(a.groups.read_text())
    geo={}
    for f in a.maps.glob('*.map26a'):
        content=f.read_bytes()
        data=recorded[f.stem]
        if sha256(content).hexdigest()!=data['map_sha256']:
            raise ValueError(f'Mismatched runtime map: {f.name}')
        geo[f.stem]=geometry(read_map(E,content),data)
    output={}
    for run in a.scratch.glob(f'gx-{a.tag}-pool-*'):
        rows=list(run.glob('games/*/summary.json'))
        if len(rows)!=172:
            raise ValueError(f'Expected 172 matches: {run}')
        t=defaultdict(Counter)
        for f in rows:
            w,m=match(f,geo[f.parent.name[:-2]],a.rounds)
            t['all'].update(m)
            t['win' if w else 'nonwin'].update(m)
        output[run.name]=t
    if not output:
        raise ValueError(f'No runs for {a.tag}')
    print(json.dumps(dict(opening_rounds=a.rounds,runs=output),indent=2))


if __name__=='__main__':
    main()
