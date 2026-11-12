"""Fetch a disclosed, diverse sample of newest known-version losses and audit the actual replays."""
import concurrent.futures as cf
import os
from pathlib import Path
import subprocess
import zipfile
from collect import ROOT,OUT,RAW,read,save,call

def main():
    metrics=read(OUT/'metrics.json')
    eligible=[r for r in metrics if r['arm']=='v62c' and not r['win']]
    selected={}
    for opp in sorted({r['opponent'] for r in eligible}):
        rr=sorted([r for r in eligible if r['opponent']==opp],key=lambda r:r['createdAt'],reverse=True)
        for r in rr[:2]:selected[r['matchId']]=r
    for r in eligible:
        if r['map']=='01boss_battle' or (r['opponent']=='Intercontinental Fish' and r['map']=='00crater') or (r['opponent']=='Claudus Maximus' and r['map']=='adgato_gemcombat5'):
            selected[r['matchId']]=r
    def fetch(r):
        dest=RAW/r['matchId'];dest.mkdir(parents=True,exist_ok=True)
        archive=dest/'replay.repl26a'
        if not archive.exists():call(['matches','download',r['matchId'],'--output',str(archive)])
        inner=dest/'inner/replay.repl26a';inner.parent.mkdir(exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None:raise RuntimeError('invalid ZIP')
            inner.write_bytes(z.read('replay.repl26a'))
        return dict(matchId=r['matchId'],opponent=r['opponent'],map=r['map'],arm=r['arm'],archive=archive.relative_to(ROOT).as_posix(),inner=inner.relative_to(ROOT).as_posix())
    entries,errors=[],[]
    with cf.ThreadPoolExecutor(max_workers=2) as ex:
        futures={ex.submit(fetch,r):k for k,r in selected.items()}
        for f in cf.as_completed(futures):
            try:entries.append(f.result())
            except Exception as e:errors.append(dict(matchId=futures[f],error=str(e)))
            print('targeted replays',len(entries),'/',len(selected),'errors',len(errors),flush=True)
            save(OUT/'deep-replay-manifest.json',dict(selection='two most recent known v62c losses per opponent, plus boss_battle and two catastrophic examples; purposive sample, not random',selected=len(selected),matches=entries,errors=errors))
    env=dict(os.environ,NFS_REPLAY_ENGINE='2.0.0')
    def decode(i):
        files=[str(ROOT/e['inner']) for e in entries[i::4]]
        if not files:return
        output=OUT/f'fights-{i}.json'
        p=subprocess.run(['node','--no-warnings',str(OUT/'fight_audit.mjs'),str(output),*files],env=env,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=600)
        (OUT/f'fights-{i}.log').write_text(p.stdout+p.stderr,encoding='utf8')
        if p.returncode:raise RuntimeError(p.stderr[-1000:])
        return read(output)
    rows=[]
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        for result in ex.map(decode,range(4)):rows.extend(result or [])
    save(OUT/'deep-fights.json',rows)
    print('DEEP REPLAY DONE',len(rows),flush=True)

if __name__=='__main__':main()
