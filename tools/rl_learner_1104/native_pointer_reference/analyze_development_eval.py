from pathlib import Path
import json,hashlib,numpy as np
r=Path(__file__).resolve().parents[1];p=r/'runs/native-query-update01-dev';plan=json.loads((p/'plan.json').read_text());runs=json.loads((p/'runs.json').read_text())
cells=[]
for x in runs['games']:
 assert x['returncode']==0
 d=json.loads(Path(x['stats']).read_text());team='team'+x['side'];assert d['match']['mapHash']==x['map_sha256']
 assert d['diagnostics']['detailedCaptureComplete'] and not any(d['diagnostics']['botFaults'].values())
 outcome=d['match']['outcome'];score=.5 if outcome=='draw' else float(outcome==team)
 fuel=sum(len(e['entries']) for e in d['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')==team)
 other='teamB' if team=='teamA' else 'teamA'
 oppfuel=sum(len(e['entries']) for e in d['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')==other)
 cells.append(dict(candidate=x['candidate'],opponent=x['opponent'],map=x['map'],family=x['family'],side=x['side'],score=score,own_fuel_outs=fuel,opponent_fuel_outs=oppfuel))
pairs={}
for a,b in plan['pairs']:
 z=[c for c in cells if c['candidate']==a and c['opponent']==b];assert len(z)==30
 pairs[a+'-vs-'+b]=dict(games=30,wins=sum(c['score']==1 for c in z),draws=sum(c['score']==.5 for c in z),losses=sum(c['score']==0 for c in z),score=sum(c['score'] for c in z),own_fuel_outs=sum(c['own_fuel_outs'] for c in z),opponent_fuel_outs=sum(c['opponent_fuel_outs'] for c in z))
rng=np.random.default_rng(110409)
def comparison(a,b,opponent):
 aa={(c['map'],c['side']):c for c in cells if c['candidate']==a and c['opponent']==opponent};bb={(c['map'],c['side']):c for c in cells if c['candidate']==b and c['opponent']==opponent}
 assert aa.keys()==bb.keys() and len(aa)==30
 fam={}
 for k,c in aa.items():fam.setdefault(c['family'],[]).append(c['score']-bb[k]['score'])
 groups=[np.asarray(v) for v in fam.values()];boot=[]
 for _ in range(10000):
  selected=rng.integers(len(groups),size=len(groups));boot.append(float(np.concatenate([groups[i] for i in selected]).mean()))
 return dict(delta_score_rate=float(np.mean([aa[k]['score']-bb[k]['score'] for k in aa])),families=len(groups),family_cluster_bootstrap_95=list(map(float,np.quantile(boot,[.025,.975]))),identical_win_scores=sum(aa[k]['score']==bb[k]['score'] for k in aa))
comp={'u1-minus-u0_vs_v92':comparison('u1','u0','v92'),'u1-minus-u0_vs_native':comparison('u1','u0','native'),'u1-minus-native_vs_v92':comparison('u1','native','v92')}
report=dict(scope='Matched DEVELOPMENT evaluation after first real native-query RL update; no sealed holdout/ladder/future superiority claim',games=len(cells),maps=15,families=len({c['family'] for c in cells}),wall_seconds=runs['wall_seconds'],pairs=pairs,comparisons=comp,artifact_hashes={k:v['sha256'] for k,v in plan['artifacts'].items()},collection_logging='disabled in initial/learned deployment artifacts; unused added-head snapshot copies and skip logging removed from both',limitations=['One compiled policy RNG seed; both sides/maps/opponents, not independent policy seed replications.','Opponents are related frozen v92/native; more diverse current teams required for broad performance claim.','Development maps have prior experimental exposure; confirmation_reserved not used.','Bootstrap clusters the13 map families, not112k training decisions.','A single small update may not establish a detectable advantage.'],cells=cells)
out=r.parent.parent/'outputs/rl-execution/NATIVE_QUERY_DEVELOPMENT_EVAL.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('cells','limitations','artifact_hashes')},indent=2))
