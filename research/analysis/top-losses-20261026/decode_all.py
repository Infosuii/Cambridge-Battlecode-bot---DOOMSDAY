"""Decode every downloaded loss, using its recorded engine version; never mixes engines."""
import concurrent.futures as cf
import os
import subprocess
import zipfile
from pathlib import Path
from collect import ROOT,OUT,RAW,read,save

def main():
    losses={m['matchId'] for m in read(OUT/'losses.json')}
    manifest=read(OUT/'manifest.json')
    assert not manifest['errors'],manifest['errors']
    entries=[e for e in manifest['matches'] if e['matchId'] in losses]
    assert len(entries)==len(losses)
    for e in entries:
        p=ROOT/e['replay'];dest=RAW/e['matchId']/'inner/replay.repl26a';dest.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(p) as z:dest.write_bytes(z.read('replay.repl26a'))
        e['inner']=str(dest)
    jobs=[]
    for engine in sorted({e['engine'] for e in entries}):
        ee=[e for e in entries if e['engine']==engine]
        for offset in range(4):
            for start in range(offset*16,len(ee),64):
                batch=ee[start:start+16]
                if batch:jobs.append((engine,len(jobs),batch))
    errors=[];rows=[]
    def run(job):
        engine,index,batch=job
        out=RAW/f'audit-{index}.json'
        env=dict(os.environ,NFS_REPLAY_ENGINE=engine)
        args=['node','--no-warnings',str(OUT/'fight_audit.mjs'),str(out),*[e['inner'] for e in batch]]
        p=subprocess.run(args,capture_output=True,text=True,encoding='utf8',errors='replace',env=env,timeout=600)
        (RAW/f'audit-{index}.log').write_text(p.stdout+p.stderr,encoding='utf8')
        if p.returncode:raise RuntimeError(f'engine {engine} batch {index}: '+p.stderr[-1000:])
        result=read(out)
        for r in result:
            r['engine']=engine
            r['file']=Path(r['file']).relative_to(ROOT).as_posix()
        return result
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        futures={ex.submit(run,j):j for j in jobs}
        for f in cf.as_completed(futures):
            try:rows.extend(f.result())
            except Exception as e:errors.append(str(e))
            print('decoded',len(rows),'/',len(entries),'batch errors',len(errors),flush=True)
            save(OUT/'all-loss-fights.json',rows)
            save(OUT/'decode-status.json',dict(expected=len(entries),decoded=len(rows),errors=errors))
    assert not errors,errors
    assert {r['id'] for r in rows}==losses
    print('ALL LOSS REPLAYS DECODED',len(rows),flush=True)

if __name__=='__main__':main()
