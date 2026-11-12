"""Final fuel repair: leave the established field-building quota ahead of optional scheduling."""
from pathlib import Path
import importlib.util,json
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('screen',BASE/'screen.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=BASE/'team-tail'
prior=json.loads((s.OUT/'manifest.json').read_text())
s.MAPS=[Path(p) for p in prior['maps']]
s.OPPS=['x1','x2','v86h','v92']
s.ARMS={'off':[],'parent':s.PARENT,'team_tail':['X3_TEAM=7'],'team_after_fields':['X3_TEAM=8']}
s.main()
