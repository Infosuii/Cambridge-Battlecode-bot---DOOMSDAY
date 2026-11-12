"""Synthetic checks of the sparse joint PPO objective, no game-strength claim."""
import json
import torch
from ppo_objective import objective, exact_gate_kl

torch.set_num_threads(1)
g = torch.tensor(-.7, dtype=torch.double, requires_grad=True)
l = torch.tensor([.2,-.5,.8], dtype=torch.double, requires_grad=True)
a=g.sigmoid(); q=l.softmax(0)
p=torch.cat(((1-a).view(1),a*q))
z=torch.tensor([False,True,True,True])
reward=torch.tensor([.7,.7,-.2,1.],dtype=torch.double)
expected=torch.autograd.grad(-(p*reward).sum(),(g,l),retain_graph=True)
# Probability weights embedded in synthetic returns implement exact enumeration.
loss,d=objective(g.repeat(4),z,q.log(),p.detach().log(),reward*p.detach(),1,gate_entropy_coefficient=0.)
actual=torch.autograd.grad(loss,(g,l))
assert all(torch.allclose(x,y,atol=1e-13) for x,y in zip(expected,actual))
# All holds: no conditional rows or q parameters needed; gate still learns.
gh=torch.tensor([-.8,.1],requires_grad=True)
hloss,hd=objective(gh,torch.zeros(2,dtype=torch.bool),torch.empty(0),
                  torch.nn.functional.logsigmoid(-gh.detach()),torch.tensor([1.,-1.]),1)
hloss.backward(); assert torch.isfinite(gh.grad).all() and (gh.grad!=0).all()
# k3 is nonnegative, and its expectation equals exact latent KL with full support.
g0=torch.tensor(-1.,dtype=torch.double); g1=torch.tensor(.3,dtype=torch.double)
q0=torch.tensor([.1,.3,.6],dtype=torch.double); q1=torch.tensor([.4,.2,.4],dtype=torch.double)
p0=torch.cat(((1-g0.sigmoid()).view(1),g0.sigmoid()*q0))
p1=torch.cat(((1-g1.sigmoid()).view(1),g1.sigmoid()*q1))
lr=p1.log()-p0.log(); k3=torch.expm1(lr)-lr
exact=(p0*(p0.log()-p1.log())).sum()
assert (k3>=0).all() and torch.allclose((p0*k3).sum(),exact,atol=1e-13)
assert torch.allclose(exact,exact_gate_kl(g0,g1)+g0.sigmoid()*(q0*(q0.log()-q1.log())).sum(),atol=1e-13)
# PPO clipping: positive/negative returns and both sides of the clipping range.
for ret in (-1.,1.):
 for shift in (-.4,.4):
  gg=torch.tensor([.2],dtype=torch.double,requires_grad=True)
  old=torch.nn.functional.logsigmoid(-gg.detach())-shift
  v,_=objective(gg,torch.tensor([False]),torch.empty(0,dtype=torch.double),old,torch.tensor([ret],dtype=torch.double),1,gate_entropy_coefficient=0.)
  ratio=torch.tensor(shift).exp(); expected_loss=-torch.minimum(ratio*ret,ratio.clamp(.9,1.1)*ret)
  assert torch.allclose(v,expected_loss.double(),atol=1e-7)
print(json.dumps(dict(scope='synthetic objective verification only, no integrated actor or strength claim',
 expected_task_gradient='pass',all_hold_sparse_gradient='pass',joint_kl_identity='pass',
 k3_expectation='pass',clipping_signs='pass',entropy='gate only; no full policy entropy claimed'),indent=2))
