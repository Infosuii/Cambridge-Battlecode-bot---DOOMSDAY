from pathlib import Path
import importlib.util,json,re
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'versions-2-diagnostics'
f=json.loads((BASE/'restored-features.json').read_text());flags=[k+'='+v for k,v in dict(f['core'],**f['restored'],**f['planning']).items()]+['APEX_MODESTATS=1']
b=s.build('full-trace',flags,trace=True)
for name,m in [('gold',s.ROOT/'maps/local-benchmarks/01gold-rush.map26a'),('grid',BASE/'team-maps/dev/open-grid-0.map26a')]:
 folder=s.OUT/name
 if not (folder/'candidate.stdout').exists():s.dz.match(b,BASE/'team-contract/opponents/x2.wasm',m,'A',folder,True,650)
 t=(folder/'candidate.stdout').read_text();r=[l for l in t.splitlines() if l.startswith(('X3_','modes','MODE','MS '))]
 assert 'X3_CONFIG' in t and 'X3_PATHS_READ' in t and 'bot error:' not in t,(name,r[:10])
 s.write(s.OUT/(name+'.json'),dict(scope='Instrumented full version activation; not strength evidence',records=r))
 print(name,'configs',t.count('X3_CONFIG'),'summary reads',t.count('X3_PATHS_READ'),'orders',t.count('X3_ORDER'),'bank orders',t.count('X3_RACE'),flush=True)
