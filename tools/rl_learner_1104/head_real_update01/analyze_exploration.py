"""Offline exploration calibration on training observations, not policy evaluation."""
from pathlib import Path
import hashlib,json,numpy as np,torch
p=Path(__file__).parent
meta=json.loads((p/'bundle/manifest.json').read_text())
assert hashlib.sha256((p/'bundle/data.npz').read_bytes()).hexdigest()==meta['data_sha256']
with np.load(p/'bundle/data.npz') as f:d={k:f[k] for k in f.files}
maps=json.loads((p/'map_manifest.json').read_text())
train={x['sha256'] for x in maps['maps'] if x['split']=='training'}
assert all(e['map_sha256'] in train for e in meta['episodes'])
torch.set_num_threads(2)
logits=torch.from_numpy(d['native_logits']);valid=torch.from_numpy(d['valid']).bool()
mapping=torch.from_numpy(d['mapping']).long();ref=torch.from_numpy(d['reference']).long()
P=meta['physical_count'];N=len(ref);games=len(meta['episodes'])
support=torch.zeros(N,P,dtype=torch.float32).scatter_add_(1,mapping.clamp(0,P-1),valid.float())>0
uniform=support.float()/support.sum(-1,keepdim=True)
# This captures physical support; slot-uniform would over-weight aliased targets.
base_slot=logits.masked_fill(~valid,-torch.inf).softmax(-1)
base_physical=torch.zeros(N,P).scatter_add_(1,mapping.clamp(0,P-1),base_slot)
rows=[]
for T in (1.,2.,4.):
 slot=(logits/T).masked_fill(~valid,-torch.inf).softmax(-1)
 physical=torch.zeros(N,P).scatter_add_(1,mapping.clamp(0,P-1),slot)
 for eps in (0.,.05,.1):
  q=(1-eps)*physical+eps*uniform
  nonref=1-q.gather(1,ref[:,None]).squeeze(1)
  entropy=-(q*q.clamp_min(torch.finfo(q.dtype).tiny).log()).sum(-1)
  # KL direction is from unmodified native conditional distribution to q.
  kl=(base_physical*(base_physical.clamp_min(1e-30).log()-q.clamp_min(1e-30).log())).sum(-1)
  for alpha in (.02,.05,.1):
   counts=[float((alpha*nonref)[torch.from_numpy(d['game'])==i].sum()) for i in range(games)]
   rows.append(dict(temperature=T,physical_uniform_fraction=eps,gate_probability=alpha,
    expected_invocations=N*alpha,expected_nonreference_actions=float((alpha*nonref).sum()),
    expected_nonreference_per_invocation=float(nonref.mean()),
    expected_nonreference_game_p10_p50_p90=list(map(float,np.quantile(counts,[.1,.5,.9]))),
    mean_conditional_physical_entropy=float(entropy.mean()),
    mean_native_to_conditional_kl=float(kl.mean())))
rep=dict(scope='Offline hypothetical distribution calibration on OLD TRAINING observations only; no new games, training, live invocation counts, fuel or strength evidence',
 data_sha256=meta['data_sha256'],policy_weights_sha256=meta['policy_weights_sha256'],
 games=games,rows=N,actual_logged_nonreference_actions=int((d['action']!=d['reference']).sum()),
 physical_support_size_p10_p50_p90=list(map(float,np.quantile(support.sum(-1).numpy(),[.1,.5,.9]))),
 grid=rows,notes=['Observations selected by old fuel guard; new cheap-gate actor sees a different population.',
 'Expected invocations are hypothetical Bernoulli draws at every row, not recovered latent labels from old marginal logs.',
 'At zero residual the native logits define conditional q; temperature or uniform mixing changes behavior and requires fresh on-policy collection.',
 'Temperature and physical uniform mixing are experiment candidates, not selected winners; do not optimize these using development outcomes.',
 'Higher invocation rate increases examples AND optional inference cost; require actual runtime control before any training sweep.',
 'Count independent completed games, both sides and map families; thousands of correlated decisions are not thousands of independent reward observations.'])
(p/'exploration_report.json').write_text(json.dumps(rep,indent=2)+'\n')
print(json.dumps({k:v for k,v in rep.items() if k!='grid'},indent=2))
print(json.dumps([r for r in rows if (r['temperature'],r['physical_uniform_fraction'],r['gate_probability']) in [(1.,0.,.02),(2.,0.,.02),(1.,.1,.02),(2.,.05,.05),(4.,0.,.1)]],indent=2))
