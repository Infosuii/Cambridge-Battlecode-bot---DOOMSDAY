from pathlib import Path
import json,numpy as np
r=Path(__file__).resolve().parents[1];folder=r/'runs/native-upper-greedy-dev';plan=json.loads((folder/'plan.json').read_text());runs=json.loads((folder/'runs.json').read_text());cells=[]
for row in runs['games']:
 assert row['returncode']==0
 d=json.loads(Path(row['stats']).read_text());team='team'+row['side'];assert d['match']['mapHash']==row['map_sha256'] and d['diagnostics']['detailedCaptureComplete'] and not any(d['diagnostics']['botFaults'].values())
 outcome=d['match']['outcome'];score=.5 if outcome=='draw' else float(outcome==team)
 def fuel(t):return sum(len(e['entries']) for e in d['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')==t)
 cells.append(dict(candidate=row['candidate'],opponent=row['opponent'],map=row['map'],family=row['family'],side=row['side'],score=score,own_fuel_outs=fuel(team),opponent_fuel_outs=fuel('teamB' if team=='teamA' else 'teamA')))
pairs={};comparisons={};rng=np.random.default_rng(110515)
for opponent in ['v92','native']:
 z={a:[c for c in cells if c['candidate']==a and c['opponent']==opponent] for a in ['upper0','upper5']};n=30 if opponent in ['v92','native'] else 8
 for a,v in z.items():
  assert len(v)==n;pairs[a+'-vs-'+opponent]=dict(games=n,wins=sum(c['score']==1 for c in v),draws=sum(c['score']==.5 for c in v),losses=sum(c['score']==0 for c in v),own_fuel_outs=sum(c['own_fuel_outs'] for c in v),score_rate=float(np.mean([c['score'] for c in v])))
 aa={(c['map'],c['side']):c for c in z['upper5']};bb={(c['map'],c['side']):c for c in z['upper0']};assert aa.keys()==bb.keys();fam={}
 for k,c in aa.items():fam.setdefault(c['family'],[]).append(c['score']-bb[k]['score'])
 groups=[np.asarray(v) for v in fam.values()];boot=[float(np.concatenate([groups[i] for i in rng.integers(len(groups),size=len(groups))]).mean()) for _ in range(10000)]
 comparisons[opponent]=dict(delta_score_rate=float(np.mean([aa[k]['score']-bb[k]['score'] for k in aa])),families=len(groups),family_cluster_bootstrap_95=list(map(float,np.quantile(boot,[.025,.975]))))
report=dict(scope='Scheduled matched GREEDY deployment evaluation after5 upper-trunk/query training batches; separate from categorical training policy, no sealed holdout or ladder claim',games=len(cells),primary_maps=15,primary_families=13,public_maps=plan['public_maps'],pairs=pairs,comparisons=comparisons,artifacts=plan['artifacts'],wall_seconds=runs['wall_seconds'],deterministic_argmax=True,logging_disabled=True,compiled_seed=110401,limitations=['Native/v92 are related opponents; public3 policies are older weaker snapshots, not current ladder proof.','Public pool uses4 outcome-independently selectedfamilies; counts8 perpair are small.','All evaluation maps DEVELOPMENT, previously exposed; external live replay exposure is separately tracked in LIVE_REPLAY_EXPOSURE_OVERLAY.json.','One shared policy RNGseed for matched comparison, no independent-seed replication claim.','No model/temperature choice made inside trainingblock; evaluation is a checkpoint, not evidence of future superiority.'],cells=cells)
(r.parent.parent/'outputs/rl-execution/NATIVE_UPPER_GREEDY_EVAL.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['cells','artifacts','public_maps']},indent=2))
