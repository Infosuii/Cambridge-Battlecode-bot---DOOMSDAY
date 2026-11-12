"""Download summaries and replays of one ladder-duel arm (read-only), for the timeline forensics.

Usage: python research/v75/collect_duel.py ARM [--plan research/v59/duel_top1.json]
Output: artifacts/local-only/duel-<ARM>/<matchId>/{summary.json,replay.repl26a}, index research/v75/duel_<ARM>.json
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/replay'))
sys.path.insert(0, str(ROOT / 'research/v75'))
from ladder_duel import finished_groups  # noqa: E402
from collect_v67 import call  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('arm')
    ap.add_argument('--plan', default='research/v59/duel_top1.json')
    a = ap.parse_args()
    plan = json.loads((ROOT / a.plan).read_text(encoding='utf8'))
    info = plan['arms'][a.arm]
    by = finished_groups({g for g in info['groups'] if g}, info['since'])
    raw = ROOT / f'artifacts/local-only/duel-{a.arm}'
    rows = []
    for i, gid in enumerate(info['groups']):
        for m in by.get(gid, []):
            if m['status'] != 'finished':
                continue
            me = next(t for t in m['teams'] if t['name'] == 'DOOMSDAY')
            dest = raw / m['matchId']
            dest.mkdir(parents=True, exist_ok=True)
            if not (dest / 'summary.json').exists():
                call(['matches', 'summary', m['matchId'], '--json', '--output', str(dest / 'summary.json')])
            if not (dest / 'replay.repl26a').exists():
                call(['matches', 'download', m['matchId'], '--output', str(dest / 'replay.repl26a')])
            rows.append(dict(matchId=m['matchId'], map=m['map'], side=me['side'], result=me['result'],
                             opponent=plan['groups'][i]['opponent'], summary=(dest / 'summary.json').relative_to(ROOT).as_posix()))
    (ROOT / f'research/v75/duel_{a.arm}.json').write_text(json.dumps(rows, indent=1, ensure_ascii=False) + '\n', encoding='utf8')
    print(len(rows), 'games;', sum(r['result'] == 'win' for r in rows), 'wins')


if __name__ == '__main__':
    main()
