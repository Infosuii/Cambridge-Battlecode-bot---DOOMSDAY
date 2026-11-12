"""EXP265: reuse exact passing V2 smoke binary, all90dev/both sides."""
from concurrent.futures import ThreadPoolExecutor
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from qualify_local import partition

if __name__=='__main__':
    smoke=read(HERE/'DRAFT_BUSH_CACHE_SMOKE_V2.json');assert smoke['pass'] and smoke['games']==8
    old=read(HERE/'GROUPED_BUSH_CODEC_IDLE_PROOF.json');assert old['pass'];index={(r['map'],r['side']):r for r in old['rows']}
    wasm=SDK_ROOT/'bots/draft-bush-cache-smoke-v2-probe-20261106/bot.wasm';assert bench.digest(wasm)==smoke['pins']['probe']
    for n,h in smoke['pins']['sources'].items():assert bench.digest(wasm.parent/'src'/n)==h
    off=SDK_ROOT/'bots/draft-bush-cache-smoke-v2-off-20261106/bot.wasm';assert bench.digest(off)==smoke['pins']['off']
    ref=SDK_ROOT/'bots/offset-aoe-idle-20261106/bot.wasm';assert bench.digest(ref)==smoke['pins']['reference'] and bench.digest(CLI)==CLI_HASH
    maps=sorted(partition('dev'),key=bench.digest);assert len(maps)==90
    output=bench.CACHE/'draft-bush-cache-full-v2-20261106';output.mkdir()
    plan={'engine':ENGINE,'cli':CLI_HASH,'probe':bench.digest(wasm),'off':bench.digest(off),'reference':bench.digest(ref),'sources':smoke['pins']['sources'],
          'maps':{p.name:bench.digest(p) for p in maps},'games':180,'baseline_sha256':bench.digest(HERE/'GROUPED_BUSH_CODEC_IDLE_PROOF.json'),
          'scope':'Same-game schema/memory/corruption/partial-label/cold-load/original-source draft controls only, not release safety/strength.'}
    write(HERE/'DRAFT_BUSH_CACHE_FULL_V2_PLAN.json',plan)
    def run(job):
        mp,side=job;prior=index[mp.stem,side];p=bench.ROOT/prior['directory']/'native.json';assert bench.digest(p)==prior['native_sha256'];before=read(p)
        d=output/f'{mp.stem}-{side}';d.mkdir();bots=(wasm,ref) if side=='A' else (ref,wasm)
        with (d/'run.log').open('xb') as log:subprocess.run([CLI,'run',*bots,'--map',mp,'--release','--fuel','100000','--json','--log-limit','100000','--statistics',d/'native.json','--out-dir',d],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        doc=read(d/'native.json');assert doc['match']['engineBuildHash']==ENGINE and doc['match']['mapHash']==bench.digest(mp) and doc['diagnostics']['detailedCaptureComplete']
        archive,=d.glob('*.repl26a')
        with ZipFile(archive) as z:stdout=z.read('team-'+side.lower()+'.stdout').replace(b'\0',b'').decode('utf8')
        line,=[l for l in stdout.splitlines() if l.startswith('DRAFT_BUSH_PROOF ')];draft=list(map(int,line.split()[1:]));assert len(draft)==10
        line,=[l for l in stdout.splitlines() if l.startswith('PLAY_BUSH_PROOF ')];play=list(map(int,line.split()[1:]));assert len(play)==5
        error=bool(doc['diagnostics']['codes'] or any(doc['diagnostics']['botFaults'].values()));fuel=sum(len(e['entries']) for e in doc['events'] if e['kind']=='fuelExhausted')
        parity=doc['roster']['draft']==before['roster']['draft']
        passed=parity and not error and not fuel and draft[5]==0 and draft[3] in (1,2,3) and play[0]==play[1]==int(draft[3]==1) and play[4]==0
        return {'map':mp.stem,'side':side,'map_hash':bench.digest(mp),'draft':draft,'play':play,'draft_equal':parity,'errors':error,'fuel':fuel,'pass':passed,
                'stdout':stdout,'native_sha256':bench.digest(d/'native.json'),'archive_sha256':bench.digest(archive),'directory':d.relative_to(bench.ROOT).as_posix()}
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(run,[(mp,side) for mp in maps for side in 'AB']):
            rows.append(r)
            if len(rows)%30==0:print(f'{len(rows)}/180',flush=True)
    report={'pins':plan,'games':len(rows),'pass':all(r['pass'] for r in rows),'failed':sum(not r['pass'] for r in rows),
            'admitted':sum(r['draft'][3]==1 for r in rows),'budget_refused':sum(r['draft'][3]==2 for r in rows),'space_refused':sum(r['draft'][3]==3 for r in rows),'rows':rows}
    write(HERE/'DRAFT_BUSH_CACHE_FULL_V2.json',report);print({k:v for k,v in report.items() if k not in ('pins','rows')},flush=True)
