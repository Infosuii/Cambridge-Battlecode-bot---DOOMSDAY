"""EXP282: charged public SDK geometry plus fixed mathematical state fixtures."""
from concurrent.futures import ThreadPoolExecutor
from math import ceil
import struct
import subprocess
from zipfile import ZipFile
import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from qualify_local import partition
from audit_varg_cliques import geometry
from prove_varg_splash import floating


def bits(x):return struct.unpack('<I',struct.pack('<f',x))[0]


def parse(stdout):
    groups=[]
    for line in stdout.splitlines():
        f=line.split()
        if not f:continue
        if f[0]=='VARG_GEOMETRY':
            v=list(map(int,f[1:]));assert len(v)==7
            groups.append({'handle':v[0],'n':v[1],'component_count':v[2],'cliques':bool(v[3]),'refusals':v[4],
                           'fuel':v[5],'crossed':v[6],'points':[],'components':[],'rows':[]})
        elif f[0]=='VARG_POINT':
            v=list(map(int,f[1:]));assert len(v)==5
            groups[-1]['points'].append({'index':v[0],'position':v[1:3],'hp':floating(v[3]),'adjacent':v[4]})
        elif f[0]=='VARG_COMPONENT':groups[-1]['components'].append(int(f[1]))
        elif f[0]=='VARG_CAPABILITY':
            v=list(map(int,f[1:]));assert len(v)==6;groups[-1]['rows'].append(v)
    assert stdout.splitlines().count('VARG_GEOMETRY_DONE')==1
    assert all(len(g['points'])==g['n'] and len(g['components'])==g['component_count'] and len(g['rows'])==12 for g in groups)
    return groups


def audit(groups,expected):
    assert len(groups)==len(expected);failures=[];checked=0
    for g,old in zip(groups,expected,strict=True):
        assert g['handle']==old['handle']
        assert [(p['position'],p['hp']) for p in g['points']]==[([c['x'],c['y']],c['hp']) for c in old['camps']]
        adj,components,supported=geometry(g['points'])
        assert [p['adjacent'] for p in g['points']]==adj and g['components']==components and g['cliques']==supported
        assert g['refusals']==4
        for variant,db,valid,count,factor,errors in g['rows']:
            damage=floating(db);assert damage in (12.5,50,93.75) and variant in range(4)
            hp=[p['hp'] if variant==0 else p['hp']*.5 if variant==1 else p['hp']*(i%2==0) if variant==2 else 0 for i,p in enumerate(g['points'])]
            wanted_count=0;wanted_factor=bits(1.6)
            if supported:
                for mask in components:
                    highest=max(h for i,h in enumerate(hp) if mask>>i&1)
                    turns=ceil(highest/damage)
                    assert turns*damage>=highest and (turns==0 or (turns-1)*damage<highest)
                    wanted_count+=turns
                if wanted_count:wanted_factor=bits(sum(hp)/(damage*wanted_count))
            assert (valid,count,factor,errors)==(int(supported),wanted_count,wanted_factor,0)
            checked+=1
        if g['crossed']:failures.append(g['handle'])
    return checked,failures


if __name__=='__main__':
    assert bench.digest(CLI)==CLI_HASH
    maps=sorted(partition('dev'),key=bench.digest);assert len(maps)==90
    sources=['varg_geometry_probe.cpp','varg_group_geometry.h'];project=SDK_ROOT/'bots/varg-geometry-proof-20261106';src=project/'src';src.mkdir(parents=True)
    for name in sources:(src/('main.cpp' if name.endswith('.cpp') else name)).write_bytes((HERE/name).read_bytes())
    idle=SDK_ROOT/'bots/offset-aoe-idle-20261106/bot.wasm';assert bench.digest(idle)==read(HERE/'OFFSET_AOE_ACTION_PROOF.json')['builds']['idle']
    out=bench.CACHE/'varg-geometry-proof-20261106';out.mkdir()
    plan={'engine':ENGINE,'cli':CLI_HASH,'sdk':bench.digest(SDK_ROOT/'sdk/cpp/cambc.h'),
          'sources':{n:bench.digest(HERE/n) for n in sources},'idle':bench.digest(idle),'maps':{p.name:bench.digest(p) for p in maps},
          'games':180,'states_per_group':12,'scope':'Pure mathematical arrays from SDK public design on normal100k turns, no engine-state edits or production safety claim.'}
    write(HERE/'VARG_GEOMETRY_PROOF_PLAN.json',plan)
    wasm=project/'bot.wasm'
    with (project/'build.log').open('xb') as log:subprocess.run([CLI,'build',project,'--release','--output',wasm],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    release={'path':str(wasm),'wasm':bench.digest(wasm),'sources':{p.name:bench.digest(p) for p in src.iterdir() if p.is_file()}}
    write(HERE/'VARG_GEOMETRY_PROOF_BUILD.json',release)
    old={r['map']:r for r in read(HERE/'CAMP_GEOMETRY_RAW.json')['rows']}
    def run(job):
        mp,side=job;d=out/f'{mp.stem}-{side}';d.mkdir();bots=(wasm,idle) if side=='A' else (idle,wasm)
        with (d/'run.log').open('xb') as log:subprocess.run([CLI,'run',*bots,'--map',mp,'--release','--fuel','100000','--json','--log-limit','100000',
                '--statistics',d/'native.json','--out-dir',d],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        n=read(d/'native.json');assert n['match']['engineBuildHash']==ENGINE and n['match']['mapHash']==bench.digest(mp) and n['diagnostics']['detailedCaptureComplete']
        archive,=d.glob('*.repl26a')
        with ZipFile(archive) as z:stdout=z.read('team-'+side.lower()+'.stdout').replace(b'\0',b'').decode('utf8')
        groups=parse(stdout);checked,crossed=audit(groups,old[mp.stem]['groups'])
        fuel=sum(len(e['entries']) for e in n['events'] if e['kind']=='fuelExhausted');errors=bool(n['diagnostics']['codes'] or any(n['diagnostics']['botFaults'].values()))
        return {'map':mp.stem,'side':side,'directory':d.relative_to(bench.ROOT).as_posix(),'native_sha256':bench.digest(d/'native.json'),
                'archive_sha256':bench.digest(archive),'stdout':stdout,'groups':groups,'checked':checked,'crossed':crossed,'fuel':fuel,'errors':errors}
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(run,[(mp,s) for mp in maps for s in 'AB']):
            rows.append(r)
            if len(rows)%30==0:print(f'{len(rows)}/180',flush=True)
    result={'plan_sha256':bench.digest(HERE/'VARG_GEOMETRY_PROOF_PLAN.json'),'release':release,'games':len(rows),'states':sum(r['checked'] for r in rows),
            'fuel':sum(r['fuel'] for r in rows),'errors':sum(r['errors'] for r in rows),'crossed':sum(len(r['crossed']) for r in rows),
            'max_cold_group_fuel':max(g['fuel'] for r in rows for g in r['groups']),'rows':rows}
    result['pass']=not(result['fuel'] or result['errors'] or result['crossed'])
    write(HERE/'VARG_GEOMETRY_PROOF.json',result);print({k:v for k,v in result.items() if k not in ('rows','release')},flush=True)
