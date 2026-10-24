"""Publish current committed source without waiting for the full historical-data push. No force push.

main remains the complete archive branch. source-checkpoint includes code, tests, frozen replay evidence and
reference binaries. Only recovery/packs and history bundles are omitted from THIS branch, not from the backup.
"""
import json
import os
from pathlib import Path
import subprocess
import time
ROOT=Path(__file__).resolve().parents[1]

def main():
    index=ROOT/'artifacts/tmp'/f'recovery-source-{time.time_ns()}.index'
    env=dict(os.environ,GIT_INDEX_FILE=str(index),GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
    def git(*args,input=None):
        return subprocess.check_output(['git',*args],cwd=ROOT,env=env,input=input).decode().strip()
    head=git('rev-parse','HEAD');git('read-tree',head)
    omit=git('ls-files','recovery/packs','recovery/histories').splitlines()
    if omit:git('update-index','--force-remove','--stdin',input=('\n'.join(omit)+'\n').encode())
    tree=git('write-tree')
    ref='refs/heads/source-checkpoint'
    existing=subprocess.run(['git','rev-parse','--verify',ref],cwd=ROOT,env=env,capture_output=True,text=True)
    parent=existing.stdout.strip() if existing.returncode==0 else 'ff433ae'
    commit=git('-c','user.name=lead','-c','user.email=lead@local','commit-tree',tree,'-p',parent,
               input=b'Update portable source checkpoint while complete historical archive uploads continue\n')
    if existing.returncode==0:git('update-ref',ref,commit,parent)
    else:git('update-ref',ref,commit)
    subprocess.run(['git','push','origin','source-checkpoint'],cwd=ROOT,env=env,check=True)
    result=dict(branch='source-checkpoint',commit=commit,source_from=head,
                archive_packs_excluded_from_this_branch_only=True,full_data_upload_continues_on_main=True)
    (ROOT/'evaluation/results/recovery_source_checkpoint.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
