from pathlib import Path
import importlib.util,json
spec=importlib.util.spec_from_file_location('screen',Path(__file__).with_name('screen.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=Path(__file__).resolve().parent/'team-work'
bot=s.build('team-draft-trace',['X3_TEAM=2'],trace=True)
target=s.OUT/'diagnostics/team-draft-trace'
s.dz.match(bot,s.OUT/'opponents/v92.wasm',s.ROOT/'maps/local-benchmarks/01gold-rush.map26a','A',target,True,550)
lines=[x for x in (target/'candidate.stdout').read_text().splitlines() if x.startswith('X3_') or 'error:' in x]
(target/'trace.json').write_text(json.dumps(lines,indent=2)+'\n')
print('\n'.join(lines[:15]),'\n...\n','\n'.join(lines[-10:]),flush=True)
