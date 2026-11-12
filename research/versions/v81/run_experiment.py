"""Strict local run wrapper: fail on build/run errors; preserve exact frozen source, SDK and opponent provenance.

Usage: run_experiment.py RUN BOT OPP [--seed N] [--plan P] [--per-team] [--workers N]
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('bot');p.add_argument('opp')
p.add_argument('--seed',type=int,default=42);p.add_argument('--plan',default='research/v68/pool_plan.json')
p.add_argument('--per-team',action='store_true');p.add_argument('--workers',type=int,default=5)
a=p.parse_args()
out=ROOT/'artifacts/evaluations/v67'/a.run
cmd=[sys.executable,'tools/v67/raw_run.py','--run',a.run,'--bot',a.bot,'--opponent',a.opp,'--seeds',str(a.seed),
     '--plan',a.plan,'--bot-seed','1','--workers',str(a.workers)]
if a.per_team:cmd.append('--per-team')
result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf8',errors='replace')
if result.returncode:raise RuntimeError(result.stdout[-2000:]+'\n'+result.stderr[-2000:])
d=json.loads((out/'games.json').read_text());games=d['games']
plan=json.loads((ROOT/a.plan).read_text())
expected=sum(len(g['maps']) for g in plan['groups'])
assert len(games)==expected,(len(games),expected)
assert len({(g['map'],g['side'],g['seed'],g['opponent']) for g in games})==expected,'duplicate schedule cells'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
provenance=dict(cli=sha(ROOT/'tools/vendor/cambc.exe'), sdk={str(f.relative_to(ROOT)):sha(f) for f in sorted((ROOT/'sdk/cpp').rglob('*')) if f.is_file()},
                wasm={str(f.relative_to(out)):sha(f) for f in sorted((out/'build').glob('*.wasm'))},
                frozen_source={str(f.relative_to(out)):sha(f) for f in sorted((out/'build').rglob('*')) if f.is_file() and 'src' in f.relative_to(out/'build').parts},
                plan=sha(ROOT/a.plan),command=cmd,complete_games=expected)
identities=set();own_faults=opp_faults=own_fuel=opp_fuel=0
for g in games:
    n=json.loads((ROOT/g['folder']/'summary.json').read_text())
    identities.add((n['match']['engineVersion'],n['match']['engineBuildHash'],n['match']['metricSemanticsVersion']))
    team='team'+g['side'].upper();other='teamB' if team=='teamA' else 'teamA'
    own_faults+=n['diagnostics']['botFaults'][team];opp_faults+=n['diagnostics']['botFaults'][other]
    own_fuel+=g['fuel'];opp_fuel+=g['opp_fuel']
provenance.update(engines=sorted(identities),own_faults=own_faults,opponent_faults=opp_faults,
                  own_fuel_per_game=own_fuel/expected,opponent_fuel_per_game=opp_fuel/expected)
(out/'provenance.json').write_text(json.dumps(provenance,indent=1)+'\n')
assert len(identities)==1 and next(iter(identities))[0]=='2.0.0',identities
assert own_faults==opp_faults==0,(own_faults,opp_faults)
print(a.run,expected,'games',sum(g['win'] for g in games),'wins; margin',round(sum(g['margin'] for g in games)/expected,1),
      'fuel',round(own_fuel/expected,2),round(opp_fuel/expected,2),flush=True)
