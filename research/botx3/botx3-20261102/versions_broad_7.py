from pathlib import Path
import importlib.util,json
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'versions-broad-7';s.OPPS=['x1','x2','v86h','v92']
s.MAPS=[Path(p) for p in json.loads((BASE/'draft-paths-v3-regression/manifest.json').read_text())['maps']]+sorted((BASE/'draft-summary-final-maps').glob('*.map26a'))
s.ARMS={'off':[],'parent':s.PARENT,'botx3_1':[],'botx3_3':[],'plan_control':[],'botx3_7':[]}
frozen={'off':BASE/'draft-paths-v3/builds/off/bot.wasm','parent':BASE/'draft-paths-v3/builds/parent/bot.wasm','botx3_1':BASE/'versions-1-2/builds/botx3_1/bot.wasm','botx3_3':BASE/'versions-3/builds/botx3_3/bot.wasm','plan_control':BASE/'versions-7/builds/plan_control/bot.wasm','botx3_7':BASE/'versions-7/builds/botx3_7/bot.wasm'}
assert all(p.exists() for p in frozen.values())
s.build=lambda label,flags,trace=False:frozen[label]
s.write(s.OUT/'frozen-selection.json',dict(builds={k:s.dz.sha(v) for k,v in frozen.items()},scope='Broad existing/spent layouts, 46 maps; no protected-data claim'))
recent={}
for name in ['draft-paths-v3-regression','draft-paths-holdout','versions-1-2','versions-3','versions-5','versions-broad','versions-6','versions-broad-6','versions-7']:
 p=BASE/name/'rows.json'
 if (BASE/name/'summary.json').exists():
  for r in json.loads(p.read_text()):recent[(r['candidate_sha256'],r['opponent_sha256'],r['map_sha256'],r['side'])]=r
old=s.cached;s.cached=lambda c,o,m,side:recent.get((s.dz.sha(c),s.dz.sha(o),s.dz.sha(m),side)) or old(c,o,m,side)
s.main()
