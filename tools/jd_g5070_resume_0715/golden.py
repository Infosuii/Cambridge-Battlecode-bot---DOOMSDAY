"""Run inherited golden fixtures against a precise export in an isolated source snapshot."""
import os
from pathlib import Path
ORIGINAL=Path(r'C:\projects\cambridge battlecode\battlecode part 2\doomsday\tools\jd_g5070-1104\nn_golden.py')
s=ORIGINAL.read_text(encoding='utf8')
s=s.replace('SRC = os.path.join(WT, "bots", "jd-g5070-1104", "src")', 'SRC = os.environ["JD_GOLD_SRC"]')
s=s.replace('{x:.7e}', '{x:.9e}').replace('CKPT_REL_TOL = 5e-3','CKPT_REL_TOL = 1e-4')
exec(compile(s,str(ORIGINAL),'exec'),{'__file__':str(ORIGINAL),'__name__':'__main__'})
