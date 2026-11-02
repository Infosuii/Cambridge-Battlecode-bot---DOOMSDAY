"""Fix code/layout control before interpreting the banking factorial."""
from pathlib import Path
import importlib.util,json,ast,hashlib
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'team-bank-controlled'
s.MAPS=list(s.MAPS)+sorted((BASE/'team-maps/dev').glob('*.map26a'))
s.OPPS=['x1','x2','v86h','v92']
s.ARMS={'off':[],'parent':s.PARENT,
    'transport':['X3_TEAM=9','X3_TEAM_FARM=0','X3_TEAM_RACE=0'],
    'farm':['X3_TEAM=9','X3_TEAM_FARM=1','X3_TEAM_RACE=0'],
    'bank':['X3_TEAM=9','X3_TEAM_FARM=0','X3_TEAM_RACE=1'],
    'joint':['X3_TEAM=9','X3_TEAM_FARM=1','X3_TEAM_RACE=1']}
t=ast.parse((BASE/'analyse.py').read_text(encoding='utf-8'))
f=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=='code_hash')
ns={'hashlib':hashlib};exec(compile(ast.Module(body=[f],type_ignores=[]),'code_hash','exec'),ns)
hashes={a:ns['code_hash'](s.build(a,flags)) for a,flags in s.ARMS.items() if a not in ['off','parent']}
assert len(set(hashes.values()))==1,hashes
s.write(s.OUT/'same-code-proof.json',hashes)
recent={}
for name in ['initial-campaign','team-work','team-tail','team-bank']:
    for row in json.loads((BASE/name/'rows.json').read_text()):
        recent[(row['candidate_sha256'],row['opponent_sha256'],row['map_sha256'],row['side'])]=row
old_cached=s.cached
def cached(c,o,m,side):
    row=recent.get((s.dz.sha(c),s.dz.sha(o),s.dz.sha(m),side))
    return dict(row,reused_from='prior frozen local matrix') if row else old_cached(c,o,m,side)
s.cached=cached;s.main()
