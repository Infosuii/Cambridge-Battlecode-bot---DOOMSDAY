"""Same-code never-expire control after pre-expiry checkpoint divergence."""
from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location('screen',Path(__file__).with_name('screen.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.ARMS.update(bp=s.BP,planner_control=['APEX_PLAN=1'],planner_repair=['APEX_PLAN=1','X3_BANKCYCLE=2'],
              planner_budget_v3=['APEX_PLAN=1','X3_BANKCYCLE=3'],end5000=s.PARENT+['X3_PLAN_END=5000'])
s.main()
