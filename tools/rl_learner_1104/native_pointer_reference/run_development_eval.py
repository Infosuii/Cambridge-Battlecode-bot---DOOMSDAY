"""Frozen matched evaluation of initial/learned native-query deployment policies."""
from pathlib import Path
import concurrent.futures as cf,hashlib,json,subprocess,time
r=Path(__file__).resolve().parents[1];project=r/'mac-project';out=r/'runs/native-query-update01-dev';assert not out.exists();out.mkdir()
manifest=json.loads((r.parent.parent/'outputs/rl-execution/EVALUATION_MAP_MANIFEST.json').read_text());maps=[m for m in manifest['maps'] if m['split']=='development'];assert len(maps)==15
bots={'u0':r/'native_pointer_reference/native_command_u0_deploy.wasm','u1':r/'native_pointer_reference/native_command_u1_deploy.wasm','native':project/'bots/jd-a2-seed-e3/.cambc/build-release/bot-injected.wasm','v92':project/'bots/jd-v92-mac/.cambc/build-release/bot-injected.wasm'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for m in maps:assert sha(project/'maps'/m['file'])==m['sha256']
pairs=[('u0','v92'),('u1','v92'),('native','v92'),('u0','native'),('u1','native')]
plan=dict(schema='jd-native-query-development-eval-v1',pairs=pairs,maps=maps,artifacts={k:dict(path=str(p),sha256=sha(p)) for k,p in bots.items()},fuel=100000,round_cap=2000,scope='DEVELOPMENT not sealed confirmation/ladder; no further candidate selection from this batch',policy='u0/u1 same categorical command policy,T=.5,v92bonus2,18kguard,compiledseed110401; collection logs and unused snapshot copies disabled in both',latest_agent2_branch='6c2244e268e36aa37819e4f6002b8820ba21e48a',opponent_limit='Two related frozen opponents; broad ladder claim requires more diverse current teams.')
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
