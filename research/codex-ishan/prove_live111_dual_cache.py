"""Check both static travel modes, malformed slots and exact draft parity on all dev maps."""
from concurrent.futures import ThreadPoolExecutor
import re
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from live111_dual_draft_cache import prepare
from profile_live111_first import exact_build
from prove_live111_draft_cache_full import CONTROLS
from qualify_local import partition

CHECKS=CONTROLS.replace('            w.bridges_on=false;','').replace('codex_field_cache::offset','slot')
CHECKS=CHECKS.replace('            std::printf("CACHE_REJECT %d\\n",corrupt);','')
MAIN=r'''#include "bot.h"
#include "draft.h"
#include "codex_field_cache.h"
#include <cstdio>
static void verify(World& w){
    codex_field_cache::bypass=true;w.field_order.clear();w.prepare_field_order();
    auto expected=std::move(w.field_order);
    codex_field_cache::bypass=false;
    const bool loaded=codex_field_cache::load(w),equal=loaded&&expected==w.field_order;
    const auto slot=w.bridges_on?codex_field_cache::second:codex_field_cache::offset;
__CHECKS__
    std::printf("DUAL_PROOF %d %d %d %zu %d\n",loaded,equal,corrupt,expected.size(),w.bridges_on);
}
int main(){
    while(true){
        if(bc::is_draft()){
            const bool first=bc::draft::current_draft(team::ally).empty();
            codex_field_cache::store();play_draft();
            if(first)std::printf("DUAL_DRAFT %llu %llu %d\n",(unsigned long long)codex_field_cache::draft_before,(unsigned long long)codex_field_cache::draft_after,codex_field_cache::memory_preserved);
        }else{
            World w;w.init();verify(w);
            w.enable_bridges();
            if(w.bridges_on)verify(w);
            else{w.bridges_on=true;w.field_order.clear();bool absent=!codex_field_cache::load(w)&&w.field_order.empty();w.bridges_on=false;std::printf("DUAL_ABSENT %d\n",absent);}
            bc::resign();
        }
        bc::end_turn();
    }
}'''.replace('__CHECKS__',CHECKS)

if __name__ == '__main__':
    matched=read(HERE/'LIVE109_RUNTIME_TARGET_CACHEMODE111.json')['rows'][0]
    assert matched['matched_view_and_prefix'] and matched['same_native_actor_round']
    assert any(s['mark']=='field_mode' and s['a']==1 for s in matched['samples'])
    previous=read(HERE/'LIVE111_DRAFT_CACHE_FULL_PROOF.json');assert previous['pass']
    base={ (r['map'],r['side']):r for r in previous['rows'] if r['arm']=='base'}
    maps=partition('dev');assert len(base)==180
    output=bench.CACHE/'live111-dual-cache-proof';output.mkdir()
    source=output/'off-source';prepare(source,False)
    off=exact_build(source,SDK_ROOT/'bots/live111-dual-cache-proof-off',1)
    assert bench.digest(off)==previous['off']==read(HERE/'LIVE111_SOURCE_VERIFIED.json')['wasm_sha256']
    source=output/'proof-source';prepare(source,True,True)
    (source/'main.cpp').write_text(MAIN,encoding='utf8',newline='\n')
    probe=exact_build(source,SDK_ROOT/'bots/live111-dual-cache-proof',1)
    ref=SDK_ROOT/'bots/v92-e3/bot.wasm';assert bench.digest(ref)==bench.OPPS['v92'][1] and bench.digest(CLI)==CLI_HASH
    write(HERE/'LIVE111_DUAL_CACHE_PROOF_PLAN.json',{'maps':{p.name:bench.digest(p) for p in maps},'off':bench.digest(off),'probe':bench.digest(probe),'schema':'Two248byte mode-tagged slots512/760,end1008,capacity116','baseline_manifest_sha256':bench.digest(HERE/'LIVE111_DRAFT_CACHE_FULL_PROOF.json'),'new_probe_games':180,'reused_completed_controls':180})
    def run(job):
        mp,side=job;prior=base[mp.stem,side]
        native=bench.ROOT/prior['directory']/'native.json';assert bench.digest(native)==prior['native_sha256']
        original=read(native)
        directory=output/f'{mp.stem}-{side}';directory.mkdir()
        bots=(probe,ref) if side=='A' else (ref,probe)
        with (directory/'run.log').open('wb') as log:
            subprocess.run([CLI,'run',*bots,'--map',mp,'--release','--fuel','100000','--rounds','5','--log-limit','1048576','--statistics',directory/'native.json','--out-dir',directory,'--json'],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        doc=read(directory/'native.json')
        assert doc['match']['engineVersion']=='3.0.0' and doc['match']['engineBuildHash']==ENGINE and doc['match']['mapHash']==bench.digest(mp) and doc['diagnostics']['detailedCaptureComplete']
        assert all(doc['match'][k]==original['match'][k] for k in ('mapHash','engineBuildHash','seed'))
        (bundle,)=directory.glob('*.repl26a')
        with ZipFile(bundle) as z:stdout=z.read(f'team-{side.lower()}.stdout').replace(b'\0',b'')
        checks=[list(map(int,m)) for m in re.findall(rb'DUAL_PROOF (\d+) (\d+) (\d+) (\d+) (\d+)',stdout)]
        draft=[list(map(int,m)) for m in re.findall(rb'DUAL_DRAFT (\d+) (\d+) (\d+)',stdout)]
        absent=[int(m) for m in re.findall(rb'DUAL_ABSENT (\d+)',stdout)]
        errors=bool(doc['diagnostics']['codes']) or any(doc['diagnostics']['botFaults'].values())
        draft_fuel=[x for e in doc['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')=='team'+side for x in e['entries'] if x['timestamp'].get('phase')=='draft']
        parity=doc['roster']['draft']==original['roster']['draft']
        modes={p[4] for p in checks}
        passed=not errors and not draft_fuel and parity and checks and all(all(p[:3]) for p in checks) and (modes=={0,1} or modes=={0} and absent and all(absent)) and draft and all(x[0]>=1000000 and x[1]>0 and x[2] for x in draft)
        return {'map':mp.stem,'side':side,'map_hash':bench.digest(mp),'checks':checks,'draft_fuel':draft,'absent_mode_rejected':absent,'draft_equal':parity,'errors':errors,'draft_fuel_events':draft_fuel,'pass':bool(passed),'native_sha256':bench.digest(directory/'native.json'),'baseline_native_sha256':prior['native_sha256']}
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(run,[(p,s) for p in maps for s in 'AB']):
            rows.append(row)
            if len(rows)%30==0:print(f'{len(rows)}/180',flush=True)
    result={'engine':ENGINE,'new_games':len(rows),'reused_control_games':180,'off':bench.digest(off),'probe':bench.digest(probe),'pass':all(r['pass'] for r in rows),'failed':sum(not r['pass'] for r in rows),'travel_mode_checks':sum(any(c[4]==1 for c in r['checks']) for r in rows),'rows':rows}
    write(HERE/'LIVE111_DUAL_CACHE_PROOF.json',result)
    print({k:v for k,v in result.items() if k!='rows'},flush=True)
