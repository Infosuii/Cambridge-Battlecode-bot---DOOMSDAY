"""Publish closed recovery packs while the snapshot runs; finish with all manifests. No force push or training.

Use the existing Git credential, never an inline token. Run only one publisher. A source-only push is incomplete.
"""
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'recovery'
ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')

def git(*args):
    r=subprocess.run(['git',*args],cwd=ROOT,env=ENV,text=True,capture_output=True)
    if r.returncode:
        # No credential or signed upload URLs go into receipts.
        error='Git operation failed: '+str(args[:2])+' exit='+str(r.returncode)
        print((r.stderr+r.stdout)[-1600:],flush=True)
        raise RuntimeError(error)
    return r.stdout.strip()

def receipt(data):
    p=ROOT/'evaluation/results/recovery_publish.json';p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def main():
    repo='https://github.com/Infosuii/neural-networkk-battlecode'
    if git('remote','get-url','origin')!=repo+'.git':raise RuntimeError('Unexpected remote; refusing archive upload')
    uploaded=0
    while True:
        tracked=set(git('ls-files','recovery/packs').splitlines())
        closed=[]
        for path in sorted((OUT/'packs').glob('pack-*.zip')):
            relative=path.relative_to(ROOT).as_posix()
            if relative not in tracked and zipfile.is_zipfile(path):closed.append(relative)
        # Keep commits bounded and publish useful data even before the long snapshot finalizes.
        chosen=closed[:16]
        snapshot=OUT/'snapshot.json'
        final=json.loads(snapshot.read_text()) if snapshot.exists() else None
        if chosen:
            git('add','--',*chosen)
            git('-c','user.name=lead','-c','user.email=lead@local','commit','-m',
                f'Archive closed recovery packs {Path(chosen[0]).stem} through {Path(chosen[-1]).stem}')
            git('push','origin','HEAD:main');uploaded+=len(chosen)
            receipt(dict(status='partial',repo=repo,uploaded_packs_this_run=uploaded,head=git('rev-parse','HEAD'),
                         snapshot_complete=bool(final),full_remote_restore_verified=False))
            print(f'Pushed {len(chosen)} additional packs; total new this run {uploaded}',flush=True)
            continue
        if final:
            # All actual closed packs are tracked. Metadata now proves which files the archive contains.
            git('add','--','recovery/snapshot.json','recovery/files.jsonl.gz','recovery/objects.jsonl.gz',
                'recovery/exclusions.json','recovery/source_errors.json','recovery/histories.json','recovery/histories')
            if git('diff','--cached','--name-only'):
                git('-c','user.name=lead','-c','user.email=lead@local','commit','-m','Finalize full recovery manifest, histories and pack checksums')
            git('push','origin','HEAD:main')
            head=git('rev-parse','HEAD');remote=git('ls-remote','origin','refs/heads/main').split()[0]
            if head!=remote:raise RuntimeError('Remote head mismatch')
            state='uploaded' if final['status']=='complete' else 'uploaded_with_source_errors'
            receipt(dict(status=state,repo=repo,head=head,remote_head=remote,packs=len(final['packs']),files=final['files'],
                         logical_bytes=final['logical_bytes'],packed_bytes=final['packed_bytes'],source_errors=final['errors'],
                         full_remote_restore_verified=False))
            print(f'All {len(final["packs"])} packs and manifests published; remote restore verification still required',flush=True)
            return
        time.sleep(10)

if __name__=='__main__':
    try:main()
    except Exception as error:
        receipt(dict(status='blocked',error=str(error),full_remote_restore_verified=False))
        raise
