import json,torch
from joint_gate import collect,joint_logp

torch.set_num_threads(1)
# Enumerate latent probabilities. Two distinct routes execute reference0.
g=torch.tensor(-1.1,dtype=torch.double,requires_grad=True)
l=torch.tensor([.3,-.4,1.2],dtype=torch.double,requires_grad=True)
q=l.softmax(0);a=g.sigmoid();latent=torch.cat(((1-a).view(1),a*q))
reward=torch.tensor([.7,.7,-.2,1.],dtype=torch.double)
J=(latent*reward).sum();grad=torch.autograd.grad(J,(g,l),retain_graph=True)
physical=a*q;physical=physical.clone();physical[0]+=1-a
Jp=(physical*reward[1:]).sum();gp=torch.autograd.grad(Jp,(g,l),retain_graph=True)
assert all(torch.allclose(x,y,atol=1e-13) for x,y in zip(grad,gp))
scoreloss=-(latent.detach()*reward*latent.log()).sum();gs=torch.autograd.grad(scoreloss,(g,l))
assert all(torch.allclose(x,-y,atol=1e-13) for x,y in zip(gs,grad))
# Hold and invoke-reference must have distinct logged probabilities.
z=torch.tensor([False,True]);gl=g.detach().repeat(2);ac=torch.tensor([0,0]);lp=joint_logp(gl,z,ac,q[0].log().detach().view(1))
assert torch.allclose(lp.exp().sum(),physical[0])
# Deterministic resource mask must not call q or create stochastic samples.
calls=[]
def callback(ix):
 calls.append(len(ix));return torch.ones(len(ix),3)/3
r=collect(torch.zeros(16),torch.zeros(16,dtype=torch.long),callback,allowed=torch.zeros(16,dtype=torch.bool))
assert calls==[] and not r['has_logp'].any() and torch.isnan(r['logp']).all()
# Near-zero alpha: admitted holds still have a valid gate likelihood, no q calls.
r=collect(torch.full((16,),-100.),torch.zeros(16,dtype=torch.long),callback,generator=torch.Generator().manual_seed(7))
assert calls==[] and r['has_logp'].all() and torch.isfinite(r['logp']).all()
# Nontrivial batch: expensive callback sees exactly the invoked subset.
r=collect(torch.zeros(1000),torch.zeros(1000,dtype=torch.long),callback,generator=torch.Generator().manual_seed(7))
assert calls==[int(r['invoke'].sum())] and torch.isfinite(r['logp']).all()
rep=dict(scope='Enumerated synthetic policy math only; NOT game training/instruction benchmark',gradient_marginal_equivalence='passed',score_function_gradient='passed',reference_alias_routes='passed',no_q_on_hold='passed',resource_mask_has_no_logp='passed',sampled_invokes=int(r['invoke'].sum()),batch=1000,notes=['Latent PPO clipping is a different surrogate from marginal physical-action PPO','Cheap gate must consume cheap legal features and avoid always-running added projection stages','No measured gameplay or total-fuel saving claimed'])
print(json.dumps(rep,indent=2))
