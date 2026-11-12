"""EXP263 initial static-hash smoke plus original development cold-query fixture."""
from concurrent.futures import ThreadPoolExecutor
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from live111_draft_bush_cache import prepare
from profile_live111_first import exact_build
from qualify_local import partition

MAIN='''#include "bot.h"
#include "draft.h"
#include "codex_field_cache.h"
#include "draft_bush_cache.h"
#include <cstdio>
__PROBE__
int main(){bool checked=false;for(;;){
    if(bc::is_draft()){
        codex_field_cache::store();codex_draft_bush::store();
        if(!checked){cache_draft_proof();checked=true;}
        play_draft();
    }else{cache_play_proof();bc::resign();}
    bc::end_turn();
}}
'''

if __name__=='__main__':
    assert read(HERE/'GROUPED_BUSH_CODEC_IDLE_PROOF.json')['pass']
    assert bench.digest(CLI)==CLI_HASH
    output=bench.CACHE/'draft-bush-cache-smoke-20261106';output.mkdir()
    off_source=output/'off-source';prepare(off_source,False)
    off=exact_build(off_source,SDK_ROOT/'bots/draft-bush-cache-smoke-off-20261106',1)
    expected=read(HERE/'LIVE111_OWNED_JOINT_REGRESSION_PLAN.json')['source_build'];assert bench.digest(off)==expected
    source=output/'probe-source';prepare(source,True,True)
    (source/'main.cpp').write_text(MAIN.replace('__PROBE__',(HERE/'draft_bush_cache_probe.inc').read_text(encoding='utf8')),encoding='utf8',newline='\n')
    wasm=exact_build(source,SDK_ROOT/'bots/draft-bush-cache-smoke-probe-20261106',1)
    maps=sorted(partition('dev'),key=bench.digest);cold=read(HERE/'LIVE111_OWNED_JOINT_REGRESSION_PLAN.json')['case']['map']
    chosen={p.stem:p for p in maps[:3]}
    chosen[cold]=next(p for p in maps if p.stem==cold)
    ref=SDK_ROOT/'bots/offset-aoe-idle-20261106/bot.wasm';assert bench.digest(ref)==read(HERE/'OFFSET_AOE_ACTION_PROOF.json')['builds']['idle']
    plan={'engine':ENGINE,'cli':CLI_HASH,'off':bench.digest(off),'probe':bench.digest(wasm),'reference':bench.digest(ref),
          'sources':{p.name:bench.digest(p) for p in source.iterdir() if p.is_file()},'maps':{p.name:bench.digest(p) for p in chosen.values()},
          'selection':'First3 stable-SHA dev maps plus original preregistered development cold-query fixture; both sides; no official-pool tuning.',
          'games':2*len(chosen),'scope':'Same-game slot-padding/cache correctness and isolated first-play cold cost; no release/strength qualification.'}
    write(HERE/'DRAFT_BUSH_CACHE_SMOKE_PLAN.json',plan)
    def run(job):
        mp,side=job;d=output/f'{mp.stem}-{side}';d.mkdir();bots=(wasm,ref) if side=='A' else (ref,wasm)
        with (d/'run.log').open('xb') as log:subprocess.run([CLI,'run',*bots,'--map',mp,'--release','--fuel','100000','--json','--log-limit','100000','--statistics',d/'native.json','--out-dir',d],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        doc=read(d/'native.json');assert doc['match']['engineBuildHash']==ENGINE and doc['match']['mapHash']==bench.digest(mp) and doc['diagnostics']['detailedCaptureComplete']
        archive,=d.glob('*.repl26a')
        with ZipFile(archive) as z:stdout=z.read('team-'+side.lower()+'.stdout').replace(b'\0',b'').decode('utf8')
        line,=[l for l in stdout.splitlines() if l.startswith('DRAFT_BUSH_PROOF ')];draft=list(map(int,line.split()[1:]));assert len(draft)==10
        line,=[l for l in stdout.splitlines() if l.startswith('PLAY_BUSH_PROOF ')];play=list(map(int,line.split()[1:]));assert len(play)==5
        error=bool(doc['diagnostics']['codes'] or any(doc['diagnostics']['botFaults'].values()));fuel=sum(len(e['entries']) for e in doc['events'] if e['kind']=='fuelExhausted')
        passed=not error and not fuel and draft[5]==0 and draft[3] in (1,2,3) and play[0]==play[1]==int(draft[3]==1) and play[4]==0
        return {'map':mp.stem,'side':side,'map_hash':bench.digest(mp),'draft':draft,'play':play,'errors':error,'fuel':fuel,'pass':passed,
                'stdout':stdout,'native_sha256':bench.digest(d/'native.json'),'archive_sha256':bench.digest(archive),'directory':d.relative_to(bench.ROOT).as_posix()}
    with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(run,[(mp,side) for mp in chosen.values() for side in 'AB']))
    report={'pins':plan,'games':len(rows),'pass':all(r['pass'] for r in rows),'rows':rows}
    write(HERE/'DRAFT_BUSH_CACHE_SMOKE.json',report);print({'games':len(rows),'pass':report['pass'],'rows':[(r['map'],r['side'],r['draft'],r['play'],r['fuel']) for r in rows]},flush=True)
