"""Build the V-M2 contact dataset from a run capsule (offline; never a bot input).

Usage: python tools/dz_contacts_build.py RUN OUT_DIR [--workers 2]
Extracts each game's native replay from research/dz/runs/RUN/evidence.zip and runs tools/dz_contacts.mjs for DZ's
team (A in "-A" cells, B in "-B" cells). Writes OUT_DIR/<map>-<side>.json; existing outputs are kept.
"""
import argparse
import concurrent.futures as cf
import os
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('out')
    ap.add_argument('--workers', type=int, default=2)
    a = ap.parse_args()
    out = Path(a.out)
    (out / 'replays').mkdir(parents=True, exist_ok=True)
    z = zipfile.ZipFile(ROOT / 'research/dz/runs' / a.run / 'evidence.zip')
    bundles = [n for n in z.namelist() if n.endswith('.repl26a') and n.startswith('games/')
               and Path(n).name not in ('lifecycle.repl26a', 'priority.repl26a')]
    jobs = []
    for n in bundles:
        cell = n.split('/')[1]
        target = out / f'{cell}.json'
        if target.exists():
            continue
        inner = out / 'replays' / f'{cell}.repl26a'
        with zipfile.ZipFile(z.open(n)) as bundle:
            inner.write_bytes(bundle.read('replay.repl26a'))
        jobs.append((cell, inner, target))
    env = dict(os.environ, NFS_REPLAY_ENGINE='2.0.0')

    def work(job):
        cell, inner, target = job
        team = '0' if cell.endswith('-A') else '1'
        r = subprocess.run(['node', str(ROOT / 'tools/dz_contacts.mjs'), str(inner), str(target), team],
                           capture_output=True, text=True, env=env)
        inner.unlink(missing_ok=True)
        return cell, r.returncode, (r.stdout + r.stderr).strip()[-200:]

    with cf.ThreadPoolExecutor(a.workers) as ex:
        for cell, code, msg in ex.map(work, jobs):
            print(cell, code, msg, flush=True)


if __name__ == '__main__':
    main()
