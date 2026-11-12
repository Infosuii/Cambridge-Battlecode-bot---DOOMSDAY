"""Frozen combined draft-summary candidate, broad regression transfer."""
from pathlib import Path
import importlib.util,json
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'draft-paths-regression';s.OPPS=['x1','x2','v86h','v92']
s.MAPS=[Path(p) for p in json.loads((BASE/'team-bank-regression/manifest.json').read_text())['maps']]
s.MAPS+=sorted((BASE/'bank-holdout-maps').glob('*.map26a'))
s.ARMS={'off':[],'parent':s.PARENT,'control':['X3_DRAFT_PATHS=1','X3_DRAFT_USE=0'],'precompute':['X3_DRAFT_PATHS=1','X3_DRAFT_USE=1']}
frozen={k:BASE/'draft-paths-v2/builds'/k/'bot.wasm' for k in s.ARMS}
s.build=lambda label,flags,trace=False:frozen[label]
s.write(s.OUT/'frozen-selection.json',dict(builds={k:s.dz.sha(v) for k,v in frozen.items()},reason='Predeclared complete-summary interaction; no tuning on this broad matrix'))
recent={}
for name in ['team-bank-regression','team-bank-holdout','draft-paths-v2']:
 for r in json.loads((BASE/name/'rows.json').read_text()):recent[(r['candidate_sha256'],r['opponent_sha256'],r['map_sha256'],r['side'])]=r
old=s.cached;s.cached=lambda c,o,m,side:recent.get((s.dz.sha(c),s.dz.sha(o),s.dz.sha(m),side)) or old(c,o,m,side)
s.main()
