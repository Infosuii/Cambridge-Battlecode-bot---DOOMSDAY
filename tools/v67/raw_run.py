"""Run the fixed schedule and save its actual output, without appending shared audit logs.

Use run.py --record-existing with the same run/opponent/seeds after completion.
That audits the builder's exact frozen source, even if live source changed later.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run',required=True)
    ap.add_argument('--opponent',default='v65')
    ap.add_argument('--bot',default='bots/v67',help='Separate prototype path for diagnostics; acceptance uses bots/v67')
    ap.add_argument('--seeds',type=int,nargs='+',default=[1,2])
    ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--holdout',action='store_true')
    a=ap.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',a.run):ap.error('invalid run name')
    if set(a.seeds)&{3,4} and not a.holdout:ap.error('reserved seeds3/4 require an explicitly frozen holdout')
    out=ROOT/'artifacts/evaluations/v67'/a.run
    if out.exists():ap.error('fresh run directory required')
    command=[sys.executable,'tools/proxy/local_duel.py','--plan','research/v59/duel_top1.json',
             '--bot',a.bot,'--name','v67','--proxy','bots/'+a.opponent,'--seeds',*map(str,a.seeds),
             '--workers',str(a.workers),'--replays','--out',str(out)]
    env=dict(os.environ);env.setdefault('CMAKE_BUILD_PARALLEL_LEVEL','4')
    p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',errors='replace')
    out.mkdir(parents=True,exist_ok=True)
    (out/'benchmark-output.txt').write_text(p.stdout+p.stderr,encoding='utf8',newline='\n')
    print(p.stdout+p.stderr,end='',flush=True)
    raise SystemExit(p.returncode)

if __name__=='__main__':main()
