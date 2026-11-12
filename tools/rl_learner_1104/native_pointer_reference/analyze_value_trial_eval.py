from pathlib import Path
import json,numpy as np,hashlib
r=Path(__file__).resolve().parents[1];p=r/'runs/native-value-paired-dev';plan=json.loads((p/'plan.json').read_text());runs=json.loads((p/'runs.json').read_text());previous=json.loads((r.parent.parent/'outputs/rl-execution/NATIVE_UPPER_GREEDY_EVAL.json').read_text())
for name in ['upper5','native','v92']:assert plan['artifacts'][name]['sha256']==previous['artifacts'][name]['sha256']
cells=[c for c in previous['cells'] if c['candidate']=='upper5'];assert len(cells)==60
for row in runs['games']:
 assert row['returncode']==0
 d=json.loads(Path(row['stats']).read_text());team='team'+row['side'];assert d['match']['mapHash']==row['map_sha256'] and d['diagnostics']['detailedCaptureComplete'] and not any(d['diagnostics']['botFaults'].values())
 if row['candidate']=='upper5':continue
 outcome=d['match']['outcome'];score=.5 if outcome=='draw' else float(outcome==team)
 fuel=sum(len(e['entries']) for e in d['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')==team)
 cells.append(dict(candidate=row['candidate'],opponent=row['opponent'],map=row['map'],family=row['family'],side=row['side'],score=score,own_fuel_outs=fuel))
assert len(cells)==180;pairs={};comparisons={};rng=np.random.default_rng(110625)
for opp in ['v92','native']:
 for a in ['upper5','zero','value']:
  z=[c for c in cells if c['candidate']==a and c['opponent']==opp];assert len(z)==30
  pairs[a+'-vs-'+opp]=dict(games=30,wins=sum(c['score']==1 for c in z),draws=sum(c['score']==.5 for c in z),losses=sum(c['score']==0 for c in z),own_fuel_outs=sum(c['own_fuel_outs'] for c in z))
 for a,b in [('value','zero'),('zero','upper5'),('value','upper5')]:
  aa={(c['map'],c['side']):c for c in cells if c['candidate']==a and c['opponent']==opp};bb={(c['map'],c['side']):c for c in cells if c['candidate']==b and c['opponent']==opp};assert aa.keys()==bb.keys();fam={}
  for k,c in aa.items():fam.setdefault(c['family'],[]).append(c['score']-bb[k]['score'])
  groups=[np.array(v) for v in fam.values()];boot=[float(np.concatenate([groups[i] for i in rng.integers(len(groups),size=len(groups))]).mean()) for _ in range(10000)]
  comparisons[a+'-minus-'+b+'_vs_'+opp]=dict(delta=float(np.mean([aa[k]['score']-bb[k]['score'] for k in aa])),families=len(groups),family_cluster_95=list(map(float,np.quantile(boot,[.025,.975]))))
report=dict(scope='Predeclared frozen-prior-value vs zero on-policy training comparison; DEVELOPMENT only',fresh_evaluation_games=121,cached_initial_cells=60,control='Repeated pinnedupper5 control fullstatistics identical beforecache reuse',training_plan_sha256=hashlib.sha256((r/'runs/native-value-paired-01/plan.json').read_bytes()).hexdigest(),pairs=pairs,comparisons=comparisons,artifacts=plan['artifacts'],cells=cells,limitations=['One paired training seed schedule, two related frozen opponents; not proof of broad ladder superiority.','No currentopponentcode available fromuserreplays; live outcomes must be version-verified separately.','Training baseline predicts prior-state outcome; noactorinferencecost, but predictiongain alone is not astrengthgain.','Developmentmaps previouslyexposed; confirmationeligibility separately excludesVault/TheLine/Swirl.'])
(r.parent.parent/'outputs/rl-execution/PAIRED_VALUE_DEVELOPMENT_EVAL.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['cells','artifacts']},indent=2))
