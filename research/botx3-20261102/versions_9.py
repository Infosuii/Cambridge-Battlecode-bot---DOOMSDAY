"""Version 3: retain restored features and repair their priority conflicts."""
from pathlib import Path
import importlib.util,json,shutil,ast,hashlib
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'versions-9';s.OPPS=['x1','x2','v86h','v92'];s.MAPS=list(s.MAPS)+sorted((BASE/'team-maps/dev').glob('*.map26a'))
f=json.loads((s.ROOT/'bots/botx3_9/features.json').read_text())['flags'];active=[k+'='+v for k,v in f.items()];control=[k+'='+('0' if k=='X3_SIEGE_ADMIT_USE' else v) for k,v in f.items()]
s.ARMS={'off':[],'parent':s.PARENT,'botx3_1':[],'botx3_2':[],'siege_control':control,'botx3_9':active}
original=s.build
def build(label,flags,trace=False):
 if label in ['botx3_1','botx3_2']:return BASE/'versions-1-2/builds'/label/'bot.wasm'
 if label!='botx3_9':return original(label,flags,trace)
 folder=s.OUT/'builds'/label
 if not folder.exists():shutil.copytree(s.ROOT/'bots'/label/'src',folder/'src')
 wasm=folder/'bot.wasm'
 if not wasm.exists():s.dz.build(folder,wasm)
 s.write(folder/'identity.json',dict(flags=flags,sha256=s.dz.sha(wasm),source={p.name:s.dz.sha(p) for p in (folder/'src').iterdir() if p.is_file()}));print('VERSION',label,s.dz.sha(wasm),flush=True);return wasm
s.build=build
t=ast.parse((BASE/'analyse.py').read_text(encoding='utf-8'));fn=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=='code_hash');ns={'hashlib':hashlib};exec(compile(ast.Module(body=[fn],type_ignores=[]),'hash','exec'),ns)
h={a:ns['code_hash'](build(a,s.ARMS[a])) for a in ['siege_control','botx3_9']};assert len(set(h.values()))==1;s.write(s.OUT/'same-code-proof.json',h)
recent={}
for r in json.loads((BASE/'versions-1-2/rows.json').read_text()):recent[(r['candidate_sha256'],r['opponent_sha256'],r['map_sha256'],r['side'])]=r
old=s.cached;s.cached=lambda c,o,m,side:recent.get((s.dz.sha(c),s.dz.sha(o),s.dz.sha(m),side)) or old(c,o,m,side)
s.main()
