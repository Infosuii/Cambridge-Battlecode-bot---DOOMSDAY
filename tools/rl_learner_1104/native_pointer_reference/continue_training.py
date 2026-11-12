"""Four bounded fresh collect/audit/update cycles; no development feedback inside."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,time,traceback
r=Path(__file__).resolve().parents[1];here=Path(__file__).parent;src=r/'native-query-actor/bots/submission/src';py=r/'.venv/bin/python';cli=r/'.venv/bin/cambc';root=r/'runs/native-query-continuation-01';assert not root.exists();root.mkdir()
manifest=json.loads((r.parent.parent/'outputs/rl-execution/EVALUATION_MAP_MANIFEST.json').read_text());first=json.loads((here/'real_batch_u0/manifest.json').read_text());used={e['family'] for e in first['episodes']}
reps={}
for m in sorted(manifest['maps'],key=lambda z:z['file']):
 if m['split']=='training' and m['family'] not in used:reps.setdefault(m['family'],m)
remaining=sorted(reps.values(),key=lambda m:hashlib.sha256(('native-query-cycle-v1:'+m['family']).encode()).hexdigest())
assert len(remaining)==32
schedule=[dict(cycle=i+1,policy_seed=110402+i,maps=remaining[i*8:(i+1)*8]) for i in range(4)]
(root/'schedule.json').write_text(json.dumps(dict(selection='All32 remaining training families; one lexical representative, stable hash order; no match outcomes used',previous_native_training_families=sorted(used),cycles=schedule,development_check='Only after all4 cycles complete; no per-cycle dev candidate selection'),indent=2)+'\n')
status={'stage':'preparing','cycles':[]};
def save(): (root/'status.json').write_text(json.dumps(status,indent=2)+'\n')
def command(args,log):
 with open(log,'w') as f:p=subprocess.run(list(map(str,args)),cwd=r.parent.parent,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
 if p.returncode:raise RuntimeError(str(log)+' exit '+str(p.returncode))
checkpoint=here/'update01/query.pt';header=here/'update01/nn_weights.h';common=src/'common.h';s=common.read_text().replace('#define JD_NATIVE_LOG 0\n','#define JD_NATIVE_LOG 1\n');s=re.sub(r'^#define CLNA_SEED .*\n','',s,flags=re.M);common.write_text(s)
start=time.monotonic();save()
try:
 for spec in schedule:
  i=spec['cycle'];folder=root/('cycle'+str(i));folder.mkdir();(folder/'maps.json').write_text(json.dumps(spec['maps'],indent=2)+'\n')
  status['stage']='compile cycle'+str(i);save();shutil.copyfile(header,src/'nn_weights.h')
  f=src/'nnrec.cpp';text=f.read_text();text=re.sub(r'^#define CLNA_SEED .* // JD_CYCLE_SEED\n','',text,flags=re.M);text=text.replace('#include "bot.h"','#include "bot.h"\n#define CLNA_SEED '+str(spec['policy_seed'])+' // JD_CYCLE_SEED',1);f.write_text(text)
  command([cli,'__compile-bot',r/'native-query-actor'],folder/'compile.log')
  status['stage']='collect cycle'+str(i);save();raw=folder/'raw'
  command([py,here/'run_command_batch.py','--maps',folder/'maps.json','--run',raw,'--wasm',r/'native-query-actor/compiled.wasm','--header',src/'nn_weights.h','--seed',spec['policy_seed']],folder/'collect.log')
  status['stage']='audit cycle'+str(i);save();data=folder/'data'
  command([py,here/'adapt_commands.py','--rawroot',raw,'--out',data,'--header',raw/'policy_header.h'],folder/'audit.log')
  status['stage']='update cycle'+str(i);save();update=folder/'update'
  command([py,here/'train_query.py','--data',data,'--header',raw/'policy_header.h','--checkpoint',checkpoint,'--map-manifest',r.parent.parent/'outputs/rl-execution/EVALUATION_MAP_MANIFEST.json','--out',update],folder/'train.log')
  collection=json.loads((data/'collection_report.json').read_text());training=json.loads((update/'update_report.json').read_text())
  assert training['optimizer_resumed'];checkpoint=update/'query.pt';header=update/'nn_weights.h'
  summary=dict(cycle=i,games=collection['games'],rows=collection['rows'],departures=collection['departures'],training_wins=collection['wins'],training_losses=collection['losses'],families=[m['family'] for m in spec['maps']],seed=spec['policy_seed'],accepted_updates=training['accepted_updates'],total_updates=training['total_accepted_updates'],full_kl=training['final']['full_old_to_new_conditional_kl'],export_header_sha256=training['export']['export_sha256'],optimizer_resumed=True)
  status['cycles'].append(summary);status['stage']='cycle'+str(i)+' complete';save();print(json.dumps(summary),flush=True)
 status.update(stage='complete',wall_seconds=time.monotonic()-start,latest_checkpoint=str(checkpoint),latest_header=str(header));save();print(json.dumps({'stage':'complete','wall_seconds':status['wall_seconds']}),flush=True)
except Exception as e:
 status.update(stage='failed',error=str(e),wall_seconds=time.monotonic()-start);save();traceback.print_exc();raise
