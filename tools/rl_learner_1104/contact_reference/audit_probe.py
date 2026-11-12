from pathlib import Path
import json,hashlib,numpy as np,torch
from model import ContactHead
r=Path(__file__).resolve().parents[1];root=r/'runs/native-contact-shadow01';m=ContactHead();rows=[];summaries=[];torch.set_num_threads(2)
for directory in sorted(p for p in root.iterdir() if p.is_dir()):
 side=directory.name[-1].lower();stdout=directory/('team-'+side+'.stdout');stats=json.loads(directory.with_suffix('.json').read_text());assert stats['diagnostics']['detailedCaptureComplete'] and not any(stats['diagnostics']['botFaults'].values());done={};z=[]
 for line in stdout.read_bytes().replace(b'\0',b'').splitlines():
  t=line.decode().split()
  if not t:continue
  if t[0]=='JDC1':
   assert len(t)==17,(len(t),t[:5]);v=dict(zip(['logical','engine','body','seq','winning','danger','calls','hooks','opportunities','low_fuel','f0','f1','f2'],map(int,t[1:14])));v['mask']=t[14];v['x']=np.frombuffer(bytes.fromhex(t[15]),dtype='<i2').copy();v['z']=np.frombuffer(bytes.fromhex(t[16]),dtype='<i2').copy();assert v['x'].shape==(48,) and v['z'].shape==(8,) and (v['z'][3:]==0).all();assert v['mask'][0]=='1' and len(v['mask'])==3 and not set(v['mask'])-set('01');assert v['engine']==v['logical'] and v['f0']>=v['f1']>=v['f2'];assert v['x'][25]==2048*v['winning'] and v['x'][26]==2048*v['danger'];z.append(v)
  elif t[0]=='JDE1':
   assert len(t)==5;body,seq,rnd,fuel=map(int,t[1:]);assert (body,seq) not in done;done[body,seq]=(rnd,fuel)
  else:raise ValueError('unexpected stdout '+t[0])
 assert z and len(done)==len(z)
 for v in z:assert done[v['body'],v['seq']][0]==v['engine']
 for body in {v['body'] for v in z}:assert sorted(v['seq'] for v in z if v['body']==body)==list(range(1,1+sum(v['body']==body for v in z)))
 rows+=z;summaries.append(dict(case=directory.name,rows=len(z),bodies=len({v['body'] for v in z}),map_sha256=stats['match']['mapHash'],log_sha256=hashlib.sha256(stdout.read_bytes()).hexdigest(),all_markers_matched=True,min_completion_fuel=min(v[1] for v in done.values())))
x=torch.from_numpy(np.stack([v['x'] for v in rows]));logits,raw=m(x);assert torch.equal(raw.long(),torch.from_numpy(np.stack([v['z'][:3] for v in rows])).long())
# Diagnostic differentiability only. No fabricated game actions or rewards.
mask=torch.tensor([[c=='1' for c in v['mask']] for v in rows]);scores=logits.double();scores[:,0]+=2.;scores=scores.masked_fill(~mask,-torch.inf);objective=-scores.log_softmax(-1)[:,0].mean();objective.backward();assert all(torch.isfinite(p.grad).all() and p.grad.norm()>0 for p in m.parameters())
report=dict(scope='SHADOW final-contact-verdict head feasibility; no actions changed, no RL training/strength claim',rows=len(rows),trainable_parameters=sum(p.numel() for p in m.parameters()),features=48,commands=['keep heuristic verdict','force engage verdict','force retreat verdict'],native_q15_scores_bit_exact=True,gradient_norms={k:float(v.grad.norm()) for k,v in m.named_parameters()},feature_fuel=dict(median=float(np.median([v['f0']-v['f1'] for v in rows])),max=max(v['f0']-v['f1'] for v in rows)),feature_plus_head_fuel=dict(median=float(np.median([v['f0']-v['f2'] for v in rows])),max=max(v['f0']-v['f2'] for v in rows)),head_fuel=dict(median=float(np.median([v['f1']-v['f2'] for v in rows])),max=max(v['f1']-v['f2'] for v in rows)),cases=summaries,limitations=['Diagnostic nontrained coefficients; no controller execution, exploration likelihood, learned export or game improvement yet.','At most8 records per body; not a complete-contact producer and MUST NOT be used as an on-policy training episode.','Earlier burst/ambush/capture returns bypass this boundary; record coverage does not mean full combat control.','Probe/logging consumes charged fuel and may alter trajectories, even though it never assigns a different verdict.','Scores are from final heuristic state; would require state-only duplicate-effect masks and immediate completed-action-command contract before acting.'])
(r.parent.parent/'outputs/rl-execution/CONTACT_SHADOW_PROBE.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
