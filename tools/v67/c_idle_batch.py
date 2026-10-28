"""Idle-champion audit for a run (our side only): extracts replays, runs c_idle.mjs, and lists idle intervals.

Usage: c_idle_batch.py RUN [--min 40] [--top 30]
"""
import argparse
import collections
import json
import os
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('--min', type=int, default=40)
    ap.add_argument('--top', type=int, default=30)
    a = ap.parse_args()
    games = json.loads((ROOT / 'artifacts/evaluations/v67' / a.run / 'games.json').read_text())['games']
    tmp = ROOT / 'artifacts/tmp/v67/replays' / a.run
    tmp.mkdir(parents=True, exist_ok=True)
    side_of, files, seen = {}, [], set()
    for g in games:
        key = (g['map'], g['side'], g['seed'])
        if key in seen:
            continue
        seen.add(key)
        name = f"{g['map']}-{g['side']}-{g['seed']}.repl26a"
        target = tmp / name
        if not target.exists():
            with zipfile.ZipFile(next((ROOT / g['folder']).glob('*.repl26a'))) as z:
                target.write_bytes(z.read('replay.repl26a'))
        side_of[name] = 0 if g['side'] == 'a' else 1
        files.append(str(target))
    out = tmp / f'idle{a.min}.jsonl'
    if not out.exists():
        env = dict(os.environ, NFS_REPLAY_ENGINE='2.0.0')
        procs = [subprocess.Popen(['node', '--no-warnings', 'tools/v67/c_idle.mjs', f'{out}.{k}', str(a.min), *files[k::10]],
                                  cwd=ROOT, env=env) for k in range(10) if files[k::10]]
        if any(p.wait() for p in procs):
            raise SystemExit('extraction failed')
        with out.open('w') as f:
            for k in range(10):
                part = Path(f'{out}.{k}')
                if part.exists():
                    f.write(part.read_text())
                    part.unlink()
    rows, per_map = [], collections.Counter()
    for line in out.read_text().splitlines():
        r = json.loads(line)
        for i in r['idle']:
            if i['team'] != side_of[r['file']]:
                continue
            rows.append((i['to'] - i['from'], r['file'], i))
            per_map[r['file'].rsplit('-', 1)[0]] += i['to'] - i['from']
    total = sum(x for x, *_ in rows)
    print(f"{a.run}: {len(rows)} idle intervals >= {a.min} rounds on our side over {len(seen)} games; "
          f"{total / len(seen):.0f} idle champion-rounds per game")
    print('idle rounds by map/side:', ', '.join(f'{k} {v // 4}' for k, v in per_map.most_common(15)))
    for length, f, i in sorted(rows, key=lambda r: -r[0])[:a.top]:
        print(f"  {length:5d} rounds  {f:34s} type {i['type']:2d} R{i['from']}-{i['to']} at ({i['x']},{i['y']}) hp {i['hp']:.0f} gems {i['gems']}")


if __name__ == '__main__':
    main()
