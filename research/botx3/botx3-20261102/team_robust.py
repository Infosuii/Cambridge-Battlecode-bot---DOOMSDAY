"""Broader regression coverage for the frozen planner; no candidate retuning."""
from pathlib import Path
import importlib.util,json
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'team-robust'
s.OPPS=['x1','x2','v86h','v92']
s.MAPS=sorted((s.ROOT/'maps/local-benchmarks').glob('*.map26a'))[::6]
s.MAPS+=sorted((s.ROOT/'maps/x1-unseen').glob('*.map26a'))[::12][:4]
s.MAPS+=sorted((s.ROOT/'maps/x1-maze').glob('*.map26a'))[::7][:4]
s.ARMS={'off':[],'parent':s.PARENT,'team_guarded':['X3_TEAM=5']}
frozen={label:BASE/'team-transfer/builds'/label/'bot.wasm' for label in s.ARMS}
selection=json.loads((BASE/'team-maps/final-selection.json').read_text())
def build(label,flags,trace=False):
    p=frozen[label];assert s.dz.sha(p)==selection['builds'][label];return p
s.build=build
# Reuse exact recent reference cells too, rather than repeat them across suites.
recent={}
for name in ['initial-campaign','team-work','team-transfer']:
    for row in json.loads((BASE/name/'rows.json').read_text()):
        recent[(row['candidate_sha256'],row['opponent_sha256'],row['map_sha256'],row['side'])]=row
old_cached=s.cached
def cached(c,o,m,side):
    row=recent.get((s.dz.sha(c),s.dz.sha(o),s.dz.sha(m),side))
    return dict(row,reused_from='prior frozen local matrix') if row else old_cached(c,o,m,side)
s.cached=cached
s.main()
