"""EXP279: all-development legal Varg tasks, no production policy or wins."""
from concurrent.futures import ThreadPoolExecutor
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, read
from freeze_engine3_discovery import write
from qualify_local import partition
from prove_varg_splash import floating


def parse(stdout):
    task=None;design=[];frames=[]
    for line in stdout.splitlines():
        f=line.split()
        if not f:continue
        if f[0]=='VARG_TASK':
            assert task is None;task=list(map(int,f[1:]));assert len(task)==9
        elif f[0]=='VARG_DESIGN':
            v=list(map(int,f[1:]));assert len(v)==5
            design.append({'id':v[0],'position':v[1:3],'hp':floating(v[3]),'strength':floating(v[4])})
        elif f[0]=='VARG_STEP':
            v=list(map(int,f[1:]));assert len(v)==6
            frames.append({'round':v[0],'primary':v[1],'strength':floating(v[2]),'hp':floating(v[3]),'position':v[4:6],'camps':[]})
        elif f[0]=='VARG_HP':
            v=list(map(int,f[1:]));assert len(v)==3 and frames
            before,after=(None if b==2**32-1 else floating(b) for b in v[1:])
            frames[-1]['camps'].append({'id':v[0],'before':before,'after':after})
    assert task is not None and len(design)==task[7] and len(frames)==task[8]
    assert all(len(f['camps'])==len(design) for f in frames)
    return {'group':task[0],'actor':task[1],'first_round':task[2],'last_round':task[3],
            'initial_hp':floating(task[4]),'final_hp':floating(task[5]),'reason':task[6],'design':design,'frames':frames}


if __name__=='__main__':
    assert bench.digest(CLI)==CLI_HASH
    source=HERE/'varg_clear_probe.cpp';maps=sorted(partition('dev'),key=bench.digest);assert len(maps)==90
    idle=SDK_ROOT/'bots/offset-aoe-idle-20261106/bot.wasm'
    assert bench.digest(idle)==read(HERE/'OFFSET_AOE_ACTION_PROOF.json')['builds']['idle']
    output=bench.CACHE/'varg-clear-20261106';output.mkdir()
    plan={'engine':ENGINE,'cli':CLI_HASH,'sdk':bench.digest(SDK_ROOT/'sdk/cpp/cambc.h'),'source':bench.digest(source),
          'idle':bench.digest(idle),'maps':{p.name:bench.digest(p) for p in maps},'modes':{'multi':0,'isolated':1},'games':360,
          'scope':'Legal basic-only tasks, real100k release, R300/firstdeath/clear cutoff; all cases retained, no wins/policy fitting.'}
    write(HERE/'VARG_CLEAR_PLAN.json',plan)
    builds={}
    for mode,value in plan['modes'].items():
        project=SDK_ROOT/'bots'/f'varg-clear-{mode}-20261106';src=project/'src';src.mkdir(parents=True)
        (src/'main.cpp').write_bytes(f'#define SELECT_ISOLATED {value}\n'.encode()+source.read_bytes());wasm=project/'bot.wasm'
        with (project/'build.log').open('xb') as log:subprocess.run([CLI,'build',project,'--release','--output',wasm],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        builds[mode]={'path':str(wasm),'wasm':bench.digest(wasm),'source':bench.digest(src/'main.cpp')}
    write(HERE/'VARG_CLEAR_BUILDS.json',builds)
    def run(job):
        mode,mp,side=job;directory=output/f'{mode}-{mp.stem}-{side}';directory.mkdir()
        wasm=builds[mode]['path'];bots=(wasm,idle) if side=='A' else (idle,wasm)
        with (directory/'run.log').open('xb') as log:subprocess.run([CLI,'run',*bots,'--map',mp,'--release','--fuel','100000','--json','--log-limit','100000',
                    '--statistics',directory/'native.json','--out-dir',directory],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        doc=read(directory/'native.json');assert (doc['match']['engineVersion'],doc['match']['engineBuildHash'])==('3.0.0',ENGINE)
        assert doc['match']['mapHash']==bench.digest(mp) and doc['diagnostics']['detailedCaptureComplete']
        archive,=directory.glob('*.repl26a')
        with ZipFile(archive) as z:stdout=z.read('team-'+side.lower()+'.stdout').replace(b'\0',b'').decode('utf8')
        observation=parse(stdout)
        champion,=[c for c in doc['champions'] if c['id']==observation['actor'] and c['team']=='team'+side]
        damage=sum(c['before']-c['after'] for f in observation['frames'] for c in f['camps'] if c['before'] is not None and c['after'] is not None)
        native_damage=champion['metrics']['monsterDamageDone']
        fuel=sum(len(e['entries']) for e in doc['events'] if e['kind']=='fuelExhausted')
        errors=bool(doc['diagnostics']['codes'] or any(doc['diagnostics']['botFaults'].values()))
        return {'mode':mode,'map':mp.stem,'side':side,'map_hash':bench.digest(mp),'directory':directory.relative_to(bench.ROOT).as_posix(),
                'native_sha256':bench.digest(directory/'native.json'),'archive_sha256':bench.digest(archive),'stdout':stdout,
                'observation':observation,'snapshot_damage':damage,'native_damage':native_damage,'damage_equal':abs(damage-native_damage)<1e-5,
                'fuel':fuel,'errors':errors}
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(run,[(mode,mp,side) for mode in builds for mp in maps for side in 'AB']):
            rows.append(r)
            if len(rows)%30==0:print(f'{len(rows)}/360',flush=True)
    report={'plan_sha256':bench.digest(HERE/'VARG_CLEAR_PLAN.json'),'builds':builds,'rows':rows,'games':len(rows),
            'reason_counts':{mode:{str(reason):sum(r['mode']==mode and r['observation']['reason']==reason for r in rows) for reason in range(1,7)} for mode in builds},
            'fuel':sum(r['fuel'] for r in rows),'errors':sum(r['errors'] for r in rows),'damage_mismatches':sum(not r['damage_equal'] for r in rows)}
    write(HERE/'VARG_CLEAR_OBSERVATIONS.json',report);print({k:v for k,v in report.items() if k not in ('rows','builds')},flush=True)
