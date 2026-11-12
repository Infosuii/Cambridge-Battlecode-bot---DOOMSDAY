"""Death-context summary for a benchmark run: our deaths and the opponent's, by situation.

Usage: c_death_batch.py RUN [--limit N]
Extracts each distinct game's replay from its bundle, runs c_death_context.mjs (engine 2.0.0), then prints
the share of deaths by enemies/allies nearby, carried gems lost and location, separately for each team.
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
    ap.add_argument('--limit', type=int, default=10**9)
    a = ap.parse_args()
    games = json.loads((ROOT / 'artifacts/evaluations/v67' / a.run / 'games.json').read_text())['games']
    tmp = ROOT / 'artifacts/tmp/v67/replays' / a.run
    tmp.mkdir(parents=True, exist_ok=True)
    side_of, win_of, seen = {}, {}, set()
    files = []
    for g in games:
        key = (g['map'], g['side'], g['seed'])
        if key in seen:
            continue
        seen.add(key)
        bundle = next((ROOT / g['folder']).glob('*.repl26a'))
        name = f"{g['map']}-{g['side']}-{g['seed']}.repl26a"
        target = tmp / name
        if not target.exists():
            with zipfile.ZipFile(bundle) as z:
                target.write_bytes(z.read('replay.repl26a'))
        side_of[name] = 0 if g['side'] == 'a' else 1
        win_of[name] = g['win']
        files.append(str(target))
        if len(files) >= a.limit:
            break
    out = tmp / 'deaths.jsonl'
    if not out.exists():
        env = dict(os.environ, NFS_REPLAY_ENGINE='2.0.0')
        chunks = [files[i::8] for i in range(8)]
        procs = [subprocess.Popen(['node', '--no-warnings', 'tools/v67/c_death_context.mjs', str(out) + f'.{k}', *c],
                                  cwd=ROOT, env=env) for k, c in enumerate(chunks) if c]
        for p in procs:
            if p.wait():
                raise SystemExit('extraction failed')
        with out.open('w') as f:
            for k in range(8):
                part = Path(str(out) + f'.{k}')
                if part.exists():
                    f.write(part.read_text())
                    part.unlink()
    stats = {k: collections.Counter() for k in ('ours', 'theirs')}
    for line in out.read_text().splitlines():
        row = json.loads(line)
        us = side_of[row['file']]
        for d in row['deaths']:
            who = 'ours' if d['team'] == us else 'theirs'
            c = stats[who]
            c['n'] += 1
            c['gems'] += d['gems']
            c[f"e4={min(d['enemies4'], 3)}"] += 1
            c[f"outnumbered4"] += d['enemies4'] > d['allies4'] + 1
            c['alone8'] += d['allies8'] == 0
            c['ratio<0.8'] += d['hpRatio8'] < 0.8
            c['ownhalf'] += d['homeDist'] < d['enemyHomeDist']
            c['early<300'] += d['round'] < 300
            c['camp'] += d['enemies8'] == 0
    for who, c in stats.items():
        n = max(1, c['n'])
        print(f"{who}: deaths {c['n']} gems lost {c['gems']} ({c['gems'] / n:.1f}/death)")
        for k in sorted(k for k in c if k not in ('n', 'gems')):
            print(f'   {k:12s} {c[k] / n:.2f}')


if __name__ == '__main__':
    main()
