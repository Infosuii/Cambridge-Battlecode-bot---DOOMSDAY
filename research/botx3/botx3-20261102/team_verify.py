"""Verify draft transfer, explicit shared orders and metered tail cost."""
from pathlib import Path
import importlib.util,json,re,zipfile
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'team-work'
bot=s.build('team-guarded-trace',['X3_TEAM=5'],trace=True)
target=s.OUT/'diagnostics/team-guarded-trace'
if not (target/'receipt.json').exists():
    s.dz.match(bot,s.OUT/'opponents/v92.wasm',s.ROOT/'maps/local-benchmarks/01gold-rush.map26a','A',target,True,550)
stdout=(target/'candidate.stdout').read_text()
records=[x for x in stdout.splitlines() if x.startswith('X3_')]
assert 'X3_DRAFT groups' in stdout and 'X3_ORDER ' in stdout and 'X3_APPLY ' in stdout
assert 'bot error:' not in stdout
fuel=[int(x) for x in re.findall(r'X3_TEAM[^\n]*fuel(\d+)',stdout)]
result=dict(records=len(records),orders=stdout.count('X3_ORDER '),executor_reads=stdout.count('X3_APPLY '),
            draft_reads=stdout.count('X3_DRAFT_READ '),planner_fuel_max=max(fuel,default=0),
            planner_fuel_mean=sum(fuel)/max(1,len(fuel)))
(target/'trace.json').write_text(json.dumps(dict(summary=result,records=records),indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
# Native failed-game replays: economic throughput and deaths, not just final wins.
folder=s.OUT/'replay-audit';folder.mkdir(exist_ok=True)
for arm in ['off','team_v2','team_bounded','team_coordinator']:
    game=s.OUT/'games'/arm/'v92/00rows-A'
    if not list(game.glob('*.repl26a')):continue
    bundle=next(game.glob('*.repl26a'))
    with zipfile.ZipFile(bundle) as z:(folder/(arm+'.repl26a')).write_bytes(z.read('replay.repl26a'))
