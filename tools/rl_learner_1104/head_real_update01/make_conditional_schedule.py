"""Prepare disjoint training-only pilot assignments without viewing match outcomes."""
from pathlib import Path
import hashlib,json,numpy as np
root=Path(__file__).resolve().parents[1];out=root.parent.parent/'outputs/rl-execution'
manifest=json.loads((out/'EVALUATION_MAP_MANIFEST.json').read_text())
geometry=json.loads((out/'MAP_GEOMETRY_AUDIT.json').read_text())
old=json.loads((root/'head-real-batch/bundle/manifest.json').read_text())
by_hash={m['sha256']:m for m in manifest['maps']}
used_families={by_hash[e['map_sha256']]['family'] for e in old['episodes']}
g={m['file']:m for m in geometry['maps']}
# One representative per remaining training family; deterministic and outcome-free.
representatives={}
for m in sorted(manifest['maps'],key=lambda x:x['file']):
 if m['split']=='training' and m['family'] not in used_families:
  representatives.setdefault(m['family'],m)
rows=sorted(representatives.values(),key=lambda m:hashlib.sha256(('jd-cond-pilot:'+m['family']).encode()).hexdigest())
def features(m):
 z=g[m['file']];area=z['width']*z['height']
 return [np.log(area),z['width']/z['height'],z['tiles']['wall']/area,z['tiles']['hole']/area,
         z['tiles']['bush']/area,np.log1p(z['groups']),np.log1p(z['group_gold']),np.log1p(z['group_gems'])]
x=np.asarray([features(m) for m in rows]);scale=x.std(0);scale[scale==0]=1;x=(x-x.mean(0))/scale
chosen=[0]
while len(chosen)<8:
 dist=((x[:,None]-x[chosen][None,:])**2).sum(-1).min(-1)
 dist[chosen]=-1;chosen.append(int(dist.argmax()))
selected=[rows[i] for i in chosen]
for m in selected:
 assert hashlib.sha256((root/'mac-project/maps'/m['file']).read_bytes()).hexdigest()==m['sha256']
assert len({m['family'] for m in selected})==8
cells=[]
for temperature in (1,2):
 for j,m in enumerate(selected):
  for opponent in ('v92','frozen_native'):
   # Assign both sides together, half the families to each machine in each arm.
   host='PC' if j%2==0 else 'Mac'
   for side in ('A','B'):
    key=f'T{temperature}|{m["sha256"]}|{opponent}|{side}'
    cells.append(dict(cell_id=hashlib.sha256(key.encode()).hexdigest()[:20],temperature=temperature,
     initial_gate_probability=.02,map=m['file'],map_sha256=m['sha256'],family=m['family'],
     opponent=opponent,side=side,assigned_host=host,
     rng_seed=int(hashlib.sha256(('jd-cond-rng:'+m['sha256']+'|'+opponent+'|'+side).encode()).hexdigest()[:15],16)))
assert len(cells)==64 and len({c['cell_id'] for c in cells})==64
schedule=dict(schema='jd-conditional-pilot-schedule-v1',status='PREPARED_NOT_RUN_RUNTIME_ABI_AND_ARTIFACTS_PENDING',
 scope='Training-only rollout pilot; no development or reserved maps or outcome-based selection',
 selection='Exclude old Mac16 training families, one lexical representative per family; stable hashed start then greedy maximin standardized official static geometry/resource features. No match outcomes read.',
 map_manifest_sha256=hashlib.sha256((out/'EVALUATION_MAP_MANIFEST.json').read_bytes()).hexdigest(),
 excluded_previous_mac_families=sorted(used_families),selected_maps=selected,
 opponent_expected_mac_release_sha256={'v92':'b260ebe4ecb2a8df4de229f60e980b41160a57726741cf72a653fc377a687343',
 'frozen_native':'a48fe4423cb6a3f0f469266595d08038465288f82fbc67cbd68120a99db6b177'},
 fuel=100000,round_cap=2000,cells=cells,
 launch_requirements=['Pin collector commit, gate/head/feature ABI, weights, engine and per-host release artifact hashes.',
 'Runtime correctness and fuel-control comparison must pass before these runs.',
 'Seed must configure real policy RNG; a seed field alone does not make a run independent.',
 'Do not rebuild or change weights within an arm; do not overwrite completed cells.',
 'Collect complete stochastic gate rows and execution evidence; report all incomplete/failed games, no silent selective omission.',
 'Temperature changes full conditional scores and requires separate on-policy collection, not old-data relabeling.',
 'PC artifact hashes may differ with toolchain; pin and replay each host, compare controlled baseline behavior.',
 'This schedule does not seal the provisional confirmation split or establish unknown pretraining exposure.'],
 counts={'total':64,'per_arm':32,'per_host':32,'families':8})
p=out/'CONDITIONAL_PILOT_SCHEDULE.json';p.write_text(json.dumps(schedule,indent=2)+'\n')
print(json.dumps(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),maps=[m['file'] for m in selected],counts=schedule['counts']),indent=2))
