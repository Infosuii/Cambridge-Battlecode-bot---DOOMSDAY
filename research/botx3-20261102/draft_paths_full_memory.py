"""Draft-budget precomputation: matched executable controls, actual route use."""
from pathlib import Path
import importlib.util,json,ast,hashlib,zipfile
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'draft-paths-v3';s.OPPS=['x1','x2','v86h','v92']
s.MAPS=list(s.MAPS)+sorted((BASE/'team-maps/dev').glob('*.map26a'))
s.ARMS={'off':[],'parent':s.PARENT,'control':['X3_DRAFT_PATHS=1','X3_DRAFT_USE=0'],'precompute':['X3_DRAFT_PATHS=1','X3_DRAFT_USE=1']}
t=ast.parse((BASE/'analyse.py').read_text(encoding='utf-8'));f=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=='code_hash');ns={'hashlib':hashlib};exec(compile(ast.Module(body=[f],type_ignores=[]),'hash','exec'),ns)
h={a:ns['code_hash'](s.build(a,s.ARMS[a])) for a in ['control','precompute']};assert len(set(h.values()))==1;s.write(s.OUT/'same-code-proof.json',h)
recent={}
for name in ['team-contract','team-fieldready']:
 for r in json.loads((BASE/name/'rows.json').read_text()):recent[(r['candidate_sha256'],r['opponent_sha256'],r['map_sha256'],r['side'])]=r
old=s.cached
s.cached=lambda c,o,m,side:recent.get((s.dz.sha(c),s.dz.sha(o),s.dz.sha(m),side)) or old(c,o,m,side)
s.main()
