from pathlib import Path
import json,sys,numpy as np,torch
from conditional_rows import read
from conditional_model import ConditionalActor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'r1_head_tools'))
import head_export as HX
p=Path(sys.argv[1]);raw=Path(sys.argv[2]).read_bytes();out=Path(sys.argv[3]);torch.set_num_threads(2)
head,version=HX.load_header(str(p/'clna_head_w.h'))
m=ConditionalActor(head.state_dict(),initial_alpha=.2)
with torch.no_grad():
 m.cheap_gate.weight.copy_(torch.tensor([[.4,-.2,.15,.1,-.3,.25]]))
rows,assoc=read(raw)
assert rows
inv=torch.tensor([bool(r['invoke']) for r in rows]);inds=[i for i,r in enumerate(rows) if r['invoke']]
g=torch.from_numpy(np.stack([r['gate_inputs'] for r in rows]))
cond={k:torch.from_numpy(np.stack([rows[i][k] for i in inds])) for k in ('context','camps','features','native_logits','valid','mapping')} if inds else {}
cond['action']=torch.tensor([rows[i]['action'] for i in inds])
with torch.no_grad():
 lp=m.chosen_joint_logp(g,inv,cond,14);a=m.gate_logits(g).sigmoid()
 if inds:
  q=m.conditional_distribution(*[cond[k] for k in ('context','camps','features','native_logits','valid','mapping')],14)
  qc=q.gather(1,cond['action'][:,None]).squeeze(1)
old=torch.tensor([r['joint_logp'] for r in rows],dtype=torch.double)
err=(lp.double()-old).abs().max().item();ae=(a.double()-torch.tensor([r['alpha'] for r in rows],dtype=torch.double)).abs().max().item()
qe=(qc.double()-torch.tensor([rows[i]['q_chosen'] for i in inds],dtype=torch.double)).abs().max().item() if inds else None
assert err<2e-4 and ae<2e-6
# Fault injection on actual live rows: reject truncated payload/duplicate identities.
from conditional_rows import parse
first=next(b.decode() for b in raw.replace(b'\0',b'\n').splitlines() if b.startswith(b'CNG1 '))
for bad in [' '.join(first.split()[:-1]),first+' extra']:
 try:parse(bad)
 except ValueError:pass
 else:raise AssertionError('corrupted row accepted')
try:read((first+'\n'+first+'\n').encode())
except ValueError:pass
else:raise AssertionError('duplicate accepted')
report=dict(scope='Actual conditional runtime arithmetic/encoding audit with NONTRAINED diagnostic head+gate; no strength or full collection eligibility claim',
 head_version=version,rows=len(rows),invokes=len(inds),holds=len(rows)-len(inds),
 physical_departures=sum(r['chosen']!=r['ref'] for r in rows),
 max_joint_logp_error=err,max_gate_probability_error=ae,max_conditional_chosen_probability_error=qe,
 alpha_range=[min(r['alpha'] for r in rows),max(r['alpha'] for r in rows)],
 invoked_pub_age_p10_p50_p90=list(map(float,np.quantile([rows[i]['round']-rows[i]['pub'] for i in inds],[.1,.5,.9]))) if inds else None,
 association=assoc,truncated_duplicate_payload_rejection='pass')
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
