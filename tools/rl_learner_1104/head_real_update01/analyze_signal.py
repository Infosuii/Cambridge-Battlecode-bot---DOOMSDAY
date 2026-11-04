from pathlib import Path
import json,sys
from collections import defaultdict
import numpy as np,torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'target_head_reference'));from head import TargetHead
p=Path(__file__).parent;ck=torch.load(p/'head0.pt',weights_only=True);m=TargetHead();m.load_state_dict(ck['state']);torch.set_num_threads(2)
with np.load(p/'bundle/data.npz') as z:d={k:z[k] for k in z.files}
with torch.no_grad():
 policy,alpha,q=m(*[torch.from_numpy(d[k]) for k in ('context','camps','features','native_logits','valid','mapping','reference')],14)
 ref=torch.from_numpy(d['reference']);nonref=(1-policy.gather(1,ref[:,None]).squeeze(1)).numpy()
changes=[];roundgaps=[];block_changes=defaultdict(list)
for game in np.unique(d['game']):
 for body in np.unique(d['body_id'][d['game']==game]):
  ix=np.flatnonzero((d['game']==game)&(d['body_id']==body));ix=ix[np.argsort(d['decision_index'][ix])]
  if len(ix)<2:continue
  changed=d['context'][ix[1:]]!=d['context'][ix[:-1]]
  changes.extend(changed.sum(1).tolist())
  for name,a,b in [('global',0,16),('self',16,32),('allies',32,64),('enemies',64,96),('camps',96,128),('altars',128,160)]:block_changes[name].extend(changed[:,a:b].sum(1).tolist())
def quant(v):return dict(zip(['p10','p50','p90','p99'],map(float,np.quantile(v,[.1,.5,.9,.99]))))
r=dict(scope='Training-data diagnostic of real initial-head batch; no playing-strength claim',games=16,decisions=len(nonref),actual_nonreference_actions=int((d['action']!=d['reference']).sum()),expected_nonreference_actions=float(nonref.sum()),nonreference_probability=quant(nonref),unchanged_context_transition_fraction=float(np.mean(np.array(changes)==0)),changed_context_coordinates=quant(changes),context_width=160,block_changed_coordinates={k:quant(v) for k,v in block_changes.items()},notes=['Context differences are between ADMITTED logged head decisions, not every native snapshot; cannot infer exact per-refresh sparsity or speedup','Observation gaps and guard admission select these transitions; compare actual implementation counters before optimizing','Small initial alpha and concentrated native q mean many gradient samples carry nearly identical reference actions','Delta-update accumulation changes floating operation order; periodic rebuild and actual replay remain required'])
(p/'signal_report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
