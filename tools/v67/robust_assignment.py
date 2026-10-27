"""Choose a map/side portfolio across four development seeds with a training floor.

The reserved seeds3/4 are never read. The dynamic program maximizes wins on
development seeds5/6 while retaining at least --floor wins on seeds1/2.
"""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--grid',default='cal29-multiseed-grid')
    ap.add_argument('--floor',type=int,default=220)
    ap.add_argument('--apply',action='store_true')
    ap.add_argument('--base',help='New exact source baseline after a policy correction')
    ap.add_argument('--extra-base')
    ap.add_argument('--supplement-grid',action='append',default=[])
    ap.add_argument('--replace-policies',type=int,nargs='*',default=[])
    a=ap.parse_args()
    folder=ROOT/'artifacts/evaluations/v67'/a.grid
    ex=json.loads((folder/'experiment.json').read_text())
    assert set(ex['seeds'])=={1,2,5,6}
    bases=[a.base or ex['base'],a.extra_base or ex['extra_base']]
    roots=[ROOT/'artifacts/evaluations/v67'/name for name in bases]
    assignment=json.loads((roots[0]/'build/src-bot-s1/src/assignment.json').read_text())
    selection=json.loads((roots[0]/'build/src-bot-s1/src/selection.json').read_text())
    current={(r['map'],s):r[s] for r in assignment['maps'] for s in ['a','b']}
    original=[]
    for root in roots: original+=json.loads((root/'games.json').read_text())['games']
    required=defaultdict(set)
    options=defaultdict(dict)
    baseline=defaultdict(Counter)
    for r in original:
        case=(r['map'],r['side']); required[case].add(r['seed'])
        t=baseline[case]; prefix='train' if r['seed'] in (1,2) else 'fresh'
        t[prefix]+=(r['margin']>0); t['margin']+=r['margin'];t['fuel']+=r['fuel']
    for case,m in baseline.items(): options[case][current[case]]=dict(m)
    rows=[]
    for line in (folder/'rows.jsonl').read_text().splitlines():
        try:
            r=json.loads(line)
            if r['policy'] not in a.replace_policies:rows.append(r)
        except ValueError: pass
    for supplement in a.supplement_grid:
        for line in (ROOT/'artifacts/evaluations/v67'/supplement/'rows.jsonl').read_text().splitlines():
            try:rows.append(json.loads(line))
            except ValueError:pass
    groups=defaultdict(list)
    for r in rows: groups[(r['map'],r['side']),r['policy']].append(r)
    equivalents=[]
    lookup={(r['map'],r['side'],r['seed']):r for r in original}
    for (case,p),rs in groups.items():
        if p==current[case]:
            equivalents.extend(r['gems']-r['opponent_gems']==lookup[r['map'],r['side'],r['seed']]['margin'] for r in rs)
        if {r['seed'] for r in rs}!=required[case] or any(r['faults'] for r in rs):continue
        t=Counter()
        for r in rs:
            prefix='train' if r['seed'] in (1,2) else 'fresh'
            t[prefix]+=(r['gems']>r['opponent_gems'])*r['weight']
            t['margin']+=(r['gems']-r['opponent_gems'])*r['weight']
            t['fuel']+=r['fuel_exhausted']*r['weight']
        options[case][p]=dict(t)
    assert all(equivalents),'the same policy must reproduce its exact outcome on each development seed'
    # DP value is fresh wins, margin, negative fuel, chosen policy sequence.
    dp={0:(0,0,0,[])}
    cases=sorted(options)
    for case in cases:
        next_dp={}
        for train,(fresh,margin,negfuel,sequence) in dp.items():
            for p,m in options[case].items():
                n=train+m.get('train',0)
                candidate=(fresh+m.get('fresh',0),margin+m.get('margin',0),negfuel-m.get('fuel',0),sequence+[p])
                if n not in next_dp or candidate[:3]>next_dp[n][:3]: next_dp[n]=candidate
        dp=next_dp
    eligible=[(n,v) for n,v in dp.items() if n>=a.floor]
    assert eligible,'baseline should retain a feasible training floor'
    n,value=max(eligible,key=lambda item:(item[1][0],item[0],item[1][1],item[1][2]))
    chosen={case:p for case,p in zip(cases,value[3])}
    report=dict(grid=a.grid,source_bases=[str(r.relative_to(ROOT)) for r in roots],development_seeds=[1,2,5,6],
                supplement_grids=a.supplement_grid,replaced_policy_indices=a.replace_policies,
                diagnostic_rows=len(rows),equivalence_checks=len(equivalents),training_floor=a.floor,
                predicted_train_strict_wins=n,predicted_fresh_strict_wins=value[0],
                predicted_total_fuel=-value[2],predicted_margin_sum=value[1],
                choices={m+'|'+s:p for (m,s),p in chosen.items()},
                complete_options={m+'|'+s:len(v) for (m,s),v in options.items()},
                status='prediction_only_requires_rebuilt_full_benchmarks')
    (folder/'robust-proposal.json').write_text(json.dumps(report,indent=1)+'\n',encoding='utf8')
    print(json.dumps({k:report[k] for k in ['diagnostic_rows','equivalence_checks','training_floor','predicted_train_strict_wins','predicted_fresh_strict_wins','predicted_total_fuel']},indent=2))
    if not a.apply:return
    assert (folder/'suggested.json').exists(),'finish the diagnostic grid before applying'
    src=ROOT/'bots/v67/src'
    assert json.loads((src/'assignment.json').read_text())==assignment,'unexpected live source changes'
    for row in assignment['maps']:
        for side in ['a','b']:
            p=chosen.get((row['map'],side),row[side]);row[side]=p
            assignment['values'][row['slot']*2+(side=='b')+2]=p
    p=src/'main.cpp';source=p.read_text(encoding='utf8')
    initializer=f"volatile std::int32_t policy_assignment67[{len(assignment['values'])}]={{"+','.join(map(str,assignment['values']))+'};'
    source,count=re.subn(r'volatile std::int32_t policy_assignment67\[\d+\]=\{[^}]+\};',lambda m:initializer,source)
    assert count==1
    p.write_text(source,encoding='utf8',newline='\n')
    (src/'assignment.json').write_text(json.dumps(assignment,indent=1)+'\n',encoding='utf8')
    selection['robust_calibration']=report
    names={r['index']:r['run'] for r in selection['policies']}
    selection['map_side']={r['map']:{s:names[r[s]] for s in ['a','b']} for r in assignment['maps']}
    (src/'selection.json').write_text(json.dumps(selection,indent=1)+'\n',encoding='utf8')
    (ROOT/'research/v67/ROBUST_CALIBRATION.json').write_text(json.dumps(report,indent=1)+'\n',encoding='utf8')


if __name__=='__main__':main()
