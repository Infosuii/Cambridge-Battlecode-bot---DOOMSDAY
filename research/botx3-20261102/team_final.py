"""Once-only family-held-out evaluation of frozen development-selected builds."""
from pathlib import Path
import importlib.util,json,hashlib
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
development=json.loads((BASE/'team-transfer/summary.json').read_text())
assert development['team_guarded']['wins']>=development['off']['wins']
assert development['team_guarded']['fuel']<=development['off']['fuel']
s.OUT=BASE/'team-final'
s.MAPS=sorted((BASE/'team-maps/final').glob('*.map26a'))
s.ARMS={'off':[],'parent':s.PARENT,'team_guarded':['X3_TEAM=5'],'transport_control':['X3_TEAM=6']}
frozen={label:BASE/'team-transfer/builds'/label/'bot.wasm' for label in s.ARMS}
selection=dict(rule='One positive team scheduler on development families; freeze before final results; no final-driven retuning.',
               builds={label:s.dz.sha(p) for label,p in frozen.items()},
               maps={p.name:s.dz.sha(p) for p in s.MAPS},maps_manifest_sha256=s.dz.sha(BASE/'team-maps/manifest.json'))
dest=BASE/'team-maps/final-selection.json'
if dest.exists():assert json.loads(dest.read_text())==selection
else:dest.write_text(json.dumps(selection,indent=2)+'\n')
def build(label,flags,trace=False):
    p=frozen[label];assert s.dz.sha(p)==selection['builds'][label];return p
s.build=build
s.main()
