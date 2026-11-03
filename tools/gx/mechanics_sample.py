"""Read a stable map sample with the official replay decoder and cross-check match totals."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import zipfile


def worker(entries, assets):
    env = dict(os.environ, NFS_REPLAY_ENGINE='2.0.0', NFS_REPLAY_ASSETS=str(assets.resolve()))
    script = Path(__file__).with_name('match_mechanics.mjs').resolve()
    paths = [x[0] for x in entries]
    run = subprocess.run(['node',str(script),*map(str,paths)], env=env,
        capture_output=True,text=True,timeout=240,check=True)
    output = [json.loads(line) for line in run.stdout.splitlines()]
    if len(output) != len(entries):
        raise ValueError('Replay decoder output count changed')
    for row, (path, summary_path, side) in zip(output,entries):
        if Path(row['path']) != path:
            raise ValueError('Replay decoder identity changed')
        d = json.loads(summary_path.read_text())
        if row['round'] != d['match']['roundsStarted']:
            raise ValueError((path,row['round'],d['match']['roundsStarted']))
        by_team = {t['team']:t for t in d['teams']}
        for t, name in zip(row['teams'], ('teamA','teamB')):
            bank = sum(len(e['entries']) for e in d['events'] if e['kind']=='gemSubmission' and e['owner']['team']==name)
            if (t['bankGems'], t['bankEvents']) != (int(by_team[name]['submittedGems']),bank):
                raise ValueError((path,name,t,by_team[name],bank))
        row['cell'] = summary_path.parent.name
        row['map_sha256'] = d['match']['mapHash']
        row['side'] = side
        row['won'] = d['match']['outcome'] == 'team'+side
        del row['path']
    return output


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('scratch',type=Path)
    p.add_argument('assets',type=Path)
    p.add_argument('extracted',type=Path)
    p.add_argument('tag')
    p.add_argument('opponents',nargs='+')
    p.add_argument('--maps',type=int,default=24)
    p.add_argument('--workers',type=int,default=2)
    a=p.parse_args()
    a.extracted.mkdir(parents=True)
    reports={}
    for opp in a.opponents:
        root=a.scratch/f'gx-{a.tag}-pool-{opp}'/'games'
        candidates=sorted((p.name[:-2] for p in root.glob('*-A')),
            key=lambda name:sha256(('gx-mechanics-v1:'+name).encode()).digest())
        if len(candidates)!=86:
            raise ValueError((opp,'Not a full pool',len(candidates)))
        names=sorted(candidates[:a.maps])
        jobs=[]
        for n in names:
            for side in 'AB':
                folder=root/f'{n}-{side}'
                bundles=list(folder.glob('*.repl26a'))
                if len(bundles)!=1:
                    raise ValueError((folder,bundles))
                path=a.extracted/f'{opp}-{n}-{side}.repl26a'
                with zipfile.ZipFile(bundles[0]) as archive:
                    path.write_bytes(archive.read('replay.repl26a'))
                jobs.append((path,folder/'summary.json',side))
        with ThreadPoolExecutor(max_workers=a.workers) as pool:
            batches=[jobs[i::a.workers] for i in range(a.workers)]
            rows=sorted((row for batch in pool.map(lambda b:worker(b,a.assets),batches)
                         for row in batch),key=lambda row:row['cell'])
        ours,theirs=Counter(),Counter()
        for row in rows:
            side='AB'.index(row['side'])
            ours.update(row['teams'][side])
            theirs.update(row['teams'][1-side])
        reports[opp]=dict(maps=names,games=len(rows),us=ours,opponent=theirs,cells=rows)
    print(json.dumps(reports,indent=2))


if __name__=='__main__':
    main()
