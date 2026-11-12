"""Audit unsubmitted live bags immediately before baseline non-wins."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import zipfile

from map_audit import Engine, read_map


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('scratch',type=Path)
    p.add_argument('maps',type=Path)
    p.add_argument('engine',type=Path)
    p.add_argument('assets',type=Path)
    p.add_argument('extracted',type=Path)
    p.add_argument('--workers',type=int,default=2)
    a=p.parse_args()
    a.extracted.mkdir(parents=True)
    os.environ['BC_ENGINE_WASM']=str(a.engine.resolve())
    e=Engine()
    altars={}
    for path in sorted(a.maps.glob('*.map26a')):
        data=path.read_bytes()
        m=read_map(e,data)
        altars[path.stem]=(sha256(data).hexdigest(),m['altars'])
    meta={}
    jobs=[]
    for opponent in ('v92','v86h','x1bru'):
        for p in sorted((a.scratch/f'gx-base-pool-{opponent}'/'games').glob('*/summary.json')):
            d=json.loads(p.read_text())
            side=p.parent.name[-1]
            m=d['match']
            if m['outcome']=='team'+side:
                continue
            digest,points=altars[p.parent.name[:-2]]
            if digest!=m['mapHash']:
                raise ValueError(p)
            entry=p.parent.name+':'+opponent
            bundles=list(p.parent.glob('*.repl26a'))
            if len(bundles)!=1:
                raise ValueError(p)
            dest=a.extracted/f'{entry}.repl26a'
            with zipfile.ZipFile(bundles[0]) as z:
                dest.write_bytes(z.read('replay.repl26a'))
            scores={x['team']:int(x['submittedGems']) for x in d['teams']}
            meta[entry]=(m['roundsStarted'],[scores['teamA'],scores['teamB']],side,opponent)
            jobs.append(dict(id=entry,side='AB'.index(side),last=m['roundsStarted'],altars=points,path=str(dest.resolve())))
    env=dict(os.environ,NFS_REPLAY_ENGINE='2.0.0',NFS_REPLAY_ASSETS=str(a.assets.resolve()))
    script=Path(__file__).with_suffix('.mjs').resolve()

    def run(i):
        path=a.extracted/f'worker-{i}.json'
        path.write_text(json.dumps(jobs[i::a.workers]))
        r=subprocess.run(['node',str(script),str(path)],env=env,text=True,check=True,capture_output=True,timeout=300)
        return [json.loads(line) for line in r.stdout.splitlines()]

    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        rows=sorted((x for batch in pool.map(run,range(a.workers)) for x in batch),key=lambda x:x['id'])
    if len(rows)!=len(jobs):
        raise ValueError('Unexpected row count')
    summary={}
    for row in rows:
        last,expected,side,opponent=meta[row['id']]
        if (row['finish']['round'],row['finish']['banks'])!=(last,expected):
            raise ValueError((row['id'],row['finish'],last,expected))
        for tag in ('all',opponent):
            s=summary.setdefault(tag,{'matches':0,'windows':{}})
            s['matches']+=1
            for w in row['rows']:
                out=s['windows'].setdefault(w['length'],Counter())
                for key,value in w.items():
                    if key.startswith('max_bank_'):
                        out[key+'_1000']+=value>=1000
                        out[key+'_beats_final_enemy']+=value>expected['AB'.index(side)^1]
    print(json.dumps(dict(summary=summary,cells=rows),indent=2))


if __name__=='__main__':
    main()
