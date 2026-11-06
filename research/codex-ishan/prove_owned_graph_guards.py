"""EXP250: every check charged; no strength/timing result from paused guard fixtures."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from live111_owned_executor import prepare as base_prepare
from profile_live111_first import exact_build
from qualify_local import partition


def prepare(src,owner,probe):
    base_prepare(src,owner)
    p=src/'common.h';p.write_bytes(f'#define CODEX_OWNER_GUARD_PROOF {int(probe)}\n'.encode()+p.read_bytes())
    p=src/'nnrec.cpp';data=p.read_text(encoding='utf8')
    anchor='        cxowned_learn(cxowned_cost[cx_stage],cx_used);';assert data.count(anchor)==1
    data=data.replace(anchor,anchor+'\n#if CODEX_OWNER_GUARD_PROOF\n'+(HERE/'owned_guard_probe.inc').read_text(encoding='utf8')+'\n#endif')
    p.write_text(data,encoding='utf8',newline='\n')
    p=src/'main.cpp';data=p.read_text(encoding='utf8');anchor='        try {';assert data.count(anchor)==1
    data=data.replace(anchor,anchor+'''\n#if CODEX_OWNER_GUARD_PROOF
            if(!bc::is_draft()&&bc::round_number()>=160){std::printf("OWNER_GUARD_UNAVAILABLE %u\\n",bc::round_number());bc::resign();}
#endif''')
    p.write_text(data,encoding='utf8',newline='\n')


if __name__=='__main__':
    assert bench.digest(CLI)==CLI_HASH and read(HERE/'LIVE111_OWNED_EXECUTOR_MECHANISM_R3.json')['pass']
    output=bench.CACHE/'live111-owned-guards-20261106';output.mkdir()
    maps=sorted(partition('dev'),key=lambda p:bench.digest(p))[:3]
    ref=bench.CACHE/bench.OPPS['v92'][0];assert bench.digest(ref)==bench.OPPS['v92'][1]
    write(HERE/'LIVE111_OWNED_GUARDS_PLAN.json',{'experiment':250,'engine':ENGINE,'cli':CLI_HASH,
          'maps':{p.name:bench.digest(p) for p in maps},'games':6,'reference':bench.digest(ref),
          'probe_source':bench.digest(HERE/'owned_guard_probe.inc'),'scope':'Charged explicit pending-owner/expiry/synthetic mode-shape checks; not production latency/strength.'})
    builds={}
    for name,owner,probe in (('off',False,False),('releasecheck',True,False),('probe',True,True)):
        src=output/('source-'+name);prepare(src,owner,probe)
        wasm=exact_build(src,SDK_ROOT/'bots'/('live111-owned-guards-'+name+'-20261106'),1)
        builds[name]={'path':str(wasm),'sha256':bench.digest(wasm)};print(name,builds[name]['sha256'],flush=True)
    assert builds['off']['sha256']==read(HERE/'LIVE111_SOURCE_VERIFIED.json')['wasm_sha256']
    assert builds['releasecheck']['sha256']==read(HERE/'LIVE111_OWNED_EXECUTOR_BUILDS.json')['on']['sha256']
    write(HERE/'LIVE111_OWNED_GUARDS_BUILDS.json',builds)
    wasm=Path(builds['probe']['path'])
    def run(job):
        mp,side=job;d=output/f'{mp.stem}-{side}';d.mkdir();bots=(wasm,ref) if side=='A' else (ref,wasm)
        with (d/'run.log').open('xb') as log:
            subprocess.run([CLI,'run',*bots,'--map',mp,'--release','--fuel','100000','--json','--log-limit','50000',
                            '--statistics',d/'native.json','--out-dir',d],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        native=read(d/'native.json');assert native['match']['engineBuildHash']==ENGINE and native['match']['mapHash']==bench.digest(mp)
        assert native['diagnostics']['detailedCaptureComplete']
        archive,=d.glob('*.repl26a')
        with ZipFile(archive) as z:stdout=z.read('team-'+side.lower()+'.stdout').replace(b'\0',b'').decode('utf8')
        proofs=[list(map(int,s.split()[1:])) for s in stdout.splitlines() if s.startswith('OWNED_GUARDS ')]
        assert len(proofs)<=1;v=proofs[0] if proofs else None
        errors=bool(native['diagnostics']['codes'] or any(native['diagnostics']['botFaults'].values()))
        actor_fuel=[x['timestamp']['round'] for e in native['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')=='team'+side and v and e['owner'].get('id')==v[0] for x in e['entries']]
        interval=[r for r in actor_fuel if v and v[3]<=r<=v[4]]
        return {'map':mp.name,'side':side,'proof':v,'available':v is not None,'errors':errors,'actor_fuel_rounds':actor_fuel,'interval_fuel':interval,
                'pass':bool(v and len(v)==13 and v[6:]==[1]*7 and not interval and not errors),
                'native_sha256':bench.digest(d/'native.json'),'archive_sha256':bench.digest(archive),'stdout':stdout}
    with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(run,[(p,s) for p in maps for s in 'AB']))
    result={'games':len(rows),'available':sum(r['available'] for r in rows),'pass':len(rows)==6 and all(r['pass'] for r in rows),'rows':rows}
    write(HERE/'LIVE111_OWNED_GUARDS_PROOF.json',result);print(result,flush=True)
