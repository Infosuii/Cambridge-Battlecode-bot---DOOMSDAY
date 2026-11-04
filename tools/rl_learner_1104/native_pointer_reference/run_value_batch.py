"""Collect a pinned native-query actor on a supplied TRAINING-only map list."""
from pathlib import Path
import argparse,concurrent.futures as cf,hashlib,json,shutil,subprocess,time
r=Path(__file__).resolve().parents[1];project=r/'mac-project'
ap=argparse.ArgumentParser();ap.add_argument('--maps',type=Path,required=True);ap.add_argument('--run',type=Path,required=True);ap.add_argument('--wasm',type=Path,required=True);ap.add_argument('--header',type=Path,required=True);ap.add_argument('--seed',type=int,required=True);a=ap.parse_args()
out=a.run.resolve();assert not out.exists();out.mkdir();maps=json.loads(a.maps.read_text());manifest=json.loads((r.parent.parent/'outputs/rl-execution/EVALUATION_MAP_MANIFEST.json').read_text());training={m['sha256'] for m in manifest['maps'] if m['split']=='training'}
assert len(maps)==8 and len({m['family'] for m in maps})==8 and all(m['sha256'] in training for m in maps)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for m in maps:assert sha(project/'maps'/m['file'])==m['sha256']
wasm=out/'collector.wasm';shutil.copyfile(a.wasm,wasm);shutil.copyfile(a.header,out/'policy_header.h')
opps={'v92':project/'bots/jd-v92-mac/.cambc/build-release/bot-injected.wasm','native':project/'bots/jd-a2-seed-e3/.cambc/build-release/bot-injected.wasm'}
source=r/'native-value-trial-actor/bots/submission/src';tree=hashlib.sha256(''.join(p.name+':'+sha(p)+'\n' for p in sorted(source.iterdir()) if p.is_file()).encode()).hexdigest()
plan=dict(schema='jd-native-upper-command-v3',mode='stochastic categorical',temperature=.5,v92_bonus=2,guard=18000,policy_seed=a.seed,candidate_wasm_sha256=sha(wasm),native_header_sha256=sha(out/'policy_header.h'),source_tree_sha256=tree,opponents={k:dict(path=str(v),sha256=sha(v)) for k,v in opps.items()},maps=maps,round_cap=2000,fuel=100000,action_semantics='target command to frozen downstream executor; may be cancelled/reassigned, not an executed-action label',seed_note='One actual compiled policy RNG seed per batch; no independent-seed claim for every game')
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def run(cell):
 m,opponent,side=cell;name=m['file'].split('.')[0]+'-'+opponent+'-'+side;directory=out/name;stats=out/(name+'.json')
 aa=['--label','native-query-train','--language','cpp',str(wasm)];bb=['--label',opponent+'-frozen','--language','cpp',str(opps[opponent])]
 if side=='B':aa,bb=bb,aa
 cmd=[str(r/'.venv/bin/cambc'),'__run-match','--rounds','2000','--map',str(project/'maps'/m['file']),'--outdir',str(directory),'--statistics',str(stats),'--json','--fuel-quantum','100000','--log-limit','67108864',*aa,'--',*bb]
 st=time.monotonic();p=subprocess.run(cmd,cwd=project,capture_output=True,text=True,timeout=900)
 z=dict(map=m['file'],family=m['family'],opponent=opponent,side=side,directory=name,returncode=p.returncode,seconds=time.monotonic()-st)
 if p.returncode:z['error']=p.stderr[-1500:]
 return z
st=time.monotonic()
with cf.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,[(m,o,s) for m in maps for o in opps for s in ('A','B')]))
assert sha(wasm)==plan['candidate_wasm_sha256'] and sha(out/'policy_header.h')==plan['native_header_sha256']
for k,v in opps.items():assert sha(v)==plan['opponents'][k]['sha256']
(out/'results.json').write_text(json.dumps(dict(wall_seconds=time.monotonic()-st,games=results),indent=2)+'\n');assert all(x['returncode']==0 for x in results)
print(json.dumps(dict(run=str(out),games=len(results),wall_seconds=time.monotonic()-st)),flush=True)
