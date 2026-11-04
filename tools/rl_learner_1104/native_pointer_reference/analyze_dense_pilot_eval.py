"""Report the single-update pilot against its matched terminal-only control."""
from pathlib import Path
import json
import numpy as np
from gem_accounting import audit

root=Path(__file__).resolve().parents[1]
folder=root/'runs/native-dense-pilot-dev'
runs=json.loads((folder/'runs.json').read_text())
assert len(runs['games'])==121
cells=[]
for run in runs['games']:
    assert run['returncode']==0
    s=json.loads(Path(run['stats']).read_text());audit(s)
    assert s['match']['mapHash']==run['map_sha256']
    if run['candidate']=='upper5':
        old=root/'runs/native-upper-greedy-dev'/Path(run['stats']).name
        assert s==json.loads(old.read_text())
        continue
    team='team'+run['side'];other='teamB' if team=='teamA' else 'teamA'
    camp={team:0,other:0}
    for e in s['events']:
        if e['kind']=='gemCollection':
            camp[e['owner']['team']]+=sum(int(x['value']) for x in e['entries'] if x.get('context')=='campGroup')
    outcome=s['match']['outcome']
    cells.append(dict(arm=run['candidate'],opponent=run['opponent'],map=run['map'],family=run['family'],side=run['side'],
                      score=.5 if outcome=='draw' else float(outcome==team),
                      camp_margin=camp[team]-camp[other],own_camp_collection=camp[team],enemy_camp_collection=camp[other],
                      rounds=s['match']['roundsCompleted'],seed=s['match']['seed'],
                      fuel=sum(len(e['entries']) for e in s['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')==team)))
initial=json.loads((root.parent.parent/'outputs/rl-execution/NATIVE_UPPER_GREEDY_EVAL.json').read_text())
rng=np.random.default_rng(110752);report={}
for opponent in ['v92','native']:
    cc={arm:[c for c in cells if c['arm']==arm and c['opponent']==opponent] for arm in ['control','dense']}
    bykey={arm:{(c['map'],c['side']):c for c in rows} for arm,rows in cc.items()}
    assert bykey['control'].keys()==bykey['dense'].keys()
    assert all(bykey['control'][key]['seed']==bykey['dense'][key]['seed'] for key in bykey['control'])
    entry={}
    for arm,rows in cc.items():
        assert len(rows)==30
        entry[arm]=dict(wins=sum(c['score']==1 for c in rows),draws=sum(c['score']==.5 for c in rows),
                        own_fuel=sum(c['fuel'] for c in rows),mean_camp_margin=float(np.mean([c['camp_margin'] for c in rows])),
                        mean_own_camp_collection=float(np.mean([c['own_camp_collection'] for c in rows])))
    family=sorted({c['family'] for c in cc['dense']})
    for metric in ['score','camp_margin']:
        groups=[np.array([c[metric]-bykey['control'][c['map'],c['side']][metric] for c in cc['dense'] if c['family']==f]) for f in family]
        boot=[np.concatenate([groups[i] for i in rng.integers(len(groups),size=len(groups))]).mean() for _ in range(10000)]
        entry['dense_minus_control_'+metric]=dict(mean=float(np.mean(np.concatenate(groups))),family_bootstrap95=np.quantile(boot,[.025,.975]).tolist())
    entry['initial_upper5']=initial['pairs']['upper5-vs-'+opponent]
    report[opponent]=entry
out=dict(scope='Single32-game dense-reward pilot, two PPO steps; DEVELOPMENT evidence only, not a160-game training conclusion',
         reward='Terminal±1 plus strictly future150-round own-minus-enemy team camp gems/200; frozen terminal-only baseline, dense baseline0',
         control='Same initial checkpoint+Adam+32game batch+PPO, terminal-only frozen baseline update',
         eval_games=120,additional_cached_baseline_control_game=1,training_games_reused=32,training_rows=127879,pairs=report,cells=cells,
         all_event_accounting_checked=True,wall_seconds=runs['wall_seconds'],
         limitations=['Same exposed15 development maps/13 families and related v92/native opponents.',
                      'Training batch reused on-policy at identical starting checkpoint; not independent fresh training evidence.',
                      'No coefficient sweep or model selection inside this fixed pilot.',
                      'Dense reward changes objective, not policy-invariant shaping; wins remain decisive.',
                      'Greedy deployment differs from stochastic training; any advantage needs broader validation.'])
target=root.parent.parent/'outputs/rl-execution/DENSE_REWARD_PILOT_EVAL.json';target.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='cells'},indent=2))
