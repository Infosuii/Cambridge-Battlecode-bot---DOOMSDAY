"""Frozen confirmation; never tune after this writes FINAL_FREEZE.json."""
import datetime,json,subprocess,sys
from pathlib import Path
import run as bridge
r=bridge.runner
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
RESEARCH=REPO/'research/jd-g5070-resume-0715'
ALIASES=['resume-release-cg','resume-release-cpg','resume-release-gov']

def cmd(args):subprocess.run([sys.executable,str(HERE/'run.py'),*args],check=True)
def main():
    frozen=r.load_frozen()
    lock=RESEARCH/'FINAL_FREEZE.json'
    if lock.exists():raise SystemExit('Already frozen: do not overwrite or tune after seeing final data')
    subprocess.run(['git','diff','--exit-code','--','bots/jd-g5070-resume-0715'],cwd=REPO,check=True)
    variants={a:dict(name=r.resolve(a),**frozen['bots'][r.resolve(a)]) for a in ALIASES}
    lock.write_text(json.dumps(dict(frozen_at=r.now(),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),variants=variants,policy='No bot/strategy edits after freeze; pool+fresh51104 confirmation only. Runtime governor is a control, not a selected policy.',cells_per_variant=2232,finalists=2),indent=2))
    for alias in ALIASES:
        for maps in ['pool','fresh51104']:
            name='final-'+alias.removeprefix('resume-release-')+'-'+maps+'-01'
            cmd(['run','--name',name,'--cand',alias,'--base','v92','--opps','v92,b5_c3,v61_c3,public-decrest,public-wardens,x3mf2','--maps',maps,'--jobs','12','--holdout','--task','candidate-integration'])
            cmd(['report','--name',name])
            subprocess.run([sys.executable,str(HERE/'audit.py'),name],check=True,stdout=subprocess.DEVNULL)
            print('FINAL INPUT AUDIT PASSED',name,flush=True)
if __name__=='__main__':main()
