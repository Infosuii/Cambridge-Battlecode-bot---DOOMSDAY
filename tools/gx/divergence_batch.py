"""Trace the first different game state in every flipped match of a paired gate."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import zipfile

from compare import load,pair


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('records',type=Path)
    p.add_argument('scratch',type=Path)
    p.add_argument('assets',type=Path)
    p.add_argument('extracted',type=Path)
    p.add_argument('tag')
    p.add_argument('opponents',nargs='+')
    p.add_argument('--baseline',default='base')
    p.add_argument('--workers',type=int,default=2)
    a=p.parse_args()
    a.extracted.mkdir(parents=True)
    entries=[]
    for o in a.opponents:
        names=[f'gx-{tag}-pool-{o}' for tag in (a.baseline,a.tag)]
        b,c=[load(a.records/name/'results.json') for name in names]
        pair(b,c)
        for key,x in sorted(b.items()):
            y=c[key]
            if x['outcome']==y['outcome']:
                continue
            m,s=key
            base_path=[]
            for name in names:
                source=a.scratch/name/'games'/f'{m}-{s}'
                bundles=list(source.glob('*.repl26a'))
                if len(bundles)!=1:
                    raise ValueError((source,bundles))
                out=a.extracted/f'{name}-{m}-{s}.repl26a'
                with zipfile.ZipFile(bundles[0]) as z:
                    out.write_bytes(z.read('replay.repl26a'))
                base_path.append(str(out))
            entries.append((o+':'+m,s,*base_path))
    env=dict(os.environ,NFS_REPLAY_ENGINE='2.0.0',NFS_REPLAY_ASSETS=str(a.assets.resolve()))
    script=Path(__file__).with_name('first_divergence.mjs').resolve()

    def run(jobs):
        if not jobs:
            return []
        cmd=['node',str(script),*(x for job in jobs for x in job)]
        s=subprocess.run(cmd,env=env,check=True,text=True,capture_output=True,timeout=240)
        rows=[json.loads(line) for line in s.stdout.splitlines()]
        if len(rows)!=len(jobs):
            raise ValueError('Unexpected decoder row count')
        return rows

    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        rows=sorted((row for batch in pool.map(run,(entries[i::a.workers] for i in range(a.workers))) for row in batch),
            key=lambda row:(row['name'],row['side']))
    early=[r for r in rows if r['first'] and all(t is None or r['first']['round']+1<t for t in r['finishReady'])]
    print(json.dumps(dict(tag=a.tag,baseline=a.baseline,flipped=len(rows),strictly_before_finish_ready=len(early),cells=rows),indent=2))


if __name__=='__main__':
    main()
