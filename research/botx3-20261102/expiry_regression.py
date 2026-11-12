"""Broader check of the existing plan-expiry repair, not more auction tuning."""
from pathlib import Path
import importlib.util,json,ast,hashlib
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'expiry-regression';s.OPPS=['x1','x2','v86h','v92']
# Exact prior regression-map bytes; do not depend on changing directory order.
manifest=json.loads((BASE/'team-bank-regression/manifest.json').read_text())
s.MAPS=[Path(p) for p in manifest['maps']]
s.ARMS={'off':[],'parent':s.PARENT,'never':s.PARENT+['X3_PLAN_END=5000'],'expiry':s.PARENT+['X3_PLAN_END=500']}
t=ast.parse((BASE/'analyse.py').read_text(encoding='utf-8'));f=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=='code_hash');ns={'hashlib':hashlib};exec(compile(ast.Module(body=[f],type_ignores=[]),'hash','exec'),ns)
h={a:ns['code_hash'](s.build(a,s.ARMS[a])) for a in ['never','expiry']};assert len(set(h.values()))==1;s.write(s.OUT/'same-code-proof.json',h)
recent={}
for name in ['team-work','team-tail','team-unseen','team-robust','team-contract','team-bank-regression']:
 p=BASE/name/'rows.json'
 if p.exists():
  for r in json.loads(p.read_text()):recent[(r['candidate_sha256'],r['opponent_sha256'],r['map_sha256'],r['side'])]=r
old=s.cached
def cached(c,o,m,side):
 r=recent.get((s.dz.sha(c),s.dz.sha(o),s.dz.sha(m),side))
 return dict(r,reused_from='prior frozen local matrix') if r else old(c,o,m,side)
s.cached=cached;s.main()
