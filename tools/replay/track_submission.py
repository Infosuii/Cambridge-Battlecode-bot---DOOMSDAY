"""Track our ranked results since a submission time (cambc matches list), with focus maps reported separately.

    python tools/replay/track_submission.py --since 2026-10-25T11:40:00Z [--maps 01big_world 01islands] [--team DOOMSDAY]
           [--baseline <recent_ranked.json>] [--out <report.json>]

Read-only: lists matches with the logged-in CLI session. With --baseline, the same maps' results before the submission
are shown for comparison.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]


def fetch(cli, since, limit_pages=10):
    out, cursor = [], None
    for _ in range(limit_pages):
        args = [cli, 'matches', 'list', '--team', 'me', '--kind', 'ranked', '--limit', '100', '--json'] + (['--cursor', cursor] if cursor else [])
        for _attempt in range(4):
            p = subprocess.run(args, capture_output=True, timeout=120)
            if p.stdout.strip():
                break
            time.sleep(5)
        d = json.loads(p.stdout.decode('utf-8'))
        out += d['matches']
        cursor = d.get('nextCursor')
        if not cursor or (out and out[-1]['createdAt'] < since):
            break
    return [m for m in out if m['createdAt'] >= since and m['status'] == 'finished']


def record(matches, team, maps=None):
    rows = []
    for m in matches:
        if maps is not None and m['map'] not in maps:
            continue
        me = next((t for t in m['teams'] if t['name'].lower() == team.lower()), None)
        if me:
            rows.append(me['result'] == 'win')
    return f'{sum(rows)}/{len(rows)}' + (f' ({sum(rows) / len(rows):.0%})' if rows else '')


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--since', required=True); p.add_argument('--maps', nargs='+', default=['01big_world', '01islands'])
    p.add_argument('--team', default='DOOMSDAY'); p.add_argument('--baseline'); p.add_argument('--out')
    a = p.parse_args()
    cli = json.loads((ROOT / 'config/paths.json').read_text())['cli']
    ms = fetch(cli, a.since)
    rep = dict(since=a.since, checked=time.strftime('%Y-%m-%dT%H:%M:%S'), games=len(ms), overall=record(ms, a.team),
               per_map={m: record(ms, a.team, {m}) for m in a.maps}, other_maps=record(ms, a.team, {x['map'] for x in ms} - set(a.maps)))
    if a.baseline:
        old = [m for m in json.load(open(a.baseline, encoding='utf-8')) if m['createdAt'] < a.since and m['status'] == 'finished']
        rep['before'] = dict(games=len(old), overall=record(old, a.team), per_map={m: record(old, a.team, {m}) for m in a.maps})
    print(json.dumps(rep, indent=1))
    if a.out:
        Path(a.out).write_text(json.dumps(dict(rep, matches=ms), indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
