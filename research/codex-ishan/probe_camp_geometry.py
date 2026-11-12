"""EXP233 public design census: no runtime state or strength experiment."""
from concurrent.futures import ThreadPoolExecutor
from shutil import copyfile
import subprocess
from zipfile import ZipFile

import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from qualify_local import partition


if __name__=='__main__':
    assert bench.digest(CLI)==CLI_HASH
    output=bench.CACHE/'camp-geometry-20261106';output.mkdir()
    project=SDK_ROOT/'bots/codex-camp-geometry-20261106';src=project/'src';src.mkdir(parents=True)
    copyfile(HERE/'camp_geometry_probe.cpp',src/'main.cpp')
    wasm=project/'bot.wasm'
    with (project/'build.log').open('xb') as log:
        subprocess.run([CLI,'build',project,'--release','--output',wasm],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    maps=sorted(partition('dev'),key=lambda p:bench.digest(p));assert len(maps)==90
    ref=SDK_ROOT/'bots/offset-aoe-idle-20261106/bot.wasm'
    assert bench.digest(ref)==read(HERE/'OFFSET_AOE_ACTION_PROOF.json')['builds']['idle']
    pins={'engine':ENGINE,'cli':CLI_HASH,'wasm':bench.digest(wasm),'source':bench.digest(src/'main.cpp'),
          'sdk':bench.digest(SDK_ROOT/'sdk/cpp/cambc.h'),'reference':bench.digest(ref),
          'maps':{p.name:bench.digest(p) for p in maps},'games':90,'scope':'Public initial geometry/design potential only; ordinary charged draft, no runtime/strength claim.'}
    write(HERE/'CAMP_GEOMETRY_PLAN.json',pins)
    def run(mp):
        directory=output/mp.stem;directory.mkdir()
        with (directory/'run.log').open('xb') as log:
            subprocess.run([CLI,'run',wasm,ref,'--map',mp,'--release','--fuel','100000','--json','--log-limit','100000',
                            '--statistics',directory/'native.json','--out-dir',directory],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        native=read(directory/'native.json')
        assert (native['match']['engineVersion'],native['match']['engineBuildHash'])==('3.0.0',ENGINE)
        assert native['match']['mapHash']==bench.digest(mp) and native['diagnostics']['detailedCaptureComplete']
        archive,=directory.glob('*.repl26a')
        with ZipFile(archive) as z:stdout=z.read('team-a.stdout').replace(b'\0',b'').decode('utf8')
        groups={};geometry=None;cost=None
        for line in stdout.splitlines():
            fields=line.split()
            if not fields:continue
            if fields[0]=='GEOMETRY':
                assert geometry is None;geometry=list(map(int,fields[1:]))
            elif fields[0]=='GROUP':
                h,gold,gems,respawn,n=map(int,fields[1:]);assert h not in groups
                groups[h]={'handle':h,'gold':gold,'gems':gems,'respawn':respawn,'count':n,'camps':[]}
            elif fields[0]=='CAMP':
                h,handle,kind,x,y=map(int,fields[1:6]);hp,strength=float(fields[6]),float(fields[7]);attack_range=int(fields[8])
                groups[h]['camps'].append({'handle':handle,'type':kind,'x':x,'y':y,'hp':hp,'strength':strength,'range':attack_range})
            elif fields[0]=='GEOMETRY_COST':
                assert cost is None;cost=int(fields[1])
        assert geometry and cost and len(groups)==geometry[2] and all(len(g['camps'])==g['count'] for g in groups.values())
        errors=bool(native['diagnostics']['codes'] or any(native['diagnostics']['botFaults'].values()))
        fuel=sum(len(e['entries']) for e in native['events'] if e['kind']=='fuelExhausted')
        return {'map':mp.stem,'map_sha256':bench.digest(mp),'directory':directory.relative_to(bench.ROOT).as_posix(),
                'native_sha256':bench.digest(directory/'native.json'),'archive_sha256':bench.digest(archive),
                'stdout':stdout,'width':geometry[0],'height':geometry[1],'groups':list(groups.values()),
                'charged_draft_cost':cost,'errors':errors,'fuel':fuel}
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(run,maps):
            rows.append(row)
            if len(rows)%15==0:print(f'{len(rows)}/90',flush=True)
    report={'pins':pins,'rows':rows,'errors':sum(r['errors'] for r in rows),'fuel':sum(r['fuel'] for r in rows)}
    write(HERE/'CAMP_GEOMETRY_RAW.json',report)
    print({'maps':len(rows),'errors':report['errors'],'fuel':report['fuel']},flush=True)
