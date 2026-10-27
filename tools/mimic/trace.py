"""Build a trace-enabled mimic and run one reproducible local diagnostic game."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'python'))
sys.path.insert(0, str(ROOT / 'tools/proxy'))
from nfs import engine
from local_duel import build, map_path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--map', default='00quadrants')
    ap.add_argument('--opponent', default='bots/v65')
    ap.add_argument('--team', type=int, default=-1)
    ap.add_argument('--fuel', action='store_true', help='fuel probes instead of decision traces')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    if not out.is_relative_to(ROOT / 'artifacts') or out.exists():
        raise SystemExit('fresh output directory inside artifacts/ required')
    work = out / 'build'
    work.mkdir(parents=True)
    ours = build(ROOT / 'bots/mimic', 1, work, 'mimic',
                 {'MIMIC_TRACE': int(not a.fuel), 'MIMIC_FUEL': int(a.fuel), 'MIMIC_TEAM': a.team})
    theirs = build(ROOT / a.opponent, 1, work, 'opponent')
    result = engine.run_match(ours, theirs, map_path(a.map), out / 'game', log_limit=64 << 20)
    for side in ('a', 'b'):
        (out / f'{side}.txt').write_text(engine.team_stdout(out / 'game', side), encoding='utf8', newline='\n')
    (out / 'result.json').write_text(json.dumps(result.row(), indent=2) + '\n', encoding='utf8', newline='\n')
    print(json.dumps(result.row()), flush=True)


if __name__ == '__main__':
    main()
