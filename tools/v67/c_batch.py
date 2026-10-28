"""Run several bots through a schedule in parallel (raw_run.py each) and print their summary lines.

Usage: c_batch.py --seeds 11 12 --workers 4 RUN=BOTDIR [RUN=BOTDIR ...]
Defaults match the platform as closely as local play can: the whole map pool from both sides with no repeated slots
(research/v68/pool_plan.json), and our bot built exactly as submitted (NOVA_SEED 1) while the seeds vary the opponent.
Matches are deterministic and cached (python/nfs/engine.py), so a baseline already played costs nothing to rerun.
Compare a candidate with tools/v67/c_paired.py against a baseline run on the same plan and seeds.
"""
import argparse
import concurrent.futures as cf
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seeds', type=int, nargs='+', required=True)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--opponent', default='v65')
    ap.add_argument('--plan', default='research/v68/pool_plan.json')
    ap.add_argument('--bot-seed', type=int, default=1,
                    help='our bot is the shipped build (NOVA_SEED 1); --seeds vary the opponent. -1: vary both')
    ap.add_argument('--per-team', action='store_true', help='with --opponent proxy: imitate each slot\'s top team')
    ap.add_argument('jobs', nargs='+')
    a = ap.parse_args()

    def one(job):
        run, bot = job.split('=', 1)
        seed = ([] if a.bot_seed < 0 else ['--bot-seed', str(a.bot_seed)]) + (['--per-team'] if a.per_team else [])
        p = subprocess.run([sys.executable, 'tools/v67/raw_run.py', '--run', run, '--bot', bot, '--opponent', a.opponent,
                            '--plan', a.plan, '--seeds', *map(str, a.seeds), '--workers', str(a.workers), *seed],
                           cwd=ROOT, capture_output=True, text=True, encoding='utf8', errors='replace')
        lines = (p.stdout + p.stderr).strip().splitlines()
        return f'{run}: ' + (lines[-1] if lines else f'no output (exit {p.returncode})')

    with cf.ThreadPoolExecutor(len(a.jobs)) as ex:
        for line in ex.map(one, a.jobs):
            print(line, flush=True)


if __name__ == '__main__':
    main()
