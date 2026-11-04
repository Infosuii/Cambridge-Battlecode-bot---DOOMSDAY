"""Resume runner: retain immutable frozen artifacts and locked data partitions."""
import importlib.util
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
os.environ.setdefault('JD_EVAL', r'C:\projects\cambridge battlecode\battlecode part 2\jd-eval')
spec = importlib.util.spec_from_file_location('jd_original', REPO / 'tools/jd_g5070-1104/jdrun.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
runner.RESEARCH = REPO / 'research/jd-g5070-resume-0715'
runner.AGENT = 'builder-g5070-1104'
runner.SESSION = 'builder-g5070-resume-0715-20261104-0715'
# No integration/evaluation is published under an expired epoch.
runner.TASK_EPOCHS = {'resume-evidence': 1, 'candidate-integration': 3, 'fuel-memory-runtime': 3, 'basic-decision-strategy': 3, 'rl-actor-export': 3}
if __name__ == '__main__':
    runner.main()
