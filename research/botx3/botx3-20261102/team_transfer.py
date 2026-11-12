"""New development families. No final-family access in this runner."""
from pathlib import Path
import importlib.util,json
spec=importlib.util.spec_from_file_location('screen',Path(__file__).with_name('screen.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
BASE=Path(__file__).resolve().parent
s.OUT=BASE/'team-transfer'
s.MAPS=sorted((BASE/'team-maps/dev').glob('*.map26a'))
s.ARMS={'off':[],'parent':s.PARENT,'team_guarded':['X3_TEAM=5'],'transport_control':['X3_TEAM=6']}
s.main()
