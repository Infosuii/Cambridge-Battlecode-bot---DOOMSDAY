"""Frozen matched evaluation of initial/learned native-query deployment policies."""
from pathlib import Path
import concurrent.futures as cf,hashlib,json,subprocess,time
r=Path(__file__).resolve().parents[1];project=r/'mac-project';out=r/'runs/native-upper-commit8-dev';assert not out.exists();out.mkdir()
manifest=json.loads((r.parent.parent/'outputs/rl-execution/EVALUATION_MAP_MANIFEST.json').read_text());maps=[m for m in manifest['maps'] if m['split']=='development'];assert len(maps)==15
bots={'upper0':r/'native_pointer_reference/upper0_greedy_deploy.wasm','upper5':r/'native-upper-commit8/candidate.wasm','native':project/'bots/jd-a2-seed-e3/.cambc/build-release/bot-injected.wasm','v92':project/'bots/jd-v92-mac/.cambc/build-release/bot-injected.wasm'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for m in maps:assert sha(project/'maps'/m['file'])==m['sha256']
for name in ('decrest','khiri','wardens'):bots[name]=project/('bots/jd-public-'+name+'-frozen/.cambc/build-release/bot-injected.wasm')
pairs=[('upper5',b) for b in ('v92','native')]
public_maps=sorted(maps,key=lambda m:hashlib.sha256(('upper-public-dev-v1:'+m['family']+m['file']).encode()).hexdigest());selected=[];families=set()
for m in public_maps:
 if m['family'] not in families: selected.append(m);families.add(m['family'])
 if len(selected)==4:break
plan=dict(schema='jd-native-query-development-eval-v1',pairs=pairs,maps=maps,artifacts={k:dict(path=str(p),sha256=sha(p)) for k,p in bots.items()},fuel=100000,round_cap=2000,scope='DEVELOPMENT fixed8round commitment feasibility, not sealed confirmation or ladder. No claimed strength improvement before comparison.',policy='ISOLATED v107 fixed8round command hold versus cached exact v107. Same upper5 header, deterministic argmax command, v92bonus2,18kguard,logs off. Only target commitment added; same reserve1000. No checkpoint selection during this fixed60-game test.',latest_agent2_branch='6c2244e268e36aa37819e4f6002b8820ba21e48a',opponent_limit='Native/v92 full15devmaps plus3 older public policies on4outcome-independently selectedfamilies. Public pool is not current ladder strength proof.',public_maps=selected,extra_public_pairs=0)
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def run(cell):
 candidate,opponent,m,side=cell;name=candidate+'-vs-'+opponent+'-'+m['file'].split('.')[0]+'-'+side;directory=out/name;stats=out/(name+'.json')
 a=['--label',candidate,'--language','cpp',str(bots[candidate])];b=['--label',opponent,'--language','cpp',str(bots[opponent])]
 if side=='B':a,b=b,a
 cmd=[str(r/'.venv/bin/cambc'),'__run-match','--rounds','2000','--map',str(project/'maps'/m['file']),'--outdir',str(directory),'--statistics',str(stats),'--json','--fuel-quantum','100000','--log-limit','0',*a,'--',*b]
 st=time.monotonic();p=subprocess.run(cmd,cwd=project,capture_output=True,text=True,timeout=900)
 row=dict(candidate=candidate,opponent=opponent,map=m['file'],map_sha256=m['sha256'],family=m['family'],side=side,returncode=p.returncode,seconds=time.monotonic()-st,stats=str(stats))
 if p.returncode:row['error']=p.stderr[-1500:]
 else:
  d=json.loads(stats.read_text());row['diagnostics']=d['diagnostics']
  if d['diagnostics']['detailedCaptureComplete'] and not any(d['diagnostics']['botFaults'].values()):
   # Rich engine statistics retained. Discard generated replay/capture blobs
   # only for verified successful cases to keep evaluation storage small.
   for f in directory.iterdir():
    if f.is_file():f.unlink()
   directory.rmdir();row['raw_capture_discarded']=True
 print(name+' '+str(p.returncode),flush=True);return row
st=time.monotonic()
with cf.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,[(a,b,m,s) for a,b in pairs for m in maps for s in ('A','B')]))
for name,p in bots.items():assert sha(p)==plan['artifacts'][name]['sha256']
(out/'runs.json').write_text(json.dumps(dict(wall_seconds=time.monotonic()-st,games=rows),indent=2)+'\n');assert all(x['returncode']==0 for x in rows)
