import json
import torch
from head import TargetHead

torch.manual_seed(7)
torch.set_num_threads(1)
m=TargetHead().double()
B,K,P=3,4,5
x=torch.randn(B,160,dtype=torch.double)
c=torch.randn(B,K,16,dtype=torch.double)
f=torch.randn(B,K,4,dtype=torch.double)
l=torch.randn(B,K+1,dtype=torch.double)
v=torch.tensor([[1,1,1,0,1],[1,1,1,1,1],[1,0,1,1,1]],dtype=torch.bool)
# Far aliases an existing camp in two rows; another duplicate camp also exists.
ids=torch.tensor([[0,1,1,4,0],[0,1,2,3,4],[2,1,3,4,2]])
ref=torch.tensor([0,4,2])
def run(cc=c,ff=f,ll=l,vv=v,ii=ids):
    return m(x,cc,ff,ll,vv,ii,ref,P)
p,a,s=run()
expected=torch.zeros_like(p)
for b in range(B):
    for j in range(K+1): expected[b,ids[b,j]] += .02*s[b,j]
    expected[b,ref[b]] += .98
assert sum(t.numel() for t in m.parameters())==11826
assert torch.allclose(p,expected,atol=1e-14)
assert torch.allclose(p.sum(-1),torch.ones(B,dtype=torch.double))
assert (s[~v]==0).all()
perm=torch.tensor([2,0,3,1]); pp=torch.cat([perm,torch.tensor([K])])
p2,_,_=run(c[:,perm],f[:,perm],l[:,pp],v[:,pp],ids[:,pp])
assert torch.allclose(p,p2,atol=1e-14)
# Full mixture finite-difference gradient, including teacher alias mass.
loss=-p[0,0].log();loss.backward()
autograd=m.gate.bias.grad.item();old=m.gate.bias.item();eps=1e-6
with torch.no_grad():
    m.gate.bias.fill_(old+eps);plus=-run()[0][0,0].log().item()
    m.gate.bias.fill_(old-eps);minus=-run()[0][0,0].log().item()
    m.gate.bias.fill_(old)
finite=(plus-minus)/(2*eps)
assert abs(autograd-finite)<1e-8
# Verify zero residual query can learn, then sends gradients into key/features.
opt=torch.optim.SGD(m.parameters(),lr=.1)
for step in range(2):
    opt.zero_grad();p,_,_=run();(-p[1,1].log()).backward()
    if step==0: assert m.query.weight.grad.abs().sum()>0
    if step==1:
        assert m.key.weight.grad.abs().sum()>0
        assert m.features.weight.grad.abs().sum()>0
    opt.step()
# Gate is free to override reference, unlike permanently low-epsilon mixture.
with torch.no_grad():
    m.gate.weight.zero_();m.gate.bias.fill_(10)
    m.far.weight.zero_();m.far.bias.fill_(-30)
forced=l.clone();forced[1].fill_(-30);forced[1,1]=30
p,_,_=run(ll=forced);assert p[1].argmax().item()==1 and ref[1].item()!=1
# Missing reference and all-masked rows rejected.
for vv,ii,rr in [(torch.zeros_like(v),ids,ref),(v,ids,torch.tensor([4,4,2]))]:
    try: m(x,c,f,l,vv,ii,rr,P)
    except ValueError: pass
    else: raise AssertionError('invalid support accepted')
print(json.dumps({'parameters':11826,'native_plus_head':40715,'mixture_mass_and_aliases':'passed','permutation_equivariance':'passed','mask_and_support_checks':'passed','gate_gradient_absolute_error':abs(autograd-finite),'query_then_key_gradient':'passed','scope':'Synthetic learner math only; no integrated runtime, rollout training or strength claim'},indent=2))
