"""EXP226 broad charged frozen-frame evaluation, with unavailable captures retained."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from shutil import copytree
import json
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from profile_live111_first import exact_build
from qualify_local import partition


def prepare(src,enabled,skip):
    identity=read(HERE/'LIVE111_SOURCE_VERIFIED.json');original=SDK_ROOT/'bots/live111/src'
    assert all(bench.digest(original/n)==h for n,h in identity['source_file_hashes'].items())
    copytree(original,src)
    header=src/'common.h';header.write_bytes(f'#define CODEX_FRAME_PROOF {int(enabled)}\n#define CODEX_FRAME_SKIP {skip}\n'.encode()+header.read_bytes())
    (src/'coherent_nn_frame_v2.h').write_bytes((HERE/'coherent_nn_frame_v2.h').read_bytes())
    p=src/'nnrec.cpp';data=p.read_text(encoding='utf8');anchor='#include "bot.h"';assert data.count(anchor)==1
    data=data.replace(anchor,anchor+'\n#if CODEX_FRAME_PROOF\n#include "coherent_nn_frame_v2.h"\n#endif')
    start=data.index('    if (nn_warm == 2 && f0 >= nn_est_camps');end=data.index('        const std::uint64_t f1 = bc::fuel_remaining();',start)
    body=data[start:end]
    anchor='        nn::live_camps(nn_lf, nn_lv, w.groups.size());\n        cmark(1);';assert body.count(anchor)==1
    body=body.replace(anchor,'''#if CODEX_FRAME_PROOF
        static unsigned proof_seen=0;
        static codex_frame2::Frame<kNF> proof_frame;
        const bool proof_active=(++proof_seen==CODEX_FRAME_SKIP+1);
        std::uint32_t proof_hash=0;
        bool proof_admitted=false;
        std::uint64_t copy_cost=0;
        if(proof_active) {
            const auto left=bc::fuel_remaining();const auto at=bc::round_number();
            proof_admitted=proof_frame.begin(nn_lf,nn_lv,w.groups.size(),round,nn_xdone==15);
            copy_cost=100000ull*(bc::round_number()-at)+left-bc::fuel_remaining();
            proof_hash=proof_frame.input_hash();
        }
#endif
'''+anchor)
    anchor='            if (!w.enemies.empty() && fe0 >= nn_xest[0] + 12000 + floor_f) {';assert body.count(anchor)==1
    body=body.replace(anchor,'''            if (
#if CODEX_FRAME_PROOF
                !proof_active &&
#endif
                !w.enemies.empty() && fe0 >= nn_xest[0] + 12000 + floor_f) {''')
    body+='''#if CODEX_FRAME_PROOF
        if(proof_active) {
            float reference[nn::kNC+1];std::copy(nn_lo.target,nn_lo.target+nn::kNC+1,reference);
            const bool original_ready=nn_lv.z_ok;
            std::uint64_t costs[5]{};
            for(int stage=0;stage<5;++stage) {
                if(stage) bc::end_turn(); // local numerical diagnostic only
                const auto left=bc::fuel_remaining();const auto at=bc::round_number();
                proof_frame.advance();
                costs[stage]=100000ull*(bc::round_number()-at)+left-bc::fuel_remaining();
            }
            const bool equal=std::memcmp(reference,proof_frame.output.target,sizeof(reference))==0;
            const bool immutable=!proof_admitted||proof_hash==proof_frame.input_hash();
            std::printf("FRAME_PROOF %d %d %u %d %d %d %d %u %d %d %llu %llu %llu %llu %llu %llu %d %d %d %d\\n",
                static_cast<int>(type),proof_frame.captured_at,bc::round_number(),equal,original_ready&&proof_frame.ready(),immutable,
                proof_frame.fresh(bc::round_number(),A2_NN_LAZY_TTL),static_cast<unsigned>(w.groups.size()),static_cast<int>(w.enemies.size()),CODEX_FRAME_SKIP,
                static_cast<unsigned long long>(copy_cost),static_cast<unsigned long long>(costs[0]),static_cast<unsigned long long>(costs[1]),
                static_cast<unsigned long long>(costs[2]),static_cast<unsigned long long>(costs[3]),static_cast<unsigned long long>(costs[4]),proof_admitted,nn_xdone,original_ready,proof_frame.ready());
            bc::resign();
        }
#endif
'''
    p.write_text(data[:start]+body+data[end:],encoding='utf8',newline='\n')


if __name__=='__main__':
    assert bench.digest(CLI)==CLI_HASH
    out=bench.CACHE/'coherent-nn-frame-broad-v2-20261106';out.mkdir()
    maps=partition('dev');ref=bench.CACHE/bench.OPPS['v92'][0];assert bench.digest(ref)==bench.OPPS['v92'][1]
    write(HERE/'COHERENT_NN_FRAME_BROAD_V2_PLAN.json',{'scope':'Controlled snapshot numerical equality only; optional enemy mid-refresh suppressed during capture,not gameplay/safety equivalence',
          'engine':ENGINE,'cli':CLI_HASH,'maps':{p.name:bench.digest(p) for p in maps},'opponent':bench.digest(ref),'capture_skips':[0,31],'games':360,'readiness_contract':'Actual nn_xdone==15; incomplete inputs must be explicitly declined and counted','frame_header_sha256':bench.digest(HERE/'coherent_nn_frame_v2.h')})
    sources={}
    for name,enabled,skip in (('off',False,0),('cold',True,0),('steady',True,31)):
        src=out/(name+'-source');prepare(src,enabled,skip);sources[name]=src
    def build(name):
        wasm=exact_build(sources[name],SDK_ROOT/'bots'/('coherent-frame-broad-v2-'+name+'-20261106'),1)
        print('build',name,bench.digest(wasm),flush=True);return name,wasm
    with ThreadPoolExecutor(max_workers=2) as pool:wasms=dict(pool.map(build,sources))
    assert bench.digest(wasms['off'])==read(HERE/'LIVE111_SOURCE_VERIFIED.json')['wasm_sha256']
    write(HERE/'COHERENT_NN_FRAME_BROAD_V2_BUILDS.json',{n:bench.digest(p) for n,p in wasms.items()})
    for name in ('cold','steady'):(out/name).mkdir()
    def run(job):
        name,mp,side=job;directory=out/name/f'{mp.stem}-{side}';directory.mkdir()
        bots=(wasms[name],ref) if side=='A' else (ref,wasms[name])
        with (directory/'run.log').open('xb') as log:
            subprocess.run([CLI,'run',*bots,'--map',mp,'--release','--fuel','100000','--json','--log-limit','50000','--statistics',directory/'native.json','--out-dir',directory],
                           cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        doc=read(directory/'native.json');assert (doc['match']['engineVersion'],doc['match']['engineBuildHash'])==('3.0.0',ENGINE) and doc['diagnostics']['detailedCaptureComplete']
        assert doc['match']['mapHash']==bench.digest(mp)
        archive,=directory.glob('*.repl26a')
        with ZipFile(archive) as z:stdout=z.read('team-'+side.lower()+'.stdout').replace(b'\x00',b'').decode('utf8')
        proofs=[list(map(int,s.split()[1:])) for s in stdout.splitlines() if s.startswith('FRAME_PROOF ')]
        assert len(proofs)<=1
        v=proofs[0] if proofs else None
        errors=bool(doc['diagnostics']['codes'] or any(doc['diagnostics']['botFaults'].values()))
        admitted=bool(v and len(v)==20 and v[16])
        numerical=bool(v and len(v)==20 and admitted and v[17]==15 and v[18:20]==[1,1] and v[3:6]==[1,1,1] and v[6]==0 and v[2]-v[1]>2)
        rejected=bool(v and len(v)==20 and not admitted and v[17]!=15 and v[18:20]==[0,0] and v[6]==0)
        valid=numerical or rejected
        fuel=[x['timestamp']['round'] for e in doc['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')=='team'+side for x in e['entries']]
        return {'capture':name,'map':mp.name,'side':side,'native_sha256':bench.digest(directory/'native.json'),'archive_sha256':bench.digest(archive),
                'available':v is not None,'admitted':admitted,'numerical_pass':numerical,'readiness_rejection_pass':rejected,'proof':v,'valid':valid,'errors':errors,'own_fuel_outs':len(fuel),'round1_fuel_outs':fuel.count(1)}
    jobs=[(name,mp,side) for mp in maps for side in 'AB' for name in ('cold','steady')];rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(run,jobs):
            rows.append(r)
            if len(rows)%30==0:print(f'{len(rows)}/{len(jobs)}',flush=True)
    available=[r for r in rows if r['available']]
    result={'scope':'Numerical prerequisite only; diagnostic owner-turn yields and controlled frozen reference do not establish a production executor',
            'admitted_frames':sum(r['admitted'] for r in available),'readiness_rejections':sum(r['readiness_rejection_pass'] for r in available),'games':len(rows),'available':len(available),'unavailable':len(rows)-len(available),'failures':sum(not r['valid'] for r in available),
            'error_games':sum(r['errors'] for r in rows),'capture_counts':dict(Counter(r['capture'] for r in available)),
            'type_counts':dict(Counter(r['proof'][0] for r in available)),'pass':bool(available) and all(r['valid'] for r in available) and not any(r['errors'] for r in rows),'rows':rows}
    write(HERE/'COHERENT_NN_FRAME_BROAD_V2_PROOF.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2),flush=True)
