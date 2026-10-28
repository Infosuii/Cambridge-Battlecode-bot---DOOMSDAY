"""One diagnostic game of a bot folder against v65 on a chosen map, side and seed.

Writes <out>/ours.txt (our team's stdout) and result.json. Does not touch any benchmark source.
"""
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
    ap.add_argument('--bot', required=True)
    ap.add_argument('--map', required=True)
    ap.add_argument('--side', choices='ab', default='a')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--opponent', default='bots/v65')
    ap.add_argument('--out', required=True)
    ap.add_argument('--define', action='append', default=[], metavar='NAME=VALUE')
    a = ap.parse_args()
    out = ROOT / a.out
    if not out.resolve().is_relative_to(ROOT / 'artifacts') or out.exists():
        raise SystemExit('fresh artifacts directory required')
    work = out / 'build'
    work.mkdir(parents=True)
    defines = dict(s.split('=', 1) for s in a.define)
    ours = build(ROOT / a.bot, a.seed, work, 'bot', defines)
    theirs = build(ROOT / a.opponent, a.seed, work, 'opp')
    A, B = (ours, theirs) if a.side == 'a' else (theirs, ours)
    result = engine.run_match(A, B, map_path(a.map), out / 'game', candidate_side=a.side.upper(), log_limit=64 << 20)
    (out / 'ours.txt').write_text(engine.team_stdout(out / 'game', a.side), encoding='utf8', newline='\n')
    (out / 'result.json').write_text(json.dumps(result.row(), indent=2), encoding='utf8', newline='\n')
    print(json.dumps(result.row()), flush=True)


if __name__ == '__main__':
    main()
