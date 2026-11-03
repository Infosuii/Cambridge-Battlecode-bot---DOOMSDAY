"""Measure geometric access for walking, one-hole bridges and bounded jumps."""
import argparse
from collections import deque
from hashlib import sha256
import json
import os
from pathlib import Path

from map_audit import Engine, NEIGHBOURS, bfs, mirror, read_map


def flood(terrain, sources, jump):
    moves=[(x,y) for x in range(-jump,jump+1) for y in range(-jump,jump+1) if x or y]
    known=set(sources)&terrain
    q=deque(known)
    while q:
        x,y=q.popleft()
        for dx,dy in moves:
            p=(x+dx,y+dy)
            if p in terrain and p not in known:
                known.add(p)
                q.append(p)
    return known


def one_jump(terrain, reached, distance):
    launch=[(x,y) for x,y in reached if any((x+dx,y+dy) not in reached for dx,dy in NEIGHBOURS)]
    land=set()
    for x,y in launch:
        for dx in range(-distance,distance+1):
            for dy in range(-distance,distance+1):
                p=(x+dx,y+dy)
                if p in terrain and p not in reached: land.add(p)
    return reached | set(bfs(terrain,land))


def report(m,runtime,side):
    w,h=m['w'],m['h']
    xa,ya,xb,yb=m['spawn']
    a={(x,y) for y in range(ya,yb+1) for x in range(xa,xb+1)}
    b={mirror(p,w,h,m['symmetry']) for p in a}
    ours,foe=(a,b) if side=='A' else (b,a)
    holes=set(m['holes'])
    terrain={(x,y) for x in range(w) for y in range(h)}-foe-holes-set(m['walls'])-set(m['altars'])
    walk=set(bfs(terrain,ours))
    bridge={(x,y) for x,y in holes if any((x+dx,y+dy) in terrain and (x-dx,y-dy) in terrain
           for dx,dy in ((1,0),(0,1),(1,1),(1,-1)))}
    occupied={'walking':walk,'stock_bridge_overlay':set(bfs(terrain|bridge,ours)) & terrain,
              'single_jump_2':one_jump(terrain,walk,2),
              'single_jump_3':one_jump(terrain,walk,3),
              'repeated_jump_2':flood(terrain,ours,2),'repeated_jump_3':flood(terrain,ours,3)}
    ring={(x+dx,y+dy) for x,y in m['altars'] for dx,dy in NEIGHBOURS}&terrain
    out={}
    for kind,reachable in occupied.items():
        groups=[g for g in runtime if any(tuple(p) in reachable for p in g['tiles'])]
        out[kind]=dict(groups=len(groups),gems=sum(g['gems'] for g in groups),tiles=len(reachable),altar_tiles=len(ring&reachable))
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('engine',type=Path)
    p.add_argument('map_dir',type=Path)
    p.add_argument('runtime',type=Path)
    a=p.parse_args()
    os.environ['BC_ENGINE_WASM']=str(a.engine.resolve())
    E=Engine()
    data=json.loads(a.runtime.read_text())
    out={}
    for f in sorted(a.map_dir.glob('*.map26a')):
        content=f.read_bytes()
        if sha256(content).hexdigest()!=data[f.stem]['map_sha256']: raise ValueError(f)
        m=read_map(E,content)
        out[f.stem]={s:report(m,data[f.stem]['groups'],s) for s in 'AB'}
    print(json.dumps(out,indent=2))


if __name__=='__main__':
    main()
