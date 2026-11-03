from pathlib import Path
import importlib.util,zipfile,re
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'resume-bank-diagnostics'
b=s.build('bank14-trace',['X3_TEAM=14','X3_TEAM_FARM=0','X3_TEAM_RACE=1'],trace=True)
for name,side in [('gated-stripes-0','B'),('open-grid-3','A')]:
 folder=s.OUT/name
 if not (folder/'summary.json').exists():s.dz.match(b,BASE/'team-contract/opponents/v92.wasm',BASE/'team-maps/dev'/(name+'.map26a'),side,folder)
 with zipfile.ZipFile(next(folder.glob('*.repl26a'))) as z:
  t=z.read('team-'+side.lower()+'.stdout').replace(b'\0',b'').decode('utf-8','replace')
 records=[l for l in t.splitlines() if l.startswith('X3_')]
 s.write(s.OUT/(name+'.json'),dict(scope='Instrumented native activation; not strength evidence',race_orders=t.count('X3_RACE'),records=records))
 print(name,'banking orders',t.count('X3_RACE'),flush=True)
