"""Inherited phase/stage fuel profiler routed to this branch's evidence directory."""
import importlib.util
from pathlib import Path
import run as bridge
REPO=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('resume_fuelbench', REPO/'tools/jd_g5070-1104/fuelbench.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
f.jdrun=bridge.runner;f.RESEARCH=REPO/'research/jd-g5070-resume-0715'
if __name__=='__main__': f.main()
