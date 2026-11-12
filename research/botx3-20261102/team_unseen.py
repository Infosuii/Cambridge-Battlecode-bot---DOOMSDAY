"""Once-only unseen resource-layout evaluation; no tuning follows this suite."""
from pathlib import Path
import importlib.util,json
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'team-unseen'
s.MAPS=sorted((BASE/'team-unseen-maps').glob('*.map26a'))
s.OPPS=['x1','x2','v86h','v92']
s.ARMS={'off':[],'parent':s.PARENT,'team_guarded':['X3_TEAM=5'],'team_after_fields':['X3_TEAM=8']}
frozen={a:BASE/('team-transfer' if a=='team_guarded' else 'team-tail')/'builds'/a/'bot.wasm' for a in s.ARMS}
selection=dict(primary='team_after_fields',secondary='team_guarded',
    rule='Primary improves the 224-cell development/regression pool against three opponents and ties the fourth; fuel remains unresolved. Secondary is the earlier frozen controller. Neither may be retuned using this suite.',
    binaries={a:s.dz.sha(p) for a,p in frozen.items()},maps={p.name:s.dz.sha(p) for p in s.MAPS},
    resource_manifest=s.dz.sha(BASE/'team-unseen-maps/manifest.json'))
p=BASE/'team-unseen-maps/selection.json'
if p.exists():assert json.loads(p.read_text())==selection
else:p.write_text(json.dumps(selection,indent=2)+'\n')
def build(label,flags,trace=False):
    path=frozen[label];assert s.dz.sha(path)==selection['binaries'][label];return path
s.build=build;s.main()
