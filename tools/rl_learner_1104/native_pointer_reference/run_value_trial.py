"""Bounded paired on-policy experiment: zero baseline vs frozen prior value.
Shared first rollout, then independent on-policy branches on matched map/seed
schedules. No development feedback inside the block; no platform actions.
"""
from pathlib import Path
import json,hashlib,shutil,re,subprocess,time,traceback
r=Path(__file__).resolve().parents[1];here=Path(__file__).parent;root=r/'runs/native-value-paired-01';assert not root.exists();root.mkdir()
project=r/'native-value-trial-actor';assert not project.exists();(project/'bots/submission').mkdir(parents=True);src=project/'bots/submission/src';shutil.copytree(r/'native-upper-actor/bots/submission/src',src)
for name in ('sdk','cmake'):(project/name).symlink_to(r/'mac-project'/name,target_is_directory=True)
assert '#define JD_NATIVE_LOG 1' in (src/'common.h').read_text() and '#define JD_NATIVE_DET 0' in (src/'common.h').read_text()
s=(here/'run_upper_batch.py').read_text().replace('native-upper-actor/bots/submission/src','native-value-trial-actor/bots/submission/src');(here/'run_value_batch.py').write_text(s)
manifest=json.loads((r.parent.parent/'outputs/rl-execution/EVALUATION_MAP_MANIFEST.json').read_text());reps={}
for m in sorted(manifest['maps'],key=lambda z:z['file']):
 if m['split']=='training':reps.setdefault(m['family'],m)
selected=sorted(reps.values(),key=lambda m:hashlib.sha256(('paired-value-training-v1:'+m['family']).encode()).hexdigest());assert len(selected)==40
schedule=[dict(cycle=i,seed=110601+i,maps=selected[8*i:8*(i+1)]) for i in range(5)]
previous=json.loads((r/'runs/native-upper-continuation-01/status.json').read_text());assert previous['stage']=='complete';base_ck=Path(previous['latest_checkpoint']);base_header=Path(previous['latest_header']);baseline=here/'frozen_prior_value.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=dict(experiment='Fixed prior state baseline vs zero; same5200param QATactor/PPO settings and initialization',shared_initial_games=32,subsequent_games_per_arm=128,total_fresh_games=288,baseline_sha256=sha(baseline),starting_checkpoint_sha256=sha(base_ck),starting_header_sha256=sha(base_header),cycles=schedule,evaluation='One scheduled matched greedy deployment comparison after all5 cycles; no dev-feedback scheduling or model selection inside block',fairness='Shared cycle0 onpolicy for identical initial actors; subsequent zero/value policies each collect their OWN trajectories on same mapfamily/side/opponent/compiled-RNGseed schedule. Family/origin overlap within shared cycle0 is intentional, not two independent samples.')
(root/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');status=dict(stage='preparing',completed=[]);start=time.monotonic();py=r/'.venv/bin/python';cli=r/'.venv/bin/cambc';arms={name:dict(checkpoint=base_ck,header=base_header) for name in ['zero','value']}
def save():
 status['elapsed_seconds']=time.monotonic()-start;(root/'status.json').write_text(json.dumps(status,indent=2)+'\n')
def command(args,log):
 with open(log,'w') as f:p=subprocess.run(list(map(str,args)),cwd=r.parent.parent,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
 if p.returncode:raise RuntimeError(str(log)+' exit '+str(p.returncode))
def collect(spec,arm,folder):
 folder.mkdir();(folder/'maps.json').write_text(json.dumps(spec['maps'],indent=2)+'\n');shutil.copyfile(arms[arm]['header'],src/'nn_weights.h');f=src/'nnrec.cpp';s=re.sub(r'#define CLNA_SEED \d+ // JD_CYCLE_SEED','#define CLNA_SEED '+str(spec['seed'])+' // JD_CYCLE_SEED',f.read_text());f.write_text(s)
 status['stage']='compile '+folder.name;save();command([cli,'__compile-bot',project],folder/'compile.log')
 status['stage']='collect '+folder.name;save();raw=folder/'raw';command([py,here/'run_value_batch.py','--maps',folder/'maps.json','--run',raw,'--wasm',project/'compiled.wasm','--header',src/'nn_weights.h','--seed',spec['seed']],folder/'collect.log')
 status['stage']='audit '+folder.name;save();data=folder/'data';command([py,here/'adapt_upper_value.py','--rawroot',raw,'--out',data,'--header',raw/'policy_header.h'],folder/'audit.log');return data,raw/'policy_header.h'
def train(spec,arm,data,header,folder):
 folder.mkdir();status['stage']='train '+folder.name;save();args=[py,here/('train_upper.py' if arm=='zero' else 'train_upper_value.py'),'--data',data,'--header',header,'--checkpoint',arms[arm]['checkpoint'],'--map-manifest',r.parent.parent/'outputs/rl-execution/EVALUATION_MAP_MANIFEST.json','--out',folder/'update']
 if arm=='value':args+=['--value-baseline',baseline]
 command(args,folder/'train.log');rep=json.loads((folder/'update/update_report.json').read_text());assert rep['optimizer_resumed'];arms[arm]=dict(checkpoint=folder/'update/upper.pt',header=folder/'update/nn_weights.h');status['completed'].append(dict(arm=arm,cycle=spec['cycle'],decisions=rep['decisions'],accepted_updates=rep['accepted_updates'],total_updates=rep['total_accepted_updates'],header_sha256=rep['export']['export_sha256'],full_kl=rep['final']['full_old_to_new_conditional_kl']));save()
save()
try:
 data,header=collect(schedule[0],'zero',root/'shared-cycle0')
 for arm in arms:train(schedule[0],arm,data,header,root/(arm+'-cycle0'))
 for spec in schedule[1:]:
  for arm in arms:
   folder=root/(arm+'-cycle'+str(spec['cycle']));data,header=collect(spec,arm,folder);train(spec,arm,data,header,root/(arm+'-update'+str(spec['cycle'])))
 status.update(stage='complete',arms={name:{k:str(v) for k,v in a.items()} for name,a in arms.items()});save();print(json.dumps(status,indent=2),flush=True)
except Exception as e:
 status.update(stage='failed',error=str(e));save();traceback.print_exc();raise
