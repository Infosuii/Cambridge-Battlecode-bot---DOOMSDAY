"""Broaden the banking repair on spent regression maps; no protected-data claim."""
from pathlib import Path
import importlib.util,json
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'team-bank-regression'
s.OPPS=['x1','x2','v86h','v92']
s.MAPS=sorted((s.ROOT/'maps/local-benchmarks').glob('*.map26a'))[::6]
s.MAPS+=sorted((s.ROOT/'maps/x1-unseen').glob('*.map26a'))[::12][:4]
s.MAPS+=sorted((s.ROOT/'maps/x1-maze').glob('*.map26a'))[::7][:4]
s.MAPS+=sorted((BASE/'team-unseen-maps').rglob('*.map26a'))
s.ARMS={'off':[],'parent':s.PARENT,'transport':['X3_TEAM=14','X3_TEAM_FARM=0','X3_TEAM_RACE=0'],'bank':['X3_TEAM=14','X3_TEAM_FARM=0','X3_TEAM_RACE=1']}
frozen={k:BASE/'team-fieldready/builds'/k/'bot.wasm' for k in s.ARMS}
s.build=lambda label,flags,trace=False:frozen[label]
recent={}
for name in ['team-work','team-tail','team-unseen','team-robust','team-contract','team-commitments','team-fieldready']:
 p=BASE/name/'rows.json'
 if p.exists():
  for row in json.loads(p.read_text()):recent[(row['candidate_sha256'],row['opponent_sha256'],row['map_sha256'],row['side'])]=row
old=s.cached
def cached(c,o,m,side):
 r=recent.get((s.dz.sha(c),s.dz.sha(o),s.dz.sha(m),side))
 return dict(r,reused_from='prior frozen local matrix') if r else old(c,o,m,side)
s.cached=cached;s.main()
