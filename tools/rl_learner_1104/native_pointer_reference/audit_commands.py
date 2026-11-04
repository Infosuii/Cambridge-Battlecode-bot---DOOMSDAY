from pathlib import Path
import argparse,json,numpy as np,torch
from command_rows import read
from qat_pointer import NativePointer
from export_query import values
p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--header',required=True);p.add_argument('--out',required=True);p.add_argument('--deterministic',action='store_true');a=p.parse_args()
r=Path(__file__).resolve().parents[1];src=Path(a.header).read_text();rows,assoc=read((r/'runs'/a.run/'team-a.stdout').read_bytes());assert rows
m=NativePointer(*[values(src,n,True) for n in ['kP_target_qW_TQ','kP_target_qbQ','kP_target_kWQ','kP_target_kbQ','kP_target_EQ']]);torch.set_num_threads(2)
with torch.no_grad():
 logits,_=m(torch.from_numpy(np.stack([x['h1'] for x in rows])),torch.from_numpy(np.stack([x['camps'] for x in rows])),torch.from_numpy(np.stack([x['present'] for x in rows])))
 scores=logits.double();mask=torch.from_numpy(np.stack([x['valid'] for x in rows]));ix=torch.arange(len(rows));vs=torch.tensor([x['vslot'] for x in rows]);action=torch.tensor([x['action'] for x in rows]);scores[ix,vs]+=torch.tensor([x['bonus'] for x in rows],dtype=torch.double)
 # Tie goes to v92. For stochastic rows it is ordinary canonical softmax.
 score_masked=scores.masked_fill(~mask,-torch.inf);mx=score_masked.max(-1).values;arg=score_masked.argmax(-1);arg=torch.where(score_masked[ix,vs]==mx,vs,arg)
 lp=(score_masked/torch.tensor([x['temperature'] for x in rows])[:,None]).log_softmax(-1)[ix,action]
 nat=np.stack([x['native_logits'] for x in rows]);present=np.concatenate((np.stack([x['present'] for x in rows]),np.ones((len(rows),1),bool)),-1)
 max_logit=float(np.max(np.abs((logits.numpy()-nat)[present])))
 max_lp=float(np.max(np.abs(lp.numpy()-np.array([x['old_logp'] for x in rows])))) if not a.deterministic else None
 if not a.deterministic:assert max_lp<2e-4
 assert max_logit==0 and assoc['producer_markers_complete']
 ref_matches=sum(x['groups'][int(arg[i])]==x['reference'] for i,x in enumerate(rows))
 det_matches=sum(int(arg[i])==x['action'] for i,x in enumerate(rows))
 if a.deterministic:assert det_matches==len(rows)
 rep=dict(scope='Actual native target-command actor replay; no trained improvement claim',run=a.run,mode='deterministic control' if a.deterministic else 'stochastic collection audit',rows=len(rows),native_logits_bit_exact=max_logit==0,
  max_chosen_logp_error=max_lp,argmax_reference_matches=ref_matches,argmax_reference_mismatches=len(rows)-ref_matches,
  departures=sum(x['chosen']!=x['reference'] for x in rows),association=assoc)
 Path(a.out).write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep,indent=2))
