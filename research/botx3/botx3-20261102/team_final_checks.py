from pathlib import Path
import importlib.util,json
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'team-work'
off=s.build('current-source-off',[])
assert s.dz.sha(off)=='1746f2bb7fa341530f41bd8c8c4896b35172783f35eacee8e4a4b6ac0ceea183'
current=s.build('current-source-team8',['X3_TEAM=8'])
frozen=BASE/'team-tail/builds/team_after_fields/bot.wasm'
assert s.dz.sha(current)==s.dz.sha(frozen),'Current source differs from frozen tested candidate'
bot=s.build('team8-trace',['X3_TEAM=8'],trace=True)
target=s.OUT/'diagnostics/team8-trace'
if not (target/'receipt.json').exists():
    s.dz.match(bot,s.OUT/'opponents/v92.wasm',s.ROOT/'maps/local-benchmarks/01gold-rush.map26a','A',target,True,550)
text=(target/'candidate.stdout').read_text()
assert 'X3_ORDER ' in text and 'X3_APPLY ' in text and 'bot error:' not in text
result=dict(off_sha256=s.dz.sha(off),current_sha256=s.dz.sha(current),
    frozen_sha256=s.dz.sha(frozen),orders=text.count('X3_ORDER '),executor_reads=text.count('X3_APPLY '))
(s.OUT/'final-source-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
