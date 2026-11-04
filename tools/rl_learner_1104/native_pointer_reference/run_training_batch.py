"""32 distinct native-query training games on frozen training-only map schedule."""
from pathlib import Path
import concurrent.futures as cf,hashlib,json,subprocess,time
r=Path(__file__).resolve().parents[1];project=r/'mac-project';out=r/'runs/native-query-u0-flush-mac32'
assert not out.exists();out.mkdir()
schedule=json.loads((r.parent.parent/'outputs/rl-execution/CONDITIONAL_PILOT_SCHEDULE.json').read_text());maps=schedule['selected_maps']
manifest=json.loads((r.parent.parent/'outputs/rl-execution/EVALUATION_MAP_MANIFEST.json').read_text());train={m['sha256'] for m in manifest['maps'] if m['split']=='training'}
assert all(m['sha256'] in train for m in maps)
for m in maps:assert hashlib.sha256((project/'maps'/m['file']).read_bytes()).hexdigest()==m['sha256']
wasm=r/'native_pointer_reference/native_command_stochastic_u0_flush.wasm'
opps={'v92':project/'bots/jd-v92-mac/.cambc/build-release/bot-injected.wasm','native':project/'bots/jd-a2-seed-e3/.cambc/build-release/bot-injected.wasm'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=r/'native-query-actor/bots/submission/src';tree=hashlib.sha256(''.join(p.name+':'+sha(p)+'\n' for p in sorted(source.iterdir()) if p.is_file()).encode()).hexdigest()
plan=dict(schema='jd-native-query-command-v2',mode='stochastic categorical',temperature=.5,v92_bonus=2,guard=18000,policy_seed=110401,
 candidate_wasm_sha256=sha(wasm),native_header_sha256=sha(source/'nn_weights.h'),source_tree_sha256=tree,
 opponents={k:dict(path=str(p),sha256=sha(p)) for k,p in opps.items()},maps=maps,round_cap=2000,fuel=100000,
 action_semantics='target command to frozen downstream executor; may be cancelled/reassigned, not an executed-action label',
 source_base='0ea31bc with JOHNDOE native query/consumed-h1 overlay',host='Mac M2; SDK4 engine2; 2 concurrent games',
 seed_note='One actual compiled policy RNG seed. No claim of32 independent RNG streams; both sides/opponents/maps differ.')
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
def run(cell):
 m,opp,side=cell;name=m['file'].split('.')[0]+'-'+opp+'-'+side;directory=out/name;stats=out/(name+'.json')
 a=['--label','native-query-u0','--language','cpp',str(wasm)];b=['--label',opp+'-frozen','--language','cpp',str(opps[opp])]
 if side=='B':a,b=b,a
 cmd=[str(r/'.venv/bin/cambc'),'__run-match','--rounds','2000','--map',str(project/'maps'/m['file']),'--outdir',str(directory),'--statistics',str(stats),'--json','--fuel-quantum','100000','--log-limit','67108864',*a,'--',*b]
 st=time.monotonic();p=subprocess.run(cmd,cwd=project,capture_output=True,text=True,timeout=900)
 result=dict(map=m['file'],family=m['family'],opponent=opp,side=side,directory=name,returncode=p.returncode,seconds=time.monotonic()-st)
 if p.returncode:result['error']=p.stderr[-1500:]
 print(json.dumps(result),flush=True);return result
st=time.monotonic()
with cf.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,[(m,o,s) for m in maps for o in opps for s in ('A','B')]))
assert sha(wasm)==plan['candidate_wasm_sha256']
for k,p in opps.items():assert sha(p)==plan['opponents'][k]['sha256']
(out/'results.json').write_text(json.dumps(dict(wall_seconds=time.monotonic()-st,games=results),indent=2)+'\n')
assert all(x['returncode']==0 for x in results)
