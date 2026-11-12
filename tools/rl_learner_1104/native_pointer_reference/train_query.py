"""Bounded on-policy QAT PPO for the existing native target query only."""
from pathlib import Path
import argparse,copy,hashlib,json,numpy as np,torch,time
from qat_pointer import NativePointer
from export_query import values,export
ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,required=True);ap.add_argument('--header',type=Path,required=True);ap.add_argument('--map-manifest',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
assert not a.out.exists();torch.set_num_threads(2)
meta=json.loads((a.data/'manifest.json').read_text());assert meta['schema']=='jd-native-query-command-v2' and meta['mode']=='stochastic categorical' and meta['data_origin']=='engine'
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
s=a.header.read_text();m=NativePointer(*[values(s,k,True) for k in ['kP_target_qW_TQ','kP_target_qbQ','kP_target_kWQ','kP_target_kbQ','kP_target_EQ']]);chunk=512

def distribution(sl):
 lg,_=m(d['h1'][sl],d['camps'][sl],d['present'][sl]);scores=lg.double();ix=torch.arange(len(scores));scores[ix,d['vslot'][sl]]+=meta['v92_bonus'];score=(scores/meta['temperature']).masked_fill(~d['valid'][sl],-torch.inf)
 lp=score.log_softmax(-1);return lp.exp(),lp
old=[];oldlp=[]
with torch.no_grad():
 for start in range(0,n,chunk):
  p,l=distribution(slice(start,start+chunk));old.append(p);oldlp.append(l)
old=torch.cat(old);oldlp=torch.cat(oldlp);ix=torch.arange(n)
replay=float((oldlp[ix,d['action']]-d['old_logp']).abs().max());assert replay<2e-4
opt=torch.optim.Adam([{'params':[m.query_w],'lr':3e-4},{'params':[m.query_bias],'lr':.003}])

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
 norm=float(torch.nn.utils.clip_grad_norm_(m.parameters(),.5,error_if_nonfinite=True));opt.step();diag=diagnostics()
 okay=not diag['support_lost'] and diag['full_old_to_new_conditional_kl']<=.005 and diag['max_sampled_logp_change']<=.5
 history.append(dict(epoch=epoch,loss=loss_sum,gradient_norm_before_clip=norm,accepted=okay,**diag))
 if not okay:m.load_state_dict(previous);opt.load_state_dict(previous_opt);break
 accepted+=1
 print(json.dumps(history[-1]),flush=True)
a.out.mkdir();ex=export(a.header,m,a.out/'nn_weights.h')
torch.save(dict(state=m.state_dict(),optimizer=opt.state_dict(),architecture='jd-native-target-query-qat-v1',updates=accepted,source_header_sha256=meta['native_header_sha256'],export_header_sha256=ex['export_sha256'],data_manifest_sha256=sha(a.data/'manifest.json')),a.out/'query.pt')
rep=dict(scope='REAL native target-query on-policy QAT PPO update, not a playing-strength result',games=ng,decisions=n,trainable_parameters=sum(p.numel() for p in m.parameters()),reward='gamma1 terminal team outcome',baseline='fixed zero',action_semantics=meta['action_semantics'],objective='sum command decisions per game, mean games; categorical entropy .003',settings=dict(epochs=2,weight_lr=.0003,bias_lr=.003,clip=.1,gradient_norm=.5,full_kl_limit=.005,max_sampled_logp_change=.5,chunk=chunk,threads=2),initial_replay_max_logp_error=replay,accepted_updates=accepted,epochs=history,final=diagnostics(),export=ex,wall_seconds=time.monotonic()-start,limitations=['Only existing1040 target-query parameters train; encoders/trunk/other heads/key/far frozen.','STE gradients approximate quantized actor optimization.','Collector logging changes fuel timing; deployment artifact requires separate runtime/strength evaluation.','One compiled policy RNG seed and8 map families; decisions are correlated.'])
(a.out/'update_report.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep,indent=2))
