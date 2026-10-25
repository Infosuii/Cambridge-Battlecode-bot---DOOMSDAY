"""List our ranked and unranked matches created after a timestamp (read-only; uses the logged-in CLI session).

Usage: python tools/replay/fetch_since.py --since 2026-10-25T13:30:12Z --out data/ladder/<name>.json
Prints records by kind and the losses by map and opponent.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import time
import sys

ROOT = Path(__file__).resolve().parents[2]


def page(cli, kind, cursor):
    args = [str(cli), 'matches', 'list', '--team', 'me', '--kind', kind, '--limit', '100', '--json'] + (['--cursor', cursor] if cursor else [])
    for _ in range(4):
        p = subprocess.run(args, capture_output=True, timeout=120)
        if p.stdout.strip():
            return json.loads(p.stdout.decode('utf-8'))
        time.sleep(5)
    raise SystemExit(p.stderr.decode('utf-8', errors='replace'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--since', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--cli', default=str(ROOT / 'tools/vendor/cambc.exe'))
    a = ap.parse_args()
    found = {}
    for kind in ['ranked', 'unranked']:
        cursor = None
        for _ in range(10):
            d = page(a.cli, kind, cursor)
            for m in d['matches']:
                found[m['matchId']] = m
            cursor = d.get('nextCursor')
            if not cursor or (d['matches'] and min(m['createdAt'] for m in d['matches']) < a.since):
                break
    new = sorted((m for m in found.values() if m['createdAt'] > a.since), key=lambda m: m['createdAt'])
    Path(a.out).write_text(json.dumps(new, indent=1) + '\n', encoding='utf-8')
    fin = [m for m in new if m['status'] == 'finished']
    me = lambda m: next(t for t in m['teams'] if t['name'] == 'DOOMSDAY')
    print(f'{len(new)} matches after {a.since}, {len(fin)} finished; latest {new[-1]["createdAt"] if new else "-"}')
    for kind in ['ranked', 'unranked']:
        f = [m for m in fin if m['kind'] == kind]
        print(f'  {kind}: {sum(me(m)["result"] == "win" for m in f)}/{len(f)} wins')
    losses = [m for m in fin if me(m)['result'] == 'loss']
    print('  losses by map:', Counter(m['map'] for m in losses).most_common())
    print('  losses by opponent:', Counter(next(t['name'] for t in m['teams'] if t['name'] != 'DOOMSDAY') for m in losses).most_common())


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
