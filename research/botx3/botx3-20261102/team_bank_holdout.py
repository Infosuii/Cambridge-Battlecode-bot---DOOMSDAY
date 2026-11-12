"""Once-only banking transfer check. No changes after observing these games."""
from pathlib import Path
import importlib.util,json
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'team-bank-holdout';s.OPPS=['x1','x2','v86h','v92']
s.MAPS=sorted((BASE/'bank-holdout-maps').glob('*.map26a'));assert len(s.MAPS)==12
s.ARMS={'off':[],'parent':s.PARENT,'transport':['X3_TEAM=14','X3_TEAM_FARM=0','X3_TEAM_RACE=0'],'bank':['X3_TEAM=14','X3_TEAM_FARM=0','X3_TEAM_RACE=1']}
frozen={k:BASE/'team-fieldready/builds'/k/'bot.wasm' for k in s.ARMS}
for label in ['off','bank']:
 current=s.build('current-'+label,s.ARMS[label]);assert s.dz.sha(current)==s.dz.sha(frozen[label]),'Current-source binary differs from frozen selection'
s.write(s.OUT/'frozen-selection.json',dict(status='Frozen before any holdout candidate matches',builds={k:s.dz.sha(v) for k,v in frozen.items()},map_manifest=s.dz.sha(BASE/'bank-holdout-maps/manifest.json')))
s.build=lambda label,flags,trace=False:frozen[label]
s.main()
