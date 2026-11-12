"""EXP278: legal isolated single-attack observations; no policy/outcome fitting."""
from concurrent.futures import ThreadPoolExecutor
import struct
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, read
from freeze_engine3_discovery import write
from qualify_local import partition


def floating(bits):
    return struct.unpack('<f',struct.pack('<I',bits))[0]


if __name__=='__main__':
    assert bench.digest(CLI)==CLI_HASH
    output=bench.CACHE/'varg-splash-20261106';output.mkdir()
    maps=sorted(partition('dev'),key=bench.digest)[:3]
    source=HERE/'varg_splash_probe.cpp'
    idle=SDK_ROOT/'bots/offset-aoe-idle-20261106/bot.wasm'
    assert bench.digest(idle)==read(HERE/'OFFSET_AOE_ACTION_PROOF.json')['builds']['idle']
    plan={'engine':ENGINE,'cli':CLI_HASH,'sdk':bench.digest(SDK_ROOT/'sdk/cpp/cambc.h'),
          'source':bench.digest(source),'idle':bench.digest(idle),'games':12,
          'maps':{p.name:bench.digest(p) for p in maps},'modes':{'nearest':0,'multi':1},
          'scope':'Legal basic-attack mechanics only; charged release100k, other actors idle, no spells/items.'}
    write(HERE/'VARG_SPLASH_PLAN.json',plan)
    builds={}
    for name,value in plan['modes'].items():
        project=SDK_ROOT/'bots'/f'varg-splash-{name}-20261106';src=project/'src';src.mkdir(parents=True)
        (src/'main.cpp').write_bytes(f'#define SELECT_MULTI {value}\n'.encode()+source.read_bytes())
        wasm=project/'bot.wasm'
        with (project/'build.log').open('xb') as log:
            subprocess.run([CLI,'build',project,'--release','--output',wasm],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        builds[name]={'path':str(wasm),'wasm':bench.digest(wasm),'source':bench.digest(src/'main.cpp')}
    write(HERE/'VARG_SPLASH_BUILDS.json',builds)
    def run(job):
        name,mp,side=job;directory=output/f'{name}-{mp.stem}-{side}';directory.mkdir()
        wasm=builds[name]['path'];bots=(wasm,idle) if side=='A' else (idle,wasm)
        with (directory/'run.log').open('xb') as log:
            subprocess.run([CLI,'run',*bots,'--map',mp,'--release','--fuel','100000','--json','--log-limit','100000',
                            '--statistics',directory/'native.json','--out-dir',directory],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        doc=read(directory/'native.json')
        assert (doc['match']['engineVersion'],doc['match']['engineBuildHash'])==('3.0.0',ENGINE)
        assert doc['match']['mapHash']==bench.digest(mp) and doc['diagnostics']['detailedCaptureComplete']
        archive,=directory.glob('*.repl26a')
        with ZipFile(archive) as z:stdout=z.read('team-'+side.lower()+'.stdout').replace(b'\0',b'').decode('utf8')
        attacks=[list(map(int,l.split()[1:])) for l in stdout.splitlines() if l.startswith('VARG_ATTACK ')]
        camps=[list(map(int,l.split()[1:])) for l in stdout.splitlines() if l.startswith('VARG_CAMP ')]
        unavailable=[l for l in stdout.splitlines() if l.startswith('VARG_UNAVAILABLE ')]
        assert len(attacks)+len(unavailable)==1 and 'VARG_ERROR' not in stdout
        if attacks:assert len(attacks[0])==13 and len(camps)==attacks[0][9] and all(len(c)==6 for c in camps)
        observation=None
        if attacks:
            a=attacks[0]
            observation={'round':a[0],'actor':a[1],'position':a[2:4],'group':a[4],'target':a[5],
                         'target_position':a[6:8],'strength':floating(a[8]),'partial':bool(a[10]),
                         'attack_snapshot_fuel':a[11],'rounds_crossed':a[12],
                         'camps':[{'id':c[0],'group':c[1],'position':c[2:4],'hp_before':floating(c[4]),'hp_after':floating(c[5]),
                                   'damage':floating(c[4])-floating(c[5])} for c in camps]}
        fuel=sum(len(e['entries']) for e in doc['events'] if e['kind']=='fuelExhausted')
        errors=bool(doc['diagnostics']['codes'] or any(doc['diagnostics']['botFaults'].values()))
        return {'mode':name,'map':mp.stem,'side':side,'directory':directory.relative_to(bench.ROOT).as_posix(),
                'native_sha256':bench.digest(directory/'native.json'),'archive_sha256':bench.digest(archive),
                'stdout':stdout,'observation':observation,'unavailable':unavailable,'fuel':fuel,'errors':errors}
    with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(run,[(n,m,s) for n in builds for m in maps for s in 'AB']))
    report={'plan_sha256':bench.digest(HERE/'VARG_SPLASH_PLAN.json'),'builds':builds,'rows':rows,'games':len(rows),
            'observed':sum(r['observation'] is not None for r in rows),'fuel':sum(r['fuel'] for r in rows),
            'errors':sum(r['errors'] for r in rows),'native_damage_audit':'PENDING; snapshots alone do not establish mechanics.'}
    write(HERE/'VARG_SPLASH_OBSERVATIONS.json',report)
    print({k:v for k,v in report.items() if k not in ('rows','builds')},flush=True)
