"""Independent numerical oracle for adapter review; not a deployed actor."""
import json, math
from pathlib import Path
import torch
torch.set_default_dtype(torch.float64)
mapping=[7,3,8,7,12]
mask=torch.tensor([True,True,False,True,True])
reference=7
physical=[3,7,12]

def distribution(z,g):
 q=z.masked_fill(~mask,-torch.inf).softmax(0)
 a=g.sigmoid()
 # Explicit latent enumeration, including both paths to the reference.
 return torch.stack([(1-a)*float(y==reference)+a*sum(q[j] for j,m in enumerate(mapping) if m==y) for y in physical])

cases=[];max_auto=max_fd=0.0
for alpha in [.02,.1,.8]:
 z=torch.tensor([0.,4.,99.,-1.,1.],requires_grad=True)
 g=torch.tensor(math.log(alpha/(1-alpha)),requires_grad=True)
 p=distribution(z,g)
 q=z.detach().masked_fill(~mask,-torch.inf).softmax(0)
 assert abs(float(p.detach().sum())-1)<1e-12 and bool((p>0).all())
 for i,y in enumerate(physical):
  dz,dg=torch.autograd.grad(p[i].log(),(z,g),retain_graph=True)
  qy=sum(float(q[j]) for j,m in enumerate(mapping) if m==y)
  py=float(p[i].detach())
  analytic=torch.tensor([alpha*float(q[j])*(float(mapping[j]==y)-qy)/py if mask[j] else 0.0 for j in range(5)]+[alpha*(1-alpha)*(qy-float(y==reference))/py])
  automatic=torch.cat([dz,dg.reshape(1)]).detach()
  theta=torch.cat([z.detach(),g.detach().reshape(1)])
  fd=[]
  for j in range(6):
   hi,lo=theta.clone(),theta.clone();hi[j]+=1e-5;lo[j]-=1e-5
   fd.append(float((distribution(hi[:5],hi[5])[i].log()-distribution(lo[:5],lo[5])[i].log())/2e-5))
  max_auto=max(max_auto,float((analytic-automatic).abs().max()))
  max_fd=max(max_fd,float((analytic-torch.tensor(fd)).abs().max()))
  cases.append({'alpha':alpha,'proposal_logits':z.detach().tolist(),'mask':mask.tolist(),'proposal_to_physical':mapping,
   'reference':reference,'physical_order':physical,'probabilities':p.detach().tolist(),'chosen':y,
   'log_probability':float(p[i].detach().log()),'gradient_logits_then_gate_logit':analytic.tolist()})
 if alpha<.5:assert physical[int(p.detach().argmax())]==reference
 else:assert physical[int(p.detach().argmax())]==3
assert max_auto<1e-12 and max_fd<1e-8,(max_auto,max_fd)
out={'kind':'probability_and_gradient_oracle_NOT_training_results','precision':'float64',
 'coverage':'masked proposal, duplicate routes to reference, physical fallback aggregation, gate and head gradients, greedy departure when alpha grows',
 'max_analytic_vs_autograd_error':max_auto,'max_analytic_vs_finite_difference_error':max_fd,'cases':cases}
p=Path(__file__).resolve().parent.parent.parent/'outputs/rl-execution/MIXTURE_MATH_FIXTURES.json'
p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='cases'}))
