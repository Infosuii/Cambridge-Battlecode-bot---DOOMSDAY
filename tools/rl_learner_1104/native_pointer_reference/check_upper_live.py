"""Replay actual consumed h0 through upper trunk and pointer; audit producer."""
from pathlib import Path
import argparse,hashlib,json,numpy as np,torch
from qat_upper import NativeUpper
from upper_rows import read
from export_query import values
ap=argparse.ArgumentParser();ap.add_argument('--stdout',type=Path,required=True);ap.add_argument('--header',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
s=a.header.read_text();names=['kT_W1_TQ','kT_b1Q','kP_target_qW_TQ','kP_target_qbQ','kP_target_kWQ','kP_target_kbQ','kP_target_EQ'];m=NativeUpper(*[values(s,n,True) for n in names]);torch.set_num_threads(2)
rows,assoc=read(a.stdout.read_bytes());assert rows and assoc['producer_markers_complete'] and not assoc['logging_round_overruns']
stack=lambda k,z:torch.from_numpy(np.stack([v[k] for v in z]))
max_lp=0.
with torch.no_grad():
 for start in range(0,len(rows),512):
  z=rows[start:start+512];logits,aux=m(stack('h0',z),stack('camps',z),stack('present',z))
  assert torch.equal(aux['h1_raw'].long(),stack('h1',z).long())
  assert torch.equal(logits,stack('native_logits',z))
  score=logits.double();ix=torch.arange(len(z));score[ix,torch.tensor([v['vslot'] for v in z])]+=torch.tensor([v['bonus'] for v in z],dtype=torch.double)
  lp=(score/torch.tensor([v['temperature'] for v in z],dtype=torch.double)[:,None]).masked_fill(~stack('valid',z),-torch.inf).log_softmax(-1)[ix,torch.tensor([v['action'] for v in z])]
  max_lp=max(max_lp,float((lp-torch.tensor([v['old_logp'] for v in z],dtype=torch.double)).abs().max()))
assert max_lp<2e-4
z=rows[:32];logits,_=m(stack('h0',z),stack('camps',z),stack('present',z));(-logits.log_softmax(-1)[:,-1].mean()).backward()
grad={k:float(v.grad.norm()) for k,v in m.named_parameters()};assert all(np.isfinite(v) and v>0 for v in grad.values())
rep=dict(scope='Actual JNP3 consumed-h0 native replay and diagnostic gradient; no RL update or strength claim',rows=len(rows),trainable_parameters=sum(v.numel() for v in m.parameters()),h1_and_logits_bit_exact=True,max_chosen_logp_error=max_lp,gradient_norms=grad,association=assoc,header_sha256=hashlib.sha256(a.header.read_bytes()).hexdigest(),stdout_sha256=hashlib.sha256(a.stdout.read_bytes()).hexdigest())
a.out.write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep,indent=2))
