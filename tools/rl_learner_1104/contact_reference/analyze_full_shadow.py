from pathlib import Path
import json,numpy as np
r=Path(__file__).resolve().parents[1];p=r/'runs/native-contact-shadow-dev';plan=json.loads((p/'plan.json').read_text());runs=json.loads((p/'runs.json').read_text());previous=json.loads((r.parent.parent/'outputs/rl-execution/NATIVE_UPPER_GREEDY_EVAL.json').read_text());cells=[c for c in previous['cells'] if c['candidate']=='upper5']
for row in runs['games']:
 assert row['returncode']==0
 d=json.loads(Path(row['stats']).read_text());assert d['diagnostics']['detailedCaptureComplete'] and not any(d['diagnostics']['botFaults'].values())
 if row['candidate']=='upper5':continue
 team='team'+row['side'];assert d['match']['mapHash']==row['map_sha256'];score=.5 if d['match']['outcome']=='draw' else float(d['match']['outcome']==team);fuel=sum(len(e['entries']) for e in d['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')==team)
 cells.append(dict(candidate='shadow',opponent=row['opponent'],map=row['map'],family=row['family'],side=row['side'],score=score,own_fuel_outs=fuel))
pairs={};comparisons={};rng=np.random.default_rng(110701)
for c in ['upper5','shadow']:
 for o in ['v92','native']:
  z=[x for x in cells if x['candidate']==c and x['opponent']==o];assert len(z)==30;pairs[c+'-vs-'+o]=dict(games=30,wins=sum(x['score']==1 for x in z),draws=sum(x['score']==.5 for x in z),own_fuel_outs=sum(x['own_fuel_outs'] for x in z))
for opp in ['v92','native']:
 aa={(c['map'],c['side']):c for c in cells if c['candidate']=='shadow' and c['opponent']==opp};bb={(c['map'],c['side']):c for c in cells if c['candidate']=='upper5' and c['opponent']==opp};assert aa.keys()==bb.keys();fam={}
 for k,c in aa.items():fam.setdefault(c['family'],[]).append(c['score']-bb[k]['score'])
 groups=[np.array(v) for v in fam.values()];boot=[float(np.concatenate([groups[i] for i in rng.integers(len(groups),size=len(groups))]).mean()) for _ in range(10000)];comparisons[opp]=dict(delta_score_rate=float(np.mean([aa[k]['score']-bb[k]['score'] for k in aa])),family_cluster_95=list(map(float,np.quantile(boot,[.025,.975]))))
report=dict(scope='Full-game QUIET SHADOW inference-cost impact; no verdict/action override, no learned improvement claim',new_games=61,pairs=pairs,comparisons=comparisons,control='Pinned v107greedy repeat fullstatistics identical before baselinecache reuse',artifacts=plan['artifacts'],cells=cells,limitations=['No softmax/sampling/acting overhead included; nontrained head outputs go tovolatile sink toretainarithmetic.','Scorescomputed on everyfreshfinalcontact<=6 when>=25k fuel; earlierburst/ambush/capture returns andlowfuel casesexcluded.','Contactfeatures consume fuel and canchange downstream trajectories or background NN refreshes even without explicit actionoverrides.','15previouslyexposeddevmaps/two relatedfrozenopponents; no broadladderstrengthclaim.'])
(r.parent.parent/'outputs/rl-execution/CONTACT_FULL_RUNTIME_EVAL.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(pairs=pairs,comparisons=comparisons),indent=2))
