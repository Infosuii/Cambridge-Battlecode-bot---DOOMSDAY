"""Frozen paired local matches with complete native summaries and replay bundles."""
from pathlib import Path
import json,subprocess,concurrent.futures,hashlib,zipfile,time,os,sys,gzip,shutil
from project import ROOT,BASE,CLI,ARENA,ENGINE,ENGINE_HASH,save,sha,digest,check_stop
sys.path.insert(0,str(ROOT.parent))
from published_pool import verified_pool
STYLES=['b111','nnm4','v92','ref_x1','ref_x3ctr','ref_p65pack','ref_hold_rush100','teammate_max_gx','teammate_john_nnfinal']
def prepare_references():
    result={}
    for name in STYLES:
        if name=='b111':p=ARENA/'bots/b111/frozen.wasm'
        else:
            origin=BASE/'arena/bots'/name;spec=origin/'external-wasm.json'
            source=origin/json.loads(spec.read_text())['file'] if spec.exists() else origin/'.cambc/build-release/bot-injected.wasm'
            if spec.exists():assert sha(source)==json.loads(spec.read_text())['sha256']
            import shutil
            p=ARENA/'references'/(name+'.wasm');p.parent.mkdir(exist_ok=True)
            if not p.exists():shutil.copy2(source,p)
            assert sha(p)==sha(source)
        result[name]={'file':str(p),'sha256':sha(p)}
    save(ROOT/'references.json',result)
    catalog=json.loads((BASE/'autonomy/data/experiments/bounded-delivery-retune-20261107-platform-spotcheck/live-map-catalog.json').read_text())['maps']
    maps=verified_pool(BASE/'arena/maps',ROOT.parent/'live-map-audit-20261108/maps',catalog)
    save(ROOT/'published-maps.json',maps)
    return result,maps
def artifact(name):
    b=ARENA/'bots'/name
    return b/'frozen.wasm' if (b/'frozen.wasm').exists() else b/'.cambc/build-release/bot-injected.wasm'

def read_native(path):
    path=Path(path)
    with (gzip.open(path,'rt',encoding='utf-8') if path.suffix=='.gz' else path.open(encoding='utf-8')) as f:return json.load(f)

def storage_guard():
    check_stop()
    size=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
    if size>25*1024**3:raise RuntimeError('Local integration reached its 25 GiB storage cap; preserve work and prune reproducible outputs before proceeding')
def one(cell,folder,artifacts,debug=False):
    check_stop();candidate,opponent,mapfile,side=cell;key=hashlib.sha256(json.dumps(cell).encode()).hexdigest()[:12]
    d=folder/key;d.mkdir(exist_ok=True);summary=d/'native.json';bundle=d/'replays'
    packed=d/'native.json.gz'
    if not (summary.exists() or packed.exists()) or not list(bundle.glob('*.repl26a')):
        a,b=(candidate,opponent) if side=='a' else (opponent,candidate)
        args=[str(CLI),'run',artifacts[a]['file'],artifacts[b]['file'],'--map',mapfile,'-o',str(bundle),'--statistics',str(summary),'--json','--log-limit','67108864' if debug else '16384']
        if not debug:args+=['--release']
        with (d/'run.log').open('w',encoding='utf-8') as log:
            r=subprocess.run(args,cwd=ARENA,stdout=log,stderr=subprocess.STDOUT,timeout=240,env={**os.environ,'CAMBC_NO_UPDATE_CHECK':'1'})
        if r.returncode:raise RuntimeError('Local match process failed '+str(d))
    replay=list(bundle.glob('*.repl26a'));assert len(replay)==1 and zipfile.is_zipfile(replay[0]),str(d)
    n=read_native(summary if summary.exists() else packed);m=n['match'];diag=n['diagnostics'];us='team'+side.upper();other='teamB' if us=='teamA' else 'teamA'
    assert m['engineVersion']==ENGINE and m['engineBuildHash']==ENGINE_HASH
    assert diag['detailedCaptureComplete'] is True and m['outcome'] in ('teamA','teamB','draw')
    assert type(diag['botFaults'][us])==type(diag['botFaults'][other])==int
    assert m['mapHash'] and len(n['roster']['champions'])>0
    fuel=lambda team:sum(len(e['entries']) for e in n['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')==team)
    # Preserve complete captures losslessly without retaining oversized expanded JSON.
    if summary.exists():
        raw=summary.read_bytes()
        with gzip.open(packed,'wb',compresslevel=1) as f:f.write(raw)
        with gzip.open(packed,'rb') as f:assert f.read()==raw
        summary.unlink()
    summary=packed
    row={'candidate':candidate,'opponent':opponent,'map':Path(mapfile).stem,'map_file':mapfile,'map_sha256':sha(mapfile),'side':side,'score':1. if m['outcome']==us else .5 if m['outcome']=='draw' else 0.,
        'faults':diag['botFaults'][us],'opponent_faults':diag['botFaults'][other],'diagnostic_codes':diag['codes'],'fuel':fuel(us),'opponent_fuel':fuel(other),'rounds':m['roundsCompleted'],
        'summary':str(summary),'summary_sha256':sha(summary),'replay_bundle':str(replay[0]),'replay_sha256':sha(replay[0])}
    save(d/'cell.json',row);return row
def run(label,candidates,maps,opponents,workers=12,debug=False,schedule=None):
    storage_guard();folder=ROOT/'panels'/label;folder.mkdir(parents=True,exist_ok=True)
    refs=json.loads((ROOT/'references.json').read_text());artifacts={k:refs[k] for k in opponents}
    for n in candidates:
        p=ARENA/'bots'/n/'.cambc/build/bot-injected.wasm' if debug else artifact(n)
        artifacts[n]={'file':str(p),'sha256':sha(p)}
    cells=[(c,o,str(m),side) for c in candidates for o in opponents for m in maps for side in ('a','b')]
    if schedule is not None:
        cells=schedule
        assert all(c in candidates and o in opponents and str(m) in set(map(str,maps)) and side in ('a','b') for c,o,m,side in cells)
    manifest={'label':label,'candidates':candidates,'opponents':opponents,'artifacts':artifacts,'maps':{str(m):sha(m) for m in maps},'engine':ENGINE,'engine_hash':ENGINE_HASH,'fuel':'default; no fuel override','release':not debug,'cells':len(cells)}
    if schedule is not None:manifest['schedule']=[list(c) for c in schedule]
    p=folder/'manifest.json'
    if p.exists():assert json.loads(p.read_text())==manifest,'Frozen panel inputs changed'
    else:save(p,manifest)
    rows=[];start=time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs=[pool.submit(one,cell,folder,artifacts,debug) for cell in cells]
        for f in concurrent.futures.as_completed(jobs):
            rows.append(f.result())
            if len(rows)%20==0 or len(rows)==len(cells):
                state={'complete':len(rows),'total':len(cells),'elapsed_seconds':round(time.monotonic()-start,1),'faults':sum(r['faults']+r['opponent_faults'] for r in rows)}
                save(folder/'progress.json',state);print(json.dumps(state),flush=True)
    assert len(rows)==len(cells) and len({(r['candidate'],r['opponent'],r['map_file'],r['side']) for r in rows})==len(cells)
    for v in artifacts.values():assert sha(v['file'])==v['sha256']
    save(folder/'results.json',rows)
    scores={n:{'games':len(rs),'score':sum(r['score'] for r in rs),'faults':sum(r['faults'] for r in rs),'opponent_faults':sum(r['opponent_faults'] for r in rs),'fuel':sum(r['fuel'] for r in rs)} for n in candidates if (rs:=[r for r in rows if r['candidate']==n])}
    save(folder/'scores.json',scores);print(json.dumps(scores,indent=2),flush=True);return rows
if __name__=='__main__':
    refs,pool=prepare_references();names=['00the_line','01islands','03homonoliths','00happy_halloween','02guardians','00rows','00vault','04comb']
    chosen=[Path(next(r['file'] for r in pool if r['name']==name)) for name in names]
    run('merge-smoke-v1',['b111','b113','bterm','m00','m15'],chosen,['b111','nnm4','ref_x1','teammate_max_gx'])
