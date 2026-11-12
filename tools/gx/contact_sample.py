"""Extract independent game contact observations using the actual champion perspective."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import zipfile


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('scratch',type=Path)
    p.add_argument('assets',type=Path)
    p.add_argument('out',type=Path)
    p.add_argument('--maps',type=int,default=36)
    p.add_argument('--workers',type=int,default=2)
    a=p.parse_args()
    a.out.mkdir(parents=True)
    jobs=[]
    for opponent in ('v92','v86h','x1bru'):
        paths=a.scratch/f'gx-base-pool-{opponent}'/'games'
        names=sorted((d.name[:-2] for d in paths.glob('*-A')),
            key=lambda k:sha256(('gx-contact-v1:'+k).encode()).digest())
        if len(names)!=86: raise ValueError(paths)
        for name in names[:a.maps]:
            for side in 'AB':
                game=paths/f'{name}-{side}'
                d=json.loads((game/'summary.json').read_text())
                deaths=[]
                for row in d['events']:
                    if row['kind']=='death':
                        for event in row['entries']:
                            deaths.append([event['timestamp']['round'],row['owner']['id'],int(event['context']=='champion')])
                bundle=list(game.glob('*.repl26a'))
                if len(bundle)!=1: raise ValueError(game)
                stem=f'{name}-{side}-{opponent}'
                r=a.out/(stem+'.repl26a')
                with zipfile.ZipFile(bundle[0]) as z:
                    r.write_bytes(z.read('replay.repl26a'))
                jobs.append(dict(id=stem,map=name,opponent=opponent,side='AB'.index(side),
                    last=d['match']['roundsStarted'],path=str(r.resolve()),deaths=deaths))
    env=dict(os.environ,NFS_REPLAY_ENGINE='2.0.0',NFS_REPLAY_ASSETS=str(a.assets.resolve()))
    script=Path(__file__).with_suffix('.mjs').resolve()

    def run(i):
        path=a.out/f'contact-jobs-{i}.json'
        output=a.out/f'contacts-{i}.jsonl'
        path.write_text(json.dumps(jobs[i::a.workers]))
        with output.open('x') as dest:
            subprocess.run(['node',str(script),str(path)],env=env,text=True,check=True,stdout=dest,timeout=800)
        return output

    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        for output in pool.map(run,range(a.workers)):
            print(output,flush=True)


if __name__=='__main__':
    main()
