"""Publish only this research directory to its isolated authorized branch."""
from pathlib import Path
import argparse
import os
import subprocess
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'.git').exists())
PREFIX='research/agentic-improvement-20261107'
BRANCH='research/agentic-improvement-20261107'
ENV=os.environ.copy()
for key in ('GIT_CURL_VERBOSE','GIT_TRACE_CURL','GIT_TRACE','GIT_TRACE_PACKET','GIT_TRACE_CURL_NO_DATA'):ENV.pop(key,None)
ENV.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never',GH_PROMPT_DISABLED='1')
def git(*args, network=False):
    prefix=['git']
    if network:prefix+=['-c','credential.helper=','-c','credential.helper=!gh auth git-credential']
    p=subprocess.run(prefix+list(args),cwd=ROOT,env=ENV,capture_output=True,encoding='utf-8',errors='replace')
    if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-6000:])
    return p.stdout
def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['prepare','commit','push','verify']);args=ap.parse_args()
    assert git('branch','--show-current').strip()==BRANCH
    remote=git('remote','get-url','origin').strip().removesuffix('.git').lower()
    assert remote=='https://github.com/infosuii/neural-networkk-battlecode'
    staged=git('diff','--cached','--name-only').splitlines()
    assert all(p.startswith(PREFIX+'/') for p in staged),'Unrelated staged files; do not commit'
    if args.phase=='prepare':
        git('add','--sparse','--',PREFIX)
        git('-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check')
        print(git('diff','--cached','--stat')[-5000:])
    elif args.phase=='commit':
        assert staged
        print(git('commit','-m','Publish audited Battlecode retune, experimental release, and complete findings')[-2000:])
    elif args.phase=='push':
        assert not staged
        print(git('push','--set-upstream','origin','HEAD:refs/heads/'+BRANCH,network=True)[-2000:])
    else:
        local=git('rev-parse','HEAD').strip()
        rows=git('ls-remote','origin','refs/heads/'+BRANCH,network=True).splitlines()
        assert len(rows)==1 and rows[0].split()[0]==local
        print('Verified remote commit',local)

if __name__=='__main__':main()
