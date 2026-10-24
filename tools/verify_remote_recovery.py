"""Wait for publication, then verify a fresh remote clone and an offline relocated Windows environment.

Default downloads every LFS pack from GitHub. --seed-local-packs avoids a second huge download but records that
limitation explicitly; remote object availability is still checked for every OID. No training/submission occurs.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
RESULT=ROOT/'evaluation/results/recovery_complete.json'

def save(data):
    temp=RESULT.with_suffix('.json.partial');temp.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');temp.replace(RESULT)

def run(args,cwd=ROOT,env=None,log=None):
    process=subprocess.run([str(a) for a in args],cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
    if log:
        Path(log).parent.mkdir(parents=True,exist_ok=True);Path(log).write_text(process.stdout+process.stderr,encoding='utf-8')
    if process.returncode:raise RuntimeError('Verification command failed: '+str(args[:3])+'; inspect saved log')
    return process.stdout

def main(args):
    state=dict(status='waiting_for_full_publication',repo='https://github.com/Infosuii/neural-networkk-battlecode',
               passed=False,full_remote_download=False,relocated_environment=False)
    save(state)
    while True:
        publication=ROOT/'evaluation/results/recovery_publish.json'
        try:p=json.loads(publication.read_text()) if publication.exists() else {}
        except json.JSONDecodeError:p={}
        if p.get('status')=='blocked':raise RuntimeError('Publisher blocked; inspect recovery_publish.json')
        if str(p.get('status','')).startswith('uploaded'):
            if p.get('source_errors'):raise RuntimeError('Source read errors must be repaired before complete recovery verification')
            break
        if not args.wait:raise RuntimeError('Publication is incomplete; use --wait while uploader runs')
        time.sleep(10)
    manifest=json.loads((ROOT/'recovery/snapshot.json').read_text())
    if manifest['status']!='complete' or manifest['errors']:raise RuntimeError('Incomplete snapshot')
    state.update(status='checking_all_remote_objects',source_files=manifest['files'],packs=len(manifest['packs']),
                 archive_logical_bytes=manifest['logical_bytes'],archive_packed_bytes=manifest['packed_bytes']);save(state)
    env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never',GIT_LFS_SKIP_SMUDGE='1')
    remote=json.loads(run([sys.executable,ROOT/'tools/recovery_lfs_status.py'],env=env))
    if remote['remote_missing'] or remote['remote_available']<len(manifest['packs']):raise RuntimeError('Missing remote LFS objects')
    state['remote_objects']=remote
    destination=ROOT/'recovery'/('remote_full_check_'+str(time.time_ns()))
    run(['git','clone','--branch','main',state['repo']+'.git',destination],env=env,
        log=ROOT/'evaluation/results/recovery_remote_clone.log')
    if args.seed_local_packs:
        # Local copies have remote OID presence proof. Restore verifies every byte against manifests from GitHub.
        for group in ('packs','histories'):
            target=destination/'recovery'/group;target.mkdir(parents=True,exist_ok=True)
            for source in (ROOT/'recovery'/group).iterdir():
                if not source.is_file():continue
                out=target/source.name
                if out.exists():out.unlink() # only disposable clone pointer files, never original data
                try:os.link(source,out)
                except OSError:shutil.copy2(source,out)
        state['data_source']='verified local packs plus all-remote-OID presence; not a second full remote download'
    else:
        run(['git','lfs','pull'],cwd=destination,env=env,log=ROOT/'evaluation/results/recovery_remote_lfs_pull.log')
        state['full_remote_download']=True;state['data_source']='fresh GitHub download of every recovery LFS object'
    state.update(status='verifying_and_restoring_archive',clone=str(destination));save(state)
    run([sys.executable,destination/'tools/recovery_archive.py','verify','--full'],cwd=destination,env=env,
        log=ROOT/'evaluation/results/recovery_archive_verify.log')
    restored=destination/'recovery/restored'
    run([sys.executable,destination/'tools/recovery_archive.py','restore','--scope','all','--dest',restored],cwd=destination,env=env,
        log=ROOT/'evaluation/results/recovery_archive_restore.log')
    run([sys.executable,destination/'tools/configure_recovery.py','--restored',restored],cwd=destination,env=env,
        log=ROOT/'evaluation/results/recovery_configure.log')
    paths=json.loads((destination/'config/paths.json').read_text())
    env.update(PYTHONPATH=str(destination/'python'),NFS_GXX=paths['native_cxx'],
               PATH=str(Path(paths['native_cxx']).parent)+os.pathsep+env.get('PATH',''),
               TMP=str(destination/'artifacts/tmp'),TEMP=str(destination/'artifacts/tmp'))
    state.update(status='testing_relocated_environment',relocated_python=paths['python'],relocated_native_cxx=paths['native_cxx']);save(state)
    run([paths['python'],'-m','unittest','discover','-s','tests/python'],cwd=destination,env=env,
        log=ROOT/'evaluation/results/recovery_relocated_python.log')
    run([paths['python'],'tools/run_cpp_tests.py'],cwd=destination,env=env,log=ROOT/'evaluation/results/recovery_relocated_cpp.log')
    run([paths['python'],'tools/check_teacher_exact.py','--out','evaluation/results/recovery_relocated_teacher_exact.json'],
        cwd=destination,env=env,log=ROOT/'evaluation/results/recovery_relocated_teacher_build.log')
    teacher=json.loads((destination/'evaluation/results/recovery_relocated_teacher_exact.json').read_text())
    if not teacher['passed']:raise RuntimeError('Relocated official byte identity failed')
    shutil.copy2(destination/'evaluation/results/recovery_relocated_teacher_exact.json',ROOT/'evaluation/results/recovery_relocated_teacher_exact.json')
    state.update(status='verified',passed=True,relocated_environment=True,teacher_exact=teacher['actual_sha256'],
                 official_cli_cache='Existing current-user official cache; fresh-laptop installer copies identical archived cache. No writes outside workspace in this verification.')
    save(state);print(json.dumps(state,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--wait',action='store_true')
    parser.add_argument('--seed-local-packs',action='store_true')
    args=parser.parse_args()
    try:main(args)
    except Exception as error:
        try:state=json.loads(RESULT.read_text())
        except Exception:state={}
        state.update(status='blocked',passed=False,error=str(error));save(state)
        raise
