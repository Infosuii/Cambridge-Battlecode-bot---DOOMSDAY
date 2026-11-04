"""Bounded local paired suite; each report and input audit must succeed before continuing."""
import argparse, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def run(args):
    subprocess.run([sys.executable,str(HERE/'run.py'),*args],check=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=['conf','select'],required=True);a=p.parse_args()
    aliases=['resume-cpg','resume-contactgov','resume-progressgov','resume-fields-r1','resume-roster-r1']
    for alias in aliases:
        name=f'resume-{a.phase}-{alias.removeprefix("resume-")}-01'
        run(['run','--name',name,'--cand',alias,'--base','v92','--opps',
             'v92,x3inv,p65pack' if a.phase=='conf' else 'v92,x3ctr,p65,v86h',
             '--maps',a.phase,'--jobs','12','--task','basic-decision-strategy'])
        run(['report','--name',name])
        subprocess.run([sys.executable,str(HERE/'audit.py'),name],check=True,stdout=subprocess.DEVNULL)
        print('AUDIT PASSED',name,flush=True)
if __name__=='__main__': main()
