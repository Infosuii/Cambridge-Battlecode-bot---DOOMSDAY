"""EXP284 actual private Bot methods; diagnostic arrays, no engine-state edits."""
from concurrent.futures import ThreadPoolExecutor
import subprocess
from zipfile import ZipFile
import ablate_dev as bench
from engine3_pool import CLI,CLI_HASH,ENGINE,HERE,SDK_ROOT,read
from freeze_engine3_discovery import write
from qualify_local import partition
from live111_varg_capability import prepare
from prove_varg_geometry import bits
from audit_varg_cliques import geometry


def parse(stdout):
    groups=[]
    for line in stdout.splitlines():
        f=line.split()
        if not f:continue
        if f[0]=='VARG_WRAPPER_GROUP':
            v=list(map(int,f[1:]));groups.append({'handle':v[0],'n':v[1],'camps':[],'rows':[]})
        elif f[0]=='VARG_WRAPPER_CAMP':groups[-1]['camps'].append(list(map(int,f[1:])))
        elif f[0]=='VARG_WRAPPER':groups[-1]['rows'].append(list(map(int,f[1:])))
    assert stdout.splitlines().count('VARG_WRAPPER_DONE')==1
    assert all(len(g['camps'])==g['n'] and len(g['rows'])==12 for g in groups)
    return groups


def audit(groups,expected):
    from math import ceil
    from prove_varg_splash import floating
    checked=0
    assert len(groups)==len(expected)
    for g,old in zip(groups,expected,strict=True):
        assert g['handle']==old['handle']
        camps=[{'id':c[0],'position':c[1:3],'hp':floating(c[3]),'strength':floating(c[4])} for c in g['camps']]
        assert [(c['position'],c['hp'],c['strength']) for c in camps]==[([c['x'],c['y']],c['hp'],c['strength']) for c in old['camps']]
        adj,components,supported=geometry(camps)
        for v in g['rows']:
            assert len(v)==11 and v[0]==g['handle'];variant=v[1];assert variant in range(12)
            strength=12.5 if variant==4 else 93.75 if variant==5 else 50
            multiplier=1.5 if variant==10 else 1;damage=strength*multiplier
            hp=[];dead=[]
            for i,c in enumerate(camps):
                d=(variant==2 and i%2==1) or variant==3 or (variant==11 and i+1==len(camps));dead.append(d)
                h=c['hp']*.5 if variant==1 else camps[-1-i]['hp'] if variant==7 else 0 if variant==8 else 1 if variant in (9,10) and i==0 else c['hp']
                hp.append(c['hp'] if variant==8 else 0 if d else h)
            count=sum(ceil(max(h for i,h in enumerate(hp) if mask>>i&1)/damage) for mask in components) if supported else 0
            factor=floating(bits(sum(hp)/(damage*count))) if supported and count else floating(bits(1.6))
            expected_factor=bits(factor)
            assert v[2]==v[3]==expected_factor,(g['handle'],variant,v,expected_factor)
            dps=floating(bits(strength*(factor if len(camps)>1 else 1)))
            dps=max(1.0,floating(bits(dps*multiplier)))
            assert v[4]==bits(dps),(g['handle'],variant,v[4],bits(dps))
            # Independent Python target enumeration includes source input/range/visibility gates.
            pos=camps[variant%len(camps)]['position'];pos=[pos[0]-1,pos[1]+variant%3-1]
            best=None;key=None
            for i,c in enumerate(camps):
                if dead[i] or (variant%3==1 and i%2==1) or max(abs(pos[0]-c['position'][0]),abs(pos[1]-c['position'][1]))>1:continue
                h=c['hp']*.5 if variant==1 else camps[-1-i]['hp'] if variant==7 else 0 if variant==8 else 1 if variant in (9,10) and i==0 else c['hp']
                neighbours=sum(j!=i and not dead[j] and max(abs(c['position'][0]-o['position'][0]),abs(c['position'][1]-o['position'][1]))<=1 for j,o in enumerate(camps))
                candidate=floating(bits(h-floating(bits(c['strength']*1000))))
                candidate=floating(bits(candidate-neighbours*2000))
                if key is None or candidate<key:best=c['id'];key=candidate
            assert v[5]==v[6]==(-1 if best is None else best)
            checked+=1
    return checked


if __name__=='__main__':
    assert bench.digest(CLI)==CLI_HASH
    maps=sorted(partition('dev'),key=bench.digest)[:3];idle=SDK_ROOT/'bots/offset-aoe-idle-20261106/bot.wasm'
    assert bench.digest(idle)==read(HERE/'OFFSET_AOE_ACTION_PROOF.json')['builds']['idle']
    out=bench.CACHE/'varg-wrapper-proof-20261106';out.mkdir();project=SDK_ROOT/'bots/varg-wrapper-proof-20261106';src=project/'src'
    prepare(src,True,True)
    p=src/'bot.h';data=p.read_text(encoding='utf8');assert data.count('class Bot {')==1
    p.write_text(data.replace('class Bot {','class Bot {\n    friend void codex_varg_probe(Bot&,bool);'),encoding='utf8',newline='\n')
    p=src/'main.cpp';prefix=p.read_bytes().split(b'int main() {')[0];p.write_bytes(prefix+(HERE/'varg_wrapper_probe.cpp').read_bytes())
    sources={p.name:bench.digest(p) for p in src.iterdir() if p.is_file()}
    plan={'engine':ENGINE,'cli':CLI_HASH,'sources':sources,'prepare_sha256':bench.digest(HERE/'live111_varg_capability.py'),
          'probe_sha256':bench.digest(HERE/'varg_wrapper_probe.cpp'),'idle':bench.digest(idle),'maps':{p.name:bench.digest(p) for p in maps},'games':6,
          'scope':'Actual Bot method semantics on charged private mathematical arrays, no live-state edits or complete-game safety claim.'}
    write(HERE/'VARG_WRAPPER_PROOF_PLAN.json',plan)
    wasm=project/'bot.wasm'
    with (project/'build.log').open('xb') as log:subprocess.run([CLI,'build',project,'--release','--output',wasm],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    old={r['map']:r for r in read(HERE/'CAMP_GEOMETRY_RAW.json')['rows']}
    def run(job):
        mp,side=job;d=out/f'{mp.stem}-{side}';d.mkdir();bots=(wasm,idle) if side=='A' else (idle,wasm)
        with (d/'run.log').open('xb') as log:subprocess.run([CLI,'run',*bots,'--map',mp,'--release','--fuel','100000','--json','--log-limit','100000',
                '--statistics',d/'native.json','--out-dir',d],cwd=SDK_ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        n=read(d/'native.json');assert n['match']['engineBuildHash']==ENGINE and n['match']['mapHash']==bench.digest(mp) and n['diagnostics']['detailedCaptureComplete']
        archive,=d.glob('*.repl26a')
        with ZipFile(archive) as z:stdout=z.read('team-'+side.lower()+'.stdout').replace(b'\0',b'').decode('utf8')
        groups=parse(stdout);checked=audit(groups,old[mp.stem]['groups'])
        fuel=sum(len(e['entries']) for e in n['events'] if e['kind']=='fuelExhausted');errors=bool(n['diagnostics']['codes'] or any(n['diagnostics']['botFaults'].values()))
        return {'map':mp.stem,'side':side,'directory':d.relative_to(bench.ROOT).as_posix(),'native_sha256':bench.digest(d/'native.json'),
                'archive_sha256':bench.digest(archive),'stdout':stdout,'groups':groups,'checked':checked,'fuel':fuel,'errors':errors}
    with ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,[(m,s) for m in maps for s in 'AB']))
    result={'plan_sha256':bench.digest(HERE/'VARG_WRAPPER_PROOF_PLAN.json'),'wasm':bench.digest(wasm),'games':len(rows),'cases':sum(r['checked'] for r in rows),
            'fuel':sum(r['fuel'] for r in rows),'errors':sum(r['errors'] for r in rows),
            'crossed':sum(v[-1] for r in rows for g in r['groups'] for v in g['rows']),
            'max_cold_case_fuel':max(v[9] for r in rows for g in r['groups'] for v in g['rows']),'rows':rows}
    result['pass']=not(result['fuel'] or result['errors'] or result['crossed'])
    write(HERE/'VARG_WRAPPER_PROOF.json',result);print({k:v for k,v in result.items() if k!='rows'},flush=True)
