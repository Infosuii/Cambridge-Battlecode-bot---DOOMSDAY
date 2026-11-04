"""Chronological external test: freeze the prior-query score baseline on new upper games."""
from pathlib import Path
import json,hashlib,numpy as np,torch
from torch import nn
from past_score_features import features
r=Path(__file__).resolve().parents[1];p=Path(__file__).parent;torch.set_num_threads(2)
prior=json.loads((p/'value_score01/report.json').read_text());frozen=json.loads((p/'frozen_prior_value.json').read_text())
ck=dict(mean=torch.tensor(frozen['mean']),std=torch.tensor(frozen['std']),validation_families=sorted({x['family'] for x in prior['per_game']}))
m=nn.Linear(8,1);m.load_state_dict(dict(weight=torch.tensor(frozen['weight']),bias=torch.tensor(frozen['bias'])));m.eval()
folders=[(p/'upper_batch01',r/'runs/native-upper-u0-mac32-02')]+[(r/'runs/native-upper-continuation-01'/('cycle'+str(i))/'data',r/'runs/native-upper-continuation-01'/('cycle'+str(i))/'raw') for i in range(1,5)]
rows=[]
for data,raw in folders:
 meta=json.loads((data/'manifest.json').read_text());assert hashlib.sha256((data/'data.npz').read_bytes()).hexdigest()==meta['data_sha256'];plan=json.loads((raw/'plan.json').read_text())
 with np.load(data/'data.npz') as z:game=z['game'];rounds=z['engine_round']
 for i,ep in enumerate(meta['episodes']):
  ix=np.flatnonzero(game==i);assert len(ix)==ep['rows'];chosen=ix[np.linspace(0,len(ix)-1,32).astype(int)];mp=next(x for x in plan['maps'] if x['sha256']==ep['map_sha256']);name=mp['file'].split('.')[0]+'-'+ep['opponent']+'-'+ep['side'];stats=json.loads((raw/(name+'.json')).read_text());x=torch.from_numpy(features(stats,rounds[chosen],'team'+ep['side']))
  with torch.no_grad():pred=2*m(((x-ck['mean'])/ck['std']).clamp(-8,8)).squeeze(1).sigmoid()-1
  y=ep['outcome'];rows.append(dict(family=ep['family'],map=mp['file'],side=ep['side'],opponent=ep['opponent'],model_mse=float(((pred-y)**2).mean()),zero_mse=float(y*y),previously_held_family=ep['family'] in ck['validation_families']))
families=sorted({x['family'] for x in rows});assert len(families)==40 and len(rows)==160
rng=np.random.default_rng(110521);clusters=[np.array([x['model_mse']-x['zero_mse'] for x in rows if x['family']==f]) for f in families];boot=[float(np.concatenate([clusters[j] for j in rng.integers(len(clusters),size=len(clusters))]).mean()) for _ in range(10000)];ci=list(map(float,np.quantile(boot,[.025,.975])))
report=dict(scope='Untuned prior-query baseline tested chronologically on160 subsequent upper-model games; no actor update/strength/gradient-variance claim',baseline_sha256=frozen['source_checkpoint_sha256'],frozen_baseline_json_sha256=hashlib.sha256((p/'frozen_prior_value.json').read_bytes()).hexdigest(),baseline_training_games=prior['training_games'],future_games=160,future_families=40,model_mse=float(np.mean([x['model_mse'] for x in rows])),zero_mse=float(np.mean([x['zero_mse'] for x in rows])),family_cluster_95_difference=ci,validated_against_zero=ci[1]<0,previously_unseen_family_mse=float(np.mean([x['model_mse'] for x in rows if x['previously_held_family']])),per_game=rows,limitations=['Future games share mapfamilies withpriortraining except8 heldfamilies, so this is chronological rather than wholly new-map validation.','Prediction MSE is not the policy-gradient covariance or a strength result.','No model refit or hyperparameter choice based on these future outcomes; baseline remains frozen.'])
(r.parent.parent/'outputs/rl-execution/PRIOR_VALUE_FUTURE_EVAL.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['per_game','limitations']},indent=2))
