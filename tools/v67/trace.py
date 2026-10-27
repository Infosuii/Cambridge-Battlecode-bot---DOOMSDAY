"""One diagnostic game; does not alter the v67 sources or the fixed benchmark."""
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
    ap.add_argument('--out', required=True)
    ap.add_argument('--define', action='append', default=[], metavar='NAME=VALUE')
    a = ap.parse_args()
    out = ROOT / a.out
    if not out.resolve().is_relative_to(ROOT / 'artifacts') or out.exists():
        raise SystemExit('fresh artifacts directory required')
    work = out / 'build'
    work.mkdir(parents=True)
    defines = dict(setting.split('=', 1) for setting in a.define)
    defines['V67_TRACE'] = 1
    ours = build(ROOT / 'bots/v67', 1, work, 'bot', defines)
    opponent = build(ROOT / 'bots/v65', 1, work, 'opponent')
    result = engine.run_match(ours, opponent, map_path(a.map), out / 'game', log_limit=64 << 20)
    (out / 'a.txt').write_text(engine.team_stdout(out / 'game', 'a'), encoding='utf8', newline='\n')
    (out / 'result.json').write_text(json.dumps(result.row(), indent=2), encoding='utf8', newline='\n')
    print(json.dumps(result.row()), flush=True)


if __name__ == '__main__':
    main()
