"""Real frozen-input math replay; NOT a live conditional-policy game or training run."""
import hashlib,json,sys
from pathlib import Path
import numpy as np,torch
from conditional_model import ConditionalActor
from head import TargetHead
root=Path(__file__).resolve().parents[1];b=root/'head-real-batch'
torch.set_num_threads(2)
ck=torch.load(b/'head0.pt',weights_only=True,map_location='cpu')
with np.load(b/'bundle/data.npz') as z:d={k:torch.from_numpy(z[k]) for k in z.files}
m=ConditionalActor(ck['state']);native=TargetHead();native.load_state_dict(ck['state'])
P=14
with torch.no_grad():
 policy,alpha,slot=native(*[d[k] for k in ('context','camps','features','native_logits','valid','mapping','reference')],P)
 expected=torch.zeros(len(slot),P).scatter_add_(1,d['mapping'].long().clamp(0,P-1),slot)
 new=m.conditional_distribution(*[d[k] for k in ('context','camps','features','native_logits','valid','mapping')],P)
 err=(expected-new).abs().max().item();assert err<1e-7
# All holds have no conditional inputs and must not execute large-head inference.
def forbidden(*a,**k):raise AssertionError('head executed on hold')
saved=m.conditional_distribution;m.conditional_distribution=forbidden
hold=torch.zeros(32,dtype=torch.bool);gate=torch.zeros(32,6)
lp=m.chosen_joint_logp(gate,hold,{'action':torch.empty(0,dtype=torch.long)},P)
assert torch.allclose(lp,torch.full((32,),np.log(.98)),atol=1e-7)
(-lp.sum()).backward();assert m.cheap_gate.bias.grad is not None
assert all(p.grad is None for p in m.head.parameters())
m.conditional_distribution=saved;m.zero_grad(set_to_none=True)
# Explicit latent fixtures using real observation rows (not labels for old data).
inv=torch.tensor([False,True,False,True]);ix=torch.tensor([0,1])
q={k:d[k][ix] for k in ('context','camps','features','native_logits','valid','mapping','action')}
lp=m.chosen_joint_logp(torch.zeros(4,6),inv,q,P)
assert torch.isfinite(lp).all();(-lp.sum()).backward()
assert m.head.query.weight.grad is not None and m.head.gate.weight.grad is None
print(json.dumps(dict(scope='frozen real-input conditional distribution parity plus synthetic latent fixtures; NOT new collection/training',
 input_rows=len(slot),old_initial_head_weights_sha256=ck['weights_sha256'],
 conditional_physical_probability_max_error=err,all_hold_skips_head='pass',hold_only_gate_gradients='pass',
 invoked_query_gradients='pass',unused_old_gate_frozen='pass',
 trainable_parameters=sum(p.numel() for p in m.parameters() if p.requires_grad),
 total_stored_parameters=sum(p.numel() for p in m.parameters()),
 note='No old marginal observations relabeled as actual latent decisions; actual C++ gate feature/header replay pending'),indent=2))
