from pathlib import Path
import importlib.util,zipfile,re
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'draft-paths-v3-diagnostics'
b=s.build('summary-v3-trace',['X3_DRAFT_PATHS=1','X3_DRAFT_USE=1'],trace=True)
for name,m in [('gold',s.ROOT/'maps/local-benchmarks/01gold-rush.map26a'),('perimeter',BASE/'team-unseen-maps/perimeter-banking-2.map26a')]:
 folder=s.OUT/name
 if not (folder/'candidate.stdout').exists():s.dz.match(b,BASE/'team-contract/opponents/x2.wasm',m,'A',folder,True,500)
 t=(folder/'candidate.stdout').read_text();records=[l for l in t.splitlines() if l.startswith('X3_')]
 assert 'X3_PATHS_DRAFT' in t and 'X3_PATHS_READ' in t and 'bot error:' not in t,(name,records[:10])
 assert 'X3_MAP_VERIFY' in t and not re.search(r'mismatch[1-9]',t),(name,records[-10:])
 s.write(s.OUT/(name+'.json'),dict(scope='Instrumented native activation only',records=records,hits=t.count('X3_PATHS_HIT'),reads=t.count('X3_PATHS_READ')))
 print(name,records[:4],'hits',t.count('X3_PATHS_HIT'),flush=True)
