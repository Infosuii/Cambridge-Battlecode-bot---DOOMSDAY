"""Paired fixed reserve5000 ablation against the exact cached reserve1000 v107."""
from pathlib import Path
import hashlib
import json
import numpy as np

root=Path(__file__).resolve().parents[1]
out=root/'runs/native-upper-commit8-dev'
baseline=root/'runs/native-upper-greedy-dev'
newsrc=root/'native-upper-commit8/bots/submission/src'
oldsrc=root/'native-upper-greedy/bots/submission/src'
assert {p.name for p in newsrc.iterdir()}=={p.name for p in oldsrc.iterdir()}
assert all(p.read_bytes()==(oldsrc/p.name).read_bytes() for p in newsrc.iterdir() if p.name!='jd_native_actor.inc')
assert (newsrc/'jd_native_actor.inc').read_bytes()!=(oldsrc/'jd_native_actor.inc').read_bytes()
plan=json.loads((out/'plan.json').read_text());runs=json.loads((out/'runs.json').read_text())
assert len(runs['games'])==60
cells=[]
for row in runs['games']:
    assert row['returncode']==0
    a=json.loads(Path(row['stats']).read_text())
    b=json.loads((baseline/Path(row['stats']).name).read_text())
    assert a['match']['seed']==b['match']['seed'] and a['match']['mapHash']==b['match']['mapHash']==row['map_sha256']
    assert a['diagnostics']['detailedCaptureComplete'] and not any(a['diagnostics']['botFaults'].values())
    team='team'+row['side']
    def score(s):return .5 if s['match']['outcome']=='draw' else float(s['match']['outcome']==team)
    def fuel(s):return sum(len(e['entries']) for e in s['events'] if e['kind']=='fuelExhausted' and e['owner'].get('team')==team)
    cells.append(dict(map=row['map'],family=row['family'],side=row['side'],opponent=row['opponent'],
                      baseline_score=score(b),candidate_score=score(a),baseline_fuel=fuel(b),candidate_fuel=fuel(a),
                      baseline_rounds=b['match']['roundsCompleted'],candidate_rounds=a['match']['roundsCompleted']))
rng=np.random.default_rng(110750);pairs={}
for opponent in ['v92','native']:
    cc=[c for c in cells if c['opponent']==opponent]
    families=sorted({c['family'] for c in cc})
    groups=[np.array([c['candidate_score']-c['baseline_score'] for c in cc if c['family']==f]) for f in families]
    bootstrap=[np.concatenate([groups[i] for i in rng.integers(len(groups),size=len(groups))]).mean() for _ in range(10000)]
    pairs[opponent]=dict(games=len(cc),families=len(families),
        baseline_wins=sum(c['baseline_score']==1 for c in cc),candidate_wins=sum(c['candidate_score']==1 for c in cc),
        baseline_draws=sum(c['baseline_score']==.5 for c in cc),candidate_draws=sum(c['candidate_score']==.5 for c in cc),
        paired_score_delta=float(np.mean([c['candidate_score']-c['baseline_score'] for c in cc])),
        paired_family_bootstrap_95=np.quantile(bootstrap,[.025,.975]).tolist(),
        baseline_fuel=sum(c['baseline_fuel'] for c in cc),candidate_fuel=sum(c['candidate_fuel'] for c in cc),
        baseline_fuel_per1000_rounds=1000*sum(c['baseline_fuel'] for c in cc)/sum(c['baseline_rounds'] for c in cc),
        candidate_fuel_per1000_rounds=1000*sum(c['candidate_fuel'] for c in cc)/sum(c['candidate_rounds'] for c in cc))
report=dict(scope='Fixed8round command commitment DEVELOPMENT feasibility; not learned options or ladder validation',
            change='Fixed8round target hold, terminate on invalid state,visible enemy,lowHP or deadline; only jd_native_actor.inc changed; header6661 andreserve1000 unchanged',
            runtime_source_difference_checked=True,plan=plan,pairs=pairs,cells=cells,wall_seconds=runs['wall_seconds'],
            limitations=['Fixed-duration rule changes command trajectories; does not implement learned option termination.',
                         'Existing downstream executor may cancel/reassign the commanded group; no full physical control claim.',
                         'Same exposed15 development maps/13 families and related opponents; no untouched confirmation.',
                         'One preset tested, no parameter sweep or candidate selected during the test.'])
(root.parent.parent/'outputs/rl-execution/COMMIT8_DEVELOPMENT_EVAL.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['cells','plan']},indent=2))
