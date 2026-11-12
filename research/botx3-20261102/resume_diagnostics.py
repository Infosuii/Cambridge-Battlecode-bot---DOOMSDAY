from pathlib import Path
import importlib.util,json,re,sys
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
version=int(sys.argv[1]) if len(sys.argv)>1 else 12
s.OUT=BASE/('resume-audit' if version==12 else f'resume-audit-{version}')
b=s.build(f'contract{version}-trace',[f'X3_TEAM={version}','X3_TEAM_FARM=1','X3_TEAM_RACE=0'],trace=True)
for name,m in [('gold',s.ROOT/'maps/local-benchmarks/01gold-rush.map26a'),('grid',BASE/'team-maps/dev/open-grid-0.map26a')]:
 if not m.exists():m=next((BASE/'team-maps/dev').glob('open-grid*.map26a'))
 folder=s.OUT/name
 if not (folder/'candidate.stdout').exists():s.dz.match(b,BASE/'team-contract/opponents/x2.wasm',m,'A',folder,True,600)
 t=(folder/'candidate.stdout').read_text()
 records=[l for l in t.splitlines() if l.startswith('X3_')]
 accepts=re.findall(r'X3_CONTRACT[^\n]*accepted(\d+)',t)
 s.write(s.OUT/(name+'.json'),dict(orders=t.count('X3_ORDER '),contracts=len(accepts),accepted=accepts.count('1'),refused=accepts.count('0'),records=records))
 print(name,'orders',t.count('X3_ORDER '),'contracts',len(accepts),'accepted',accepts.count('1'),'refused',accepts.count('0'),flush=True)
