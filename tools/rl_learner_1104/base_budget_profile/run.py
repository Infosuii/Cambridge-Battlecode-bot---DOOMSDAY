from pathlib import Path
import concurrent.futures as cf,hashlib,json,subprocess,time
r=Path(__file__).resolve().parent;project=r/'mac-project';out=r/'runs/base-budget-profile-01'
assert not out.exists();out.mkdir()
wasm=r/'base-budget-profile/compiled.wasm';opp=project/'bots/jd-v92-mac/.cambc/build-release/bot-injected.wasm'
manifest=json.loads((r.parent.parent/'outputs/rl-execution/EVALUATION_MAP_MANIFEST.json').read_text())
maps=['00reverse-spiral.map26a','02fields.map26a','02uncharted-lands.map26a','00stampede.map26a']
selected=[next(m for m in manifest['maps'] if m['file']==n) for n in maps]
assert all(m['split']=='training' for m in selected)
for m in selected:assert hashlib.sha256((project/'maps'/m['file']).read_bytes()).hexdigest()==m['sha256']
hash0=hashlib.sha256(wasm.read_bytes()).hexdigest()
(out/'plan.json').write_text(json.dumps(dict(candidate_sha256=hash0,opponent_sha256=hashlib.sha256(opp.read_bytes()).hexdigest(),maps=selected,fuel=100000,round_cap=2000,purpose='raw fuel profiling only, no strength conclusion'),indent=2))
def run(cell):
 m,side=cell;name=m['file'].split('.')[0]+'-'+side
 a=['--label','profile','--language','cpp',str(wasm)];b=['--label','v92','--language','cpp',str(opp)]
 if side=='B':a,b=b,a
 cmd=[str(r/'.venv/bin/cambc'),'__run-match','--rounds','2000','--map',str(project/'maps'/m['file']),'--outdir',str(out/name),'--statistics',str(out/(name+'.json')),'--json','--fuel-quantum','100000','--log-limit','16777216',*a,'--',*b]
 st=time.monotonic();p=subprocess.run(cmd,cwd=project,capture_output=True,text=True,timeout=900)
 res=dict(map=m['file'],side=side,directory=name,returncode=p.returncode,seconds=time.monotonic()-st)
 if p.returncode:res['error']=p.stderr[-1500:]
 print(json.dumps(res),flush=True);return res
st=time.monotonic()
with cf.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,[(m,s) for m in selected for s in ('A','B')]))
assert hashlib.sha256(wasm.read_bytes()).hexdigest()==hash0
(out/'results.json').write_text(json.dumps(dict(wall_seconds=time.monotonic()-st,cells=results),indent=2))
assert all(x['returncode']==0 for x in results)
