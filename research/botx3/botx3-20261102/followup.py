"""Focused bank-planner repair and missing BP attribution control."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('screen',Path(__file__).with_name('screen.py'))
screen=importlib.util.module_from_spec(spec);spec.loader.exec_module(screen)
screen.ARMS.update(bp=screen.BP, planner_control=['APEX_PLAN=1'],
                   planner_repair=['APEX_PLAN=1','X3_BANKCYCLE=2'])
screen.main()
