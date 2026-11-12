"""Apply a completed, same-code policy grid to v67's own map assignment data."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--grid',default='cal25-policy-grid')
    a=ap.parse_args()
    folder=ROOT/'artifacts/evaluations/v67'/a.grid
    experiment=json.loads((folder/'experiment.json').read_text())
    assert not set(experiment['seeds'])&{3,4}
    suggestions=json.loads((folder/'suggested.json').read_text())
    base=ROOT/'artifacts/evaluations/v67'/experiment['base']
    games=json.loads((base/'games.json').read_text())['games']
    lookup={(r['map'],r['side'],r['seed']):r for r in games}
    src=ROOT/'bots/v67/src'
    assignment=json.loads((src/'assignment.json').read_text())
    original={(r['map'],s):r[s] for r in assignment['maps'] for s in ['a','b']}
    rows=[json.loads(line) for line in (folder/'rows.jsonl').read_text().splitlines()]
    checks=[]
    for r in rows:
        if r['policy']==original[r['map'],r['side']]:
            b=lookup[r['map'],r['side'],r['seed']]
            checks.append((r['gems']-r['opponent_gems'])==b['margin'])
    assert checks and all(checks),'same-policy outcomes must reproduce exactly'
    assert not any(r['faults'] for r in rows),'investigate faults before applying calibration'
    baseline_by_case=defaultdict(list)
    for row in games: baseline_by_case[row['map']+'|'+row['side']].append(row)
    strict=outcome=0
    for case,group in baseline_by_case.items():
        if case in suggestions['choices']:
            p=str(suggestions['choices'][case]); metrics=suggestions['metrics'][case][p]
            strict+=metrics['strict_wins']; outcome+=metrics['wins']
        else:
            strict+=sum(r['margin']>0 for r in group); outcome+=sum(r['win'] for r in group)
    changed=[]
    for row in assignment['maps']:
        for side in ['a','b']:
            case=row['map']+'|'+side
            if case not in suggestions['choices']: continue
            index=int(suggestions['choices'][case])
            if index!=row[side]: changed.append(dict(map=row['map'],side=side,before=row[side],after=index))
            row[side]=index
            assignment['values'][row['slot']*2+(side=='b')+2]=index
    proposal=dict(base=experiment['base'],grid=a.grid,training_seeds=experiment['seeds'],diagnostic_games=len(rows),
                  exact_equivalence_checks=len(checks),expected_strict_wins=strict,expected_outcome_wins=outcome,
                  status='prediction_requires_full_fresh_benchmark',changes=changed)
    p=src/'main.cpp'; source=p.read_text(encoding='utf8')
    initializer=f"volatile std::int32_t policy_assignment67[{len(assignment['values'])}]={{"+','.join(map(str,assignment['values']))+'};'
    source,n=re.subn(r'volatile std::int32_t policy_assignment67\[\d+\]=\{[^}]+\};',lambda m:initializer,source)
    assert n==1
    p.write_text(source,encoding='utf8',newline='\n')
    (src/'assignment.json').write_text(json.dumps(assignment,indent=1)+'\n',encoding='utf8')
    selection=json.loads((src/'selection.json').read_text())
    selection['calibration']=proposal
    names={r['index']:r['run'] for r in selection['policies']}
    selection['map_side']={r['map']:{s:names[r[s]] for s in ['a','b']} for r in assignment['maps']}
    selection['note']='map_side is the current selector; maps retains the initial pre-calibration map-only selection'
    (src/'selection.json').write_text(json.dumps(selection,indent=1)+'\n',encoding='utf8')
    (ROOT/'research/v67/CALIBRATION.json').write_text(json.dumps(proposal,indent=1)+'\n',encoding='utf8')
    print(json.dumps(proposal,indent=2))


if __name__=='__main__': main()
