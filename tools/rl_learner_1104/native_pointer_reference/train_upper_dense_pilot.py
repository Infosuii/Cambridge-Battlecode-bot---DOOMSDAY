"""Bounded on-policy QAT PPO for existing native upper trunk and target query."""
from pathlib import Path
import argparse,copy,hashlib,json,numpy as np,torch,time
from qat_upper import NativeUpper
from export_query import values
from export_upper import export
ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,required=True);ap.add_argument('--header',type=Path,required=True);ap.add_argument('--map-manifest',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--checkpoint',type=Path);ap.add_argument('--value-baseline',type=Path,required=True);ap.add_argument('--dense-components',type=Path,required=True);a=ap.parse_args()
assert not a.out.exists();torch.set_num_threads(2)
meta=json.loads((a.data/'manifest.json').read_text());assert meta['schema']=='jd-native-upper-command-v3' and meta['mode']=='stochastic categorical' and meta['data_origin']=='engine'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(a.header)==meta['native_header_sha256'] and sha(a.data/'data.npz')==meta['data_sha256']
train={m['sha256'] for m in json.loads(a.map_manifest.read_text())['maps'] if m['split']=='training'}
eps=meta['episodes'];assert eps and len({e['key'] for e in eps})==len(eps)
assert all(e['map_sha256'] in train and e['status']=='terminated' and e['complete_command_producer'] and e['outcome'] in (-1,0,1) for e in eps)
with np.load(a.data/'data.npz',allow_pickle=False) as z:d={k:torch.from_numpy(z[k]) for k in z.files}
n=len(d['action']);ng=len(eps);assert n>0
assert set(d['game'].tolist())=={i for i,e in enumerate(eps) if e['rows']>0}
returns=torch.empty(n,dtype=torch.double)
for i,e in enumerate(eps):
 mask=d['game']==i;assert int(mask.sum())==e['rows'];returns[mask]=e['outcome']
 for body in d['body'][mask].unique():
  ix=d['index'][mask&(d['body']==body)].sort().values
  assert torch.equal(ix,torch.arange(1,len(ix)+1))
assert meta['value_feature_contract']=='Strictly prior-round gemSubmission history; no same/future-round events'
vb=json.loads(a.value_baseline.read_text());assert vb['architecture']=='jd-past-score-logistic-value-v1' and vb['clamp']==8.
vf=d['value_features'].float();assert vf.shape==(n,8) and torch.isfinite(vf).all()
vm=torch.tensor(vb['mean'],dtype=torch.float32);vs=torch.tensor(vb['std'],dtype=torch.float32);vw=torch.tensor(vb['weight'],dtype=torch.float32);vbi=torch.tensor(vb['bias'],dtype=torch.float32)
assert vm.shape==vs.shape==(8,) and vw.shape==(1,8) and vbi.shape==(1,) and (vs>0).all()
with torch.no_grad():baseline_predictions=2*torch.nn.functional.linear(((vf-vm)/vs).clamp(-8,8),vw,vbi).squeeze(1).sigmoid()-1
returns-=baseline_predictions.double()
# Preset pilot: signed TEAM collection over strictly later150 rounds, /200.
# No dense-value prediction is borrowed from the terminal-outcome baseline.
with np.load(a.dense_components,allow_pickle=False) as cz:
 for key in ('game','body','engine_round','action','old_logp'):
  assert np.array_equal(cz[key],d[key].numpy()),'component-command alignment '+key
 dense_term=torch.from_numpy((cz['future_own'].astype(np.float64)-cz['future_enemy'].astype(np.float64))/200.)
assert dense_term.shape==returns.shape and torch.isfinite(dense_term).all()
returns+=dense_term

s=a.header.read_text();m=NativeUpper(*[values(s,k,True) for k in ['kT_W1_TQ','kT_b1Q','kP_target_qW_TQ','kP_target_qbQ','kP_target_kWQ','kP_target_kbQ','kP_target_EQ']]);chunk=512
prior_updates=0;prior_optimizer=None
if a.checkpoint:
 ck=torch.load(a.checkpoint,weights_only=True,map_location='cpu')
 assert ck['architecture']=='jd-native-upper-query-qat-v1' and ck['export_header_sha256']==meta['native_header_sha256']
 m.load_state_dict(ck['state'],strict=True);prior_updates=ck['updates'];prior_optimizer=ck['optimizer']
 assert np.array_equal(torch.round(m.query_w.detach()*16384).clamp(-32768,32767).numpy().astype(np.int64).flatten(),values(s,'kP_target_qW_TQ',True))
 assert np.array_equal(torch.round(m.query_bias.detach()*128).clamp(-32768,32767).numpy().astype(np.int64),values(s,'kP_target_qbQ',True))

if a.checkpoint:
 for name,scale,param in [('kT_W1_TQ',16384,m.trunk_w),('kT_b1Q',256,m.trunk_bias)]:
  assert np.array_equal(torch.round(param.detach()*scale).clamp(-32768,32767).numpy().astype(np.int64).flatten(),values(s,name,True))

def distribution(sl):
 lg,_=m(d['h0'][sl],d['camps'][sl],d['present'][sl]);scores=lg.double();ix=torch.arange(len(scores));scores[ix,d['vslot'][sl]]+=meta['v92_bonus'];score=(scores/meta['temperature']).masked_fill(~d['valid'][sl],-torch.inf)
 lp=score.log_softmax(-1);return lp.exp(),lp
old=[];oldlp=[]
with torch.no_grad():
 for start in range(0,n,chunk):
  p,l=distribution(slice(start,start+chunk));old.append(p);oldlp.append(l)
old=torch.cat(old);oldlp=torch.cat(oldlp);ix=torch.arange(n)
replay=float((oldlp[ix,d['action']]-d['old_logp']).abs().max());assert replay<2e-4
opt=torch.optim.Adam([{'params':[m.query_w,m.trunk_w],'lr':3e-4},{'params':[m.query_bias,m.trunk_bias],'lr':.003}])
if prior_optimizer is not None:opt.load_state_dict(prior_optimizer)

def diagnostics():
 kl=0.;maxdelta=0.;support_lost=False
 with torch.no_grad():
  for start in range(0,n,chunk):
   sl=slice(start,start+chunk);p,l=distribution(sl);v=d['valid'][sl]
   support_lost |= bool(((old[sl]>0)&(p==0)).any())
   kl+=float((old[sl]*(oldlp[sl].masked_fill(~v,0)-l.masked_fill(~v,0))).sum())
   maxdelta=max(maxdelta,float((l[torch.arange(len(l)),d['action'][sl]]-d['old_logp'][sl]).abs().max()))
 return dict(full_old_to_new_conditional_kl=kl/n,max_sampled_logp_change=maxdelta,support_lost=support_lost)
start=time.monotonic();history=[];accepted=0
for epoch in range(2):
 previous=copy.deepcopy(m.state_dict());previous_opt=copy.deepcopy(opt.state_dict());opt.zero_grad();loss_sum=0.
 for st in range(0,n,chunk):
  sl=slice(st,st+chunk);p,l=distribution(sl);act=d['action'][sl];lp=l[torch.arange(len(l)),act];ratio=(lp-d['old_logp'][sl]).exp();adv=returns[sl]
  surrogate=torch.minimum(ratio*adv,ratio.clamp(.9,1.1)*adv)
  entropy=-(p*l.masked_fill(~d['valid'][sl],0)).sum(-1)
  loss=-(surrogate+.003*entropy).sum()/ng;loss.backward();loss_sum+=float(loss.detach())
 norm=float(torch.nn.utils.clip_grad_norm_(m.parameters(),.5,error_if_nonfinite=True));attempts=[]
 initial_lrs=[g['lr'] for g in opt.param_groups]
 for trial in range(6):
  if trial:
   m.load_state_dict(previous);opt.load_state_dict(previous_opt)
   for group,lr in zip(opt.param_groups,initial_lrs):group['lr']=lr*(.5**trial)
  opt.step();diag=diagnostics()
  okay=not diag['support_lost'] and diag['full_old_to_new_conditional_kl']<=.005 and diag['max_sampled_logp_change']<=.5
  attempts.append(dict(trial=trial,lrs=[g['lr'] for g in opt.param_groups],accepted=okay,**diag))
  if okay:break
 history.append(dict(epoch=epoch,loss=loss_sum,gradient_norm_before_clip=norm,accepted=okay,attempts=attempts,**diag))
 if not okay:
  m.load_state_dict(previous);opt.load_state_dict(previous_opt)
  for group,lr in zip(opt.param_groups,initial_lrs):group['lr']=lr/64
  break
 accepted+=1
 print(json.dumps(history[-1]),flush=True)
a.out.mkdir();ex=export(a.header,m,a.out/'nn_weights.h')
torch.save(dict(state=m.state_dict(),optimizer=opt.state_dict(),architecture='jd-native-upper-query-qat-v1',updates=prior_updates+accepted,source_header_sha256=meta['native_header_sha256'],export_header_sha256=ex['export_sha256'],data_manifest_sha256=sha(a.data/'manifest.json')),a.out/'upper.pt')
rep=dict(scope='REAL native upper-trunk/query on-policy QAT PPO update, not a playing-strength result',games=ng,decisions=n,trainable_parameters=sum(p.numel() for p in m.parameters()),reward='terminal team outcome plus future150-round own-minus-enemy camp collection /200; same-round excluded; no dense baseline',baseline='Frozen prior-query logistic predictor for TERMINAL component only; zero baseline for dense component; no same-batch fitting',dense_component_sha256=sha(a.dense_components),dense_term_mean=float(dense_term.mean()),dense_term_std=float(dense_term.std()),baseline_sha256=sha(a.value_baseline),baseline_prediction_mean=float(baseline_predictions.mean()),action_semantics=meta['action_semantics'],objective='sum command decisions per game, mean games; categorical entropy .003',settings=dict(epochs=2,weight_lr=.0003,bias_lr=.003,effective_lrs=[g['lr'] for g in opt.param_groups],backtracking='up to6 training-KL/likelihood-only step halvings, restored model+Adam before retry',clip=.1,gradient_norm=.5,full_kl_limit=.005,max_sampled_logp_change=.5,chunk=chunk,threads=2),initial_replay_max_logp_error=replay,accepted_updates=accepted,total_accepted_updates=prior_updates+accepted,optimizer_resumed=prior_optimizer is not None,epochs=history,final=diagnostics(),export=ex,wall_seconds=time.monotonic()-start,limitations=['Existing5200 upper-trunk/query parameters train; lower trunk/encoders/other heads/key/far frozen.','STE gradients approximate quantized actor optimization.','Collector logging changes fuel timing; deployment artifact requires separate runtime/strength evaluation.','One compiled policy RNG seed and8 map families; decisions are correlated.','Finite-horizon team-collection bonus changes the training objective and is not policy-invariant reward shaping.','This is a single update pilot, not evidence that a full160-game dense-reward block succeeds or fails.'])
(a.out/'update_report.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep,indent=2))
