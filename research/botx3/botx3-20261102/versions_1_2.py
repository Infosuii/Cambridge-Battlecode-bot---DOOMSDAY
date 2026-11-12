"""Build actual new bot versions; compare restored feature groups and combination."""
from pathlib import Path
import importlib.util,json,shutil
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'versions-1-2';s.OPPS=['x1','x2','v86h','v92'];s.MAPS=list(s.MAPS)+sorted((BASE/'team-maps/dev').glob('*.map26a'))
f=json.loads((BASE/'restored-features.json').read_text());flags=lambda x:[k+'='+v for k,v in x.items()]
s.ARMS={'off':[],'parent':s.PARENT,'botx3_1':flags(f['core']),'corrections':flags(dict(f['core'],**f['restored'])),'planners':flags(dict(f['core'],**f['planning'])),'botx3_2':flags(dict(f['core'],**f['restored'],**f['planning']))}
original=s.build
def build(label,flags,trace=False):
 if label not in ['botx3_1','botx3_2']:return original(label,flags,trace)
 folder=s.OUT/'builds'/label
 if not folder.exists():shutil.copytree(s.ROOT/'bots'/label/'src',folder/'src')
 wasm=folder/'bot.wasm'
 if not wasm.exists():s.dz.build(folder,wasm)
 s.write(folder/'identity.json',dict(flags=flags,sha256=s.dz.sha(wasm),source={p.name:s.dz.sha(p) for p in (folder/'src').iterdir() if p.is_file()}))
 if label=='botx3_1':assert s.dz.sha(wasm)=='c7210bb65cf1fa528906e419dff9269527d3d50e1aad41e5924aad44ece35b1e'
 print('VERSION',label,s.dz.sha(wasm),flush=True);return wasm
s.build=build
recent={}
for name in ['team-contract','draft-paths-v3','draft-paths-v3-regression','draft-paths-holdout']:
 for r in json.loads((BASE/name/'rows.json').read_text()):recent[(r['candidate_sha256'],r['opponent_sha256'],r['map_sha256'],r['side'])]=r
old=s.cached;s.cached=lambda c,o,m,side:recent.get((s.dz.sha(c),s.dz.sha(o),s.dz.sha(m),side)) or old(c,o,m,side)
s.main()
