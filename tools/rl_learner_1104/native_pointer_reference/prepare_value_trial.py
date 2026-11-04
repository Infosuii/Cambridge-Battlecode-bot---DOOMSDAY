"""Prepare fixed prior-only baseline and isolated matched learner/collector scripts."""
from pathlib import Path
import json,torch,hashlib
p=Path(__file__).parent
# This checkpoint was authored locally; only its prior-trained tensor payload
# is re-exported. New consumers use plain JSON, never arbitrary pickle input.
ck=torch.load(p/'value_score01/value.pt',weights_only=False,map_location='cpu')
frozen=dict(architecture='jd-past-score-logistic-value-v1',source_checkpoint_sha256=hashlib.sha256((p/'value_score01/value.pt').read_bytes()).hexdigest(),weight=ck['state']['weight'].tolist(),bias=ck['state']['bias'].tolist(),mean=ck['mean'].tolist(),std=ck['std'].tolist(),clamp=8.,training_games=128,source='Prior query games ONLY; frozen before upper-model cohort, no future refit')
(p/'frozen_prior_value.json').write_text(json.dumps(frozen,indent=2)+'\n')
s=(p/'adapt_upper.py').read_text().replace('from upper_rows import read','from upper_rows import read\nfrom past_score_features import features')
s=s.replace(" episodes.append(ep);allrows+=rows;games += [i]*len(rows)"," vf=features(stats,np.array([v['engine_round'] for v in rows]),team)\n for v,f in zip(rows,vf):v['value_features']=f\n episodes.append(ep);allrows+=rows;games += [i]*len(rows)")
s=s.replace("('h0','h1','camps','present','valid')","('h0','h1','camps','present','valid','value_features')").replace("meta=dict(schema=", "meta=dict(value_feature_contract='Strictly prior-round gemSubmission history; no same/future-round events',schema=")
(p/'adapt_upper_value.py').write_text(s)
s=(p/'train_upper.py').read_text().replace("ap.add_argument('--checkpoint',type=Path);","ap.add_argument('--checkpoint',type=Path);ap.add_argument('--value-baseline',type=Path,required=True);")
needle="s=a.header.read_text();m=NativeUpper"
insert="""assert meta['value_feature_contract']=='Strictly prior-round gemSubmission history; no same/future-round events'
vb=json.loads(a.value_baseline.read_text());assert vb['architecture']=='jd-past-score-logistic-value-v1' and vb['clamp']==8.
vf=d['value_features'].float();assert vf.shape==(n,8) and torch.isfinite(vf).all()
vm=torch.tensor(vb['mean'],dtype=torch.float32);vs=torch.tensor(vb['std'],dtype=torch.float32);vw=torch.tensor(vb['weight'],dtype=torch.float32);vbi=torch.tensor(vb['bias'],dtype=torch.float32)
assert vm.shape==vs.shape==(8,) and vw.shape==(1,8) and vbi.shape==(1,) and (vs>0).all()
with torch.no_grad():baseline_predictions=2*torch.nn.functional.linear(((vf-vm)/vs).clamp(-8,8),vw,vbi).squeeze(1).sigmoid()-1
returns-=baseline_predictions.double()
"""
assert s.count(needle)==1;s=s.replace(needle,insert+needle).replace("baseline='fixed zero'","baseline='Frozen prior-query logistic score predictor; no same-batch fitting',baseline_sha256=sha(a.value_baseline),baseline_prediction_mean=float(baseline_predictions.mean())")
(p/'train_upper_value.py').write_text(s)
