from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location('screen',Path(__file__).with_name('screen.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.OUT=Path(__file__).resolve().parent/'team-work'
s.ARMS={'off':[],'parent':s.PARENT,'team_v2':['X3_TEAM=1'],'team_bounded':['X3_TEAM=3']}
s.main()
