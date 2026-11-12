"""Check identical replay prefixes up to one instrumented decision."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

from compare import load, pair

MARK = re.compile(r'GXPACK_CHECK (\d+) (\d+) (\d+) (\d+)')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('records',type=Path)
    p.add_argument('scratch',type=Path)
    p.add_argument('assets',type=Path)
    p.add_argument('temp',type=Path)
    p.add_argument('baseline')
    p.add_argument('candidate')
    p.add_argument('--workers',type=int,default=2)
    a=p.parse_args()
    a.temp.mkdir(parents=True)
    before,after=[load(a.records/t/'results.json') for t in (a.baseline,a.candidate)]
    scores=pair(before,after)
    jobs=[]
    no_marker=0
    no_marker_changed_summary=[]
    mispaired=[]
    for name,side in sorted(before):
        cell=f'{name}-{side}'
        folders=[a.scratch/t/'games'/cell for t in (a.baseline,a.candidate)]
        markers=[]
        bundles=[]
        for f in folders:
            stdout=f/'candidate.stdout'
            source=list(f.glob('*.repl26a'))
            if len(source)!=1: raise ValueError(f)
            bundles.append(source[0])
            if stdout.exists():
                markers.append(MARK.findall(stdout.read_text(errors='replace')))
            else:
                with zipfile.ZipFile(source[0]) as z:
                    markers.append(MARK.findall(z.read(f'team-{side.lower()}.stdout').decode(errors='replace')))
        if markers[0]!=markers[1] or len(markers[0])>1:
            mispaired.append(dict(cell=cell,markers=markers))
            continue
        if not markers[0]:
            no_marker+=1
            if sha256((folders[0]/'summary.json').read_bytes()).digest()!=sha256((folders[1]/'summary.json').read_bytes()).digest():
                no_marker_changed_summary.append(cell)
            continue
        r,actor,old,new=map(int,markers[0][0])
        job=dict(cell=cell,round=r,actor=actor,old=old,new=new)
        for tag,bundle in zip(('base','candidate'),bundles):
            dest=a.temp/f'{cell}-{tag}.repl26a'
            with zipfile.ZipFile(bundle) as z:
                dest.write_bytes(z.read('replay.repl26a'))
            job[tag]=str(dest.resolve())
        jobs.append(job)
    env=dict(os.environ,NFS_REPLAY_ENGINE='2.0.0',NFS_REPLAY_ASSETS=str(a.assets.resolve()))
    js=Path(__file__).with_suffix('.mjs')

    def run(i):
        path=a.temp/f'jobs-{i}.json'
        path.write_text(json.dumps(jobs[i::a.workers]))
        s=subprocess.run(['node',str(js),str(path)],env=env,check=True,text=True,capture_output=True,timeout=420)
        return [json.loads(line) for line in s.stdout.splitlines()]

    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        rows=sorted((x for b in pool.map(run,range(a.workers)) for x in b),key=lambda x:x['cell'])
    if len(rows)!=len(jobs):
        raise ValueError('Missing decoder rows')
    n_same=sum(x['identical'] for x in rows)
    print(json.dumps(dict(baseline=a.baseline,candidate=a.candidate,scores=scores,
        activated=len(jobs),identical_prefixes=n_same,marker_mismatches=mispaired,
        no_marker=no_marker,no_marker_changed_summary=no_marker_changed_summary,cells=rows),indent=2))
    if n_same!=len(rows) or mispaired or no_marker_changed_summary:
        raise SystemExit('Prefix equivalence did not hold for every pair')


if __name__=='__main__':
    main()
