"""EXP261: charged original-world differential codec fixture, all dev maps/both sides."""
from concurrent.futures import ThreadPoolExecutor
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from live111_dual_draft_cache import prepare
from profile_live111_first import exact_build
from qualify_local import partition

MAIN='''#include "bot.h"
#include "draft.h"
#include "codex_field_cache.h"
#include "grouped_bush_codec.h"
#include <cstdio>
__PROBE__
int main(){
    bool checked=false;
    for(;;){
        if(!bc::is_draft())bc::resign();
        codex_field_cache::store();
        if(!checked){codec_proof();checked=true;}
        play_draft();bc::end_turn();
    }
}
'''

if __name__=='__main__':
    assert bench.digest(CLI)==CLI_HASH
    capacity=read(HERE/'GROUPED_BUSH_CACHE_CAPACITY.json');index={r['map']:r for r in capacity['rows']}
    original=read(HERE/'LIVE111_DRAFT_CACHE_FULL_PROOF.json');assert original['pass']
    controls={(r['map'],r['side']):r for r in original['rows'] if r['arm']=='base'};assert len(controls)==180
    maps=sorted(partition('dev'),key=bench.digest);assert len(maps)==90
    output=bench.CACHE/'grouped-bush-codec-proof-20261106';output.mkdir();source=output/'source'
    prepare(source,True,True)
    (source/'grouped_bush_codec.h').write_bytes((HERE/'grouped_bush_codec.h').read_bytes())
    (source/'main.cpp').write_text(MAIN.replace('__PROBE__',(HERE/'grouped_bush_codec_probe.inc').read_text(encoding='utf8')),encoding='utf8',newline='\n')
    wasm=exact_build(source,SDK_ROOT/'bots/grouped-bush-codec-proof-20261106',1)
    ref=SDK_ROOT/'bots/v92-e3/bot.wasm';assert bench.digest(ref)==bench.OPPS['v92'][1]
    plan={'engine':ENGINE,'cli':CLI_HASH,'sdk':bench.digest(SDK_ROOT/'sdk/cpp/cambc.h'),'probe':bench.digest(wasm),
          'sources':{p.name:bench.digest(p) for p in source.iterdir() if p.is_file()},'reference':bench.digest(ref),
          'maps':{p.name:bench.digest(p) for p in maps},'new_probe_games':180,'reused_stock_draft_controls':180,
          'stock_manifest_sha256':bench.digest(HERE/'LIVE111_DRAFT_CACHE_FULL_PROOF.json'),
          'python_encoding_sha256':bench.digest(HERE/'GROUPED_BUSH_CACHE_CAPACITY.json'),
          'scope':'Normal charged first-draft codec, reverse-order IDs/masks and malformed-payload proof only; no production memory schema/cache or strength test.'}
    write(HERE/'GROUPED_BUSH_CODEC_PROOF_PLAN.json',plan)
    def run(job):
        mp,side=job;d=output/f'{mp.stem}-{side}';d.mkdir()
        prior=controls[mp.stem,side];path=bench.ROOT/prior['directory']/'native.json';assert bench.digest(path)==prior['native_sha256']
        baseline=read(path)
        bots=(wasm,ref) if side=='A' else (ref,wasm)
        with (d/'run.log').open('xb') as log:subprocess.run([CLI,'run',*bots,'--map',mp,'--release','--fuel','100000','--log-limit','100000','--json','--statistics',d/'native.json','--out-dir',d],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        doc=read(d/'native.json');assert doc['match']['engineBuildHash']==ENGINE and doc['match']['mapHash']==bench.digest(mp) and doc['diagnostics']['detailedCaptureComplete']
        assert doc['match']['seed']==baseline['match']['seed']
        archive,=d.glob('*.repl26a')
        with ZipFile(archive) as z:stdout=z.read('team-'+side.lower()+'.stdout').replace(b'\0',b'').decode('utf8')
        line,=[l for l in stdout.splitlines() if l.startswith('CODEC_PROOF ')]
        values=list(map(int,line.split()[1:]));assert len(values)==12
        width,height,groups,count,size,mismatch,mask_checks,rejected,tests,encode_decode_cost,cost,rounds=values
        line,=[l for l in stdout.splitlines() if l.startswith('CODEC_BYTES ')];payload=line[len('CODEC_BYTES '):]
        old=index[mp.stem];equal=payload==old['encoding_hex'] and count==old['components'] and size==old['encoded_bytes']
        draft_equal=doc['roster']['draft']==baseline['roster']['draft']
        errors=bool(doc['diagnostics']['codes'] or any(doc['diagnostics']['botFaults'].values()))
        fuel=sum(len(e['entries']) for e in doc['events'] if e['kind']=='fuelExhausted')
        passed=equal and draft_equal and not mismatch and mask_checks==count and rejected==tests and not rounds and not errors and not fuel
        return {'map':mp.stem,'map_hash':bench.digest(mp),'side':side,'values':values,'encoding_hex':payload,'python_encoding_equal':equal,
                'draft_equal':draft_equal,'errors':errors,'fuel':fuel,'pass':passed,'native_sha256':bench.digest(d/'native.json'),'archive_sha256':bench.digest(archive),'directory':d.relative_to(bench.ROOT).as_posix()}
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(run,[(mp,side) for mp in maps for side in 'AB']):
            rows.append(r)
            if len(rows)%30==0:print(f'{len(rows)}/180',flush=True)
    report={'pins':plan,'games':len(rows),'pass':all(r['pass'] for r in rows),'failed':sum(not r['pass'] for r in rows),
            'max_encode_decode_cost':max(r['values'][9] for r in rows),'max_full_reference_fixture_cost':max(r['values'][10] for r in rows),'rows':rows}
    write(HERE/'GROUPED_BUSH_CODEC_PROOF.json',report)
    print({k:v for k,v in report.items() if k not in ('pins','rows')},flush=True)
