"""Small regularized value predictor with genuine past-only score context."""
from pathlib import Path
import hashlib,json,numpy as np,torch
from torch import nn
from past_score_features import features
r=Path(__file__).resolve().parents[1];here=Path(__file__).parent;out=here/'value_score01';assert not out.exists();torch.set_num_threads(2);torch.manual_seed(110412)
folders=[(here/'real_batch_u0',r/'runs/native-query-u0-flush-mac32')]+[(r/'runs/native-query-continuation-01'/('cycle'+str(i))/'data',r/'runs/native-query-continuation-01'/('cycle'+str(i))/'raw') for i in range(1,5)]
X=[];Y=[];F=[];G=[];sources=[];gid=0
for data,rawroot in folders:
 meta=json.loads((data/'manifest.json').read_text());assert hashlib.sha256((data/'data.npz').read_bytes()).hexdigest()==meta['data_sha256']
 plan=json.loads((rawroot/'plan.json').read_text())
 with np.load(data/'data.npz',allow_pickle=False) as z:h=z['h1'];game=z['game'];rounds=z['engine_round']
 for i,e in enumerate(meta['episodes']):
  m=next(m for m in plan['maps'] if m['sha256']==e['map_sha256']);name=m['file'].split('.')[0]+'-'+e['opponent']+'-'+e['side'];stats=json.loads((rawroot/(name+'.json')).read_text())
  assert stats['match']['mapHash']==e['map_sha256'] and stats['diagnostics']['detailedCaptureComplete']
  ix=np.flatnonzero(game==i);assert len(ix)==e['rows']
  chosen=ix[np.linspace(0,len(ix)-1,32).astype(int)]
  score=features(stats,rounds[chosen],'team'+e['side'])
  # Score-only model first: smaller state space and fewer ways to memorize
  # map geometry than an unconstrained MLP over native embeddings.
  X.append(score);Y.extend([e['outcome']]*32);F.extend([e['family']]*32);G.extend([gid]*32);gid+=1
 sources.append(dict(manifest_sha256=hashlib.sha256((data/'manifest.json').read_bytes()).hexdigest(),games=len(meta['episodes'])))
x=torch.from_numpy(np.concatenate(X));y=torch.tensor(Y,dtype=torch.float32);fam=np.array(F);game=np.array(G)
family_order=sorted(set(fam),key=lambda f:hashlib.sha256(('jd-value-family-v1:'+f).encode()).hexdigest());assert len(family_order)==40
validation_families=set(family_order[:8]);val=np.array([f in validation_families for f in fam]);train=~val
# Regularized linear logistic expected-return baseline. No map/team IDs.
mean=x[train].mean(0);std=x[train].std(0).clamp_min(.1);xx=((x-mean)/std).clamp(-8,8)
model=nn.Linear(8,1);nn.init.zeros_(model.weight);nn.init.zeros_(model.bias)
opt=torch.optim.LBFGS(model.parameters(),lr=1.,max_iter=100,line_search_fn='strong_wolfe')
target=(y+1)/2
# A game contributes total likelihood weight1, not32 independent reward labels.
def closure():
 opt.zero_grad();logits=model(xx[train]).squeeze(1)
 data_loss=nn.functional.binary_cross_entropy_with_logits(logits,target[train],reduction='sum')/32
 prior=.5*(model.weight.square().sum()+model.bias.square().sum())
 loss=data_loss+prior;loss.backward();return loss
opt.step(closure)
with torch.no_grad():pred=(2*model(xx).squeeze(1).sigmoid()-1).numpy()
constant=float(y[train].mean());t=y.numpy();pergame=[]
for g in sorted(set(game[val])):
 sel=game==g;pergame.append(dict(game=int(g),family=str(fam[sel][0]),model_mse=float(np.mean((pred[sel]-t[sel])**2)),constant_mse=float(np.mean((constant-t[sel])**2)),zero_mse=float(np.mean(t[sel]**2))))
clusters=[np.array([v['model_mse']-v['constant_mse'] for v in pergame if v['family']==f]) for f in validation_families];rng=np.random.default_rng(110412)
boot=[float(np.concatenate([clusters[i] for i in rng.integers(len(clusters),size=len(clusters))]).mean()) for _ in range(10000)];ci=list(map(float,np.quantile(boot,[.025,.975])))
# Verify that changing SAME/FUTURE-round event timing cannot alter a baseline
# feature at an earlier query round, by exercising prefix lookup directly.
from past_score_features import past_total
assert past_total((np.array([5,10,15]),np.array([0,2,7,16])),np.array([5,10,11])).tolist()==[0,2,7]
validated=ci[1]<0;out.mkdir();torch.save(dict(architecture='jd-past-score-logistic-value-v1',state=model.state_dict(),mean=mean,std=std,clamp=8.,sources=sources,trained_prior_games=gid,validation_families=sorted(validation_families),validated_against_constant=validated),out/'value.pt')
report=dict(scope='Past-data-only training value baseline; no actor update or gameplay improvement claim',past_games=gid,training_games=len(set(game[train])),validation_games=len(set(game[val])),training_families=32,validation_families=8,parameters=9,feature_names=['round/2000','own score/1000','enemy score/1000','score margin/1000','own fraction','own50roundgain/100','enemy50roundgain/100','50roundmarginchange/100'],timestamp_contract='GemSubmission timestamps strictly less than actual command engine_round; same/future-round events excluded; event sums checked against final score for accounting only',objective='Game-weighted binary log likelihood plus unit Gaussian weight penalty; value=2sigmoid(logit)-1',train_mse=float(np.mean((pred[train]-t[train])**2)),validation_mse=float(np.mean((pred[val]-t[val])**2)),validation_constant_mse=float(np.mean((constant-t[val])**2)),validation_zero_mse=float(np.mean(t[val]**2)),family_cluster_95_mse_difference=ci,validated_against_constant=validated,past_only_prefix_check='pass',limitations=['Regularized logistic predictor, not a calibrated Bayesian posterior.', 'Game weighting prevents counting32 frames as32 independent terminal rewards; uncertainty is clustered by held-out family.', 'Predictive gain does not establish policy-gradient variance reduction or playing-strength gain.', 'Must freeze before using it on future actor batches; no same-batch return fitting.'],per_game=pergame)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(r.parent.parent/'outputs/rl-execution/PAST_SCORE_VALUE_BASELINE.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='per_game'},indent=2))
