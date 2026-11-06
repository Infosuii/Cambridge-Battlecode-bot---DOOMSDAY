"""EXP218 controlled action proof; no production policy or outcome selection."""
from concurrent.futures import ThreadPoolExecutor
import json
from shutil import copyfile
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI, CLI_HASH, ENGINE, HERE, SDK_ROOT, read
from freeze_engine3_discovery import write
from qualify_local import partition

if __name__=='__main__':
    out=bench.CACHE/'offset-aoe-action-20261106';out.mkdir()
    maps=sorted(partition('dev'),key=lambda p:bench.digest(p))[:3]
    settings={'idle':(0,0,1),'ryth':(0,0,0),'stellar':(5,4,0),'prism':(6,5,0)}
    assert bench.digest(CLI)==CLI_HASH
    write(HERE/'OFFSET_AOE_ACTION_PLAN.json',{'scope':'Mechanics only,forced local draft/idle opponent,normal charged100k',
          'engine':ENGINE,'cli':CLI_HASH,'source_sha256':bench.digest(HERE/'offset_aoe_probe.cpp'),
          'maps':{p.name:bench.digest(p) for p in maps},'settings':settings,'games':9})
    def build(item):
        name,(type_id,draft,idle)=item
        project=SDK_ROOT/'bots'/('offset-aoe-'+name+'-20261106');src=project/'src';src.mkdir(parents=True)
        data=(HERE/'offset_aoe_probe.cpp').read_bytes()
        (src/'main.cpp').write_bytes(f'#define PROBE_TYPE {type_id}\n#define PROBE_DRAFT {draft}\n#define PROBE_IDLE {idle}\n'.encode()+data)
        wasm=project/'bot.wasm'
        with (project/'build.log').open('xb') as log:
            subprocess.run([CLI,'build',project,'--release','--output',wasm],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        return name,wasm
    with ThreadPoolExecutor(max_workers=2) as pool:wasms=dict(pool.map(build,settings.items()))
    releases={n:bench.digest(p) for n,p in wasms.items()}
    def run(job):
        name,mp=job;directory=out/(name+'-'+mp.stem);directory.mkdir()
        with (directory/'run.log').open('xb') as log:
            subprocess.run([CLI,'run',wasms[name],wasms['idle'],'--map',mp,'--release','--fuel','100000','--json','--log-limit','50000',
                            '--statistics',directory/'native.json','--out-dir',directory],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        doc=read(directory/'native.json')
        assert (doc['match']['engineVersion'],doc['match']['engineBuildHash'])==('3.0.0',ENGINE) and doc['diagnostics']['detailedCaptureComplete']
        archive,=directory.glob('*.repl26a')
        with ZipFile(archive) as z:stdout=z.read('team-a.stdout').replace(b'\x00',b'').decode('utf8')
        lines=stdout.splitlines();observed=[list(map(float,l.split()[1:])) for l in lines if l.startswith('OFFSET_RESULT ')]
        assert len(observed)<=1
        v=observed[0] if observed else None
        passed=bool(v and len(v)==15 and v[9]==1 and v[10]>v[11] and max(abs(v[3]-v[5]),abs(v[4]-v[6]))==5 and max(abs(v[3]-v[7]),abs(v[4]-v[8]))<=4)
        return {'champion':name,'map':mp.name,'map_sha256':bench.digest(mp),'archive_sha256':bench.digest(archive),
                'native_sha256':bench.digest(directory/'native.json'),'observed':v,'stdout':stdout,'action_damage_proof':passed,'diagnostics':doc['diagnostics']}
    with ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,[(n,p) for n in settings if n!='idle' for p in maps]))
    result={'scope':'Controlled geometry/action proof,not current-source opportunity frequency or strength', 'builds':releases,
            'rows':rows,'proofs':sum(r['action_damage_proof'] for r in rows),'games':len(rows)}
    write(HERE/'OFFSET_AOE_ACTION_PROOF.json',result)
    print(json.dumps(result,indent=2),flush=True)
