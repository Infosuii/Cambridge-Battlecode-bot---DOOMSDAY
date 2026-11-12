"""Once-only frozen larger-summary validation on two new layout families."""
from pathlib import Path
import importlib.util
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'draft-paths-holdout';s.OPPS=['x1','x2','v86h','v92']
s.MAPS=sorted((BASE/'draft-summary-final-maps').glob('*.map26a'));assert len(s.MAPS)==8
s.ARMS={'off':[],'parent':s.PARENT,'control':['X3_DRAFT_PATHS=1','X3_DRAFT_USE=0'],'precompute':['X3_DRAFT_PATHS=1','X3_DRAFT_USE=1']}
frozen={k:BASE/'draft-paths-v3/builds'/k/'bot.wasm' for k in s.ARMS}
s.write(s.OUT/'frozen-selection.json',dict(builds={k:s.dz.sha(v) for k,v in frozen.items()},map_manifest=s.dz.sha(BASE/'draft-summary-final-maps/manifest.json'),reason='Larger compatible payload selected for coverage; no tuning on these layouts or outcomes. One candidate and its proper control.'))
s.build=lambda label,flags,trace=False:frozen[label]
s.main()
