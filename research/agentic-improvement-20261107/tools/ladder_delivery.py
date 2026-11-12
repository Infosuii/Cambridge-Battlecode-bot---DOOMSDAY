"""One explicitly authorized delivery, with durable receipts and no blind retry.

This separate command does not enable the continuous controller's deployment.
"""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys
import time
import zipfile

BASE = Path(os.environ.get('BATTLECODE_ROOT', r'C:\projects\cambridge battlecode\work\agentic-improvement'))
CLI = BASE / 'runtime/cambc.exe'
TEAM = 'fcf5f666-ea55-4da0-b8d4-97c64bb37236'

def now(): return datetime.now(timezone.utc).isoformat()
def save(path, obj):
    tmp = path.with_suffix('.tmp'); tmp.write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8'); tmp.replace(path)
def cli(*args, parse=True):
    p = subprocess.run([str(CLI), *map(str,args)], cwd=BASE / 'arena', capture_output=True, encoding='utf-8', errors='replace', timeout=120)
    if p.returncode: raise RuntimeError((p.stdout+p.stderr)[-2000:])
    return json.loads(p.stdout) if parse else p.stdout
def detail():
    d = cli('submissions', 'list', '--json'); assert d['team']['id'] == TEAM
    assert not d.get('frozen') and not d['team'].get('banned')
    return d

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('phase', choices=['upload','status','activate']); ap.add_argument('release',type=Path)
    ap.add_argument('--expected',type=int,required=True)
    args=ap.parse_args(); release=args.release.resolve()
    assert release.is_relative_to((BASE/'release').resolve())
    manifest=json.loads((release/'manifest.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(CLI.read_bytes()).hexdigest()==manifest['cli_sha256'], 'CLI changed since package verification'
    statefile=release/'ladder-receipt.json'
    state=json.loads(statefile.read_text(encoding='utf-8')) if statefile.exists() else {'authorization':'User: continue and once bot packaged push to ladder', 'created_at':now(), 'expected_version':args.expected}
    assert state['expected_version']==args.expected
    note='agentic-1108:'+manifest['candidate']+':'+manifest['source_digest'][:12]
    assert len(note)<=80
    d=detail(); active=d['active']['version']
    matches=[s for s in d['submissions'] if s.get('note')==note]
    if len(matches)>1: raise RuntimeError('Ambiguous existing uploads; inspect receipt')
    if args.phase=='upload':
        assert active==args.expected, f'Active version changed from {args.expected} to {active}'
        if matches:
            state.update(version=matches[0]['version'],phase='uploaded',reconciled_at=now())
        else:
            assert state.get('phase') not in ('uploading','upload_uncertain'), 'Uncertain upload requires reconciliation, never an automatic retry'
            # Verify the source that submit will bundle still equals this package.
            source=BASE/'arena/bots'/manifest['candidate']
            archive=release/manifest['source_zip']['file']
            assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['source_zip']['sha256']
            with zipfile.ZipFile(archive) as z:
                assert {n for n in z.namelist() if not n.endswith('/')} == {p.relative_to(source).as_posix() for p in (source/'src').rglob('*') if p.is_file()}, 'Source file set changed since packaging'
                for name in z.namelist():
                    if name.endswith('/'): continue
                    p=(source/name).resolve(); assert p.is_relative_to(source.resolve()) and p.read_bytes()==z.read(name)
            state.update(phase='uploading',note=note,before={'active':d['active'],'selected':d['selected']},at=now()); save(statefile,state)
            try:
                result=cli('submit','bots/'+manifest['candidate'],'--note',note,parse=False)
                state.update(phase='uploaded_response',upload_response=result,at=now()); save(statefile,state)
            except BaseException as exc:
                state.update(phase='upload_uncertain',error=str(exc),at=now()); save(statefile,state); raise
            d=detail(); matches=[s for s in d['submissions'] if s.get('note')==note]
            assert len(matches)==1, 'Reconcile upload by unique note; do not resubmit'
            state.update(version=matches[0]['version'],phase='uploaded')
    else:
        assert len(matches)==1 and state.get('version')==matches[0]['version']
        row=matches[0]; state.update(remote=row,last_checked_at=now())
        if args.phase=='activate':
            assert row['status'] in ('active','inactive'), f'Compilation not ready: {row["status"]}'
            assert active in (args.expected,row['version']), 'Team changed the active bot during delivery; do not override'
            if active!=row['version']:
                state.update(phase='activating',at=now());save(statefile,state)
                result=cli('submissions','activate',str(row['version']),'--json')
                state['activation_response']=result
            d=detail(); assert d['active']['version']==row['version'] and d['selected']['version']==row['version']
            state.update(phase='active',active_version=row['version'],activated_at=now())
            save(statefile,state)
            # Preserve the new incumbent for future collection/review without
            # enabling automatic deployment or changing a teammate's worktree.
            sys.path.insert(0,str(BASE/'autonomy'))
            from store import CONFIG, put
            assert CONFIG['team_id']==TEAM
            put('champion',{'version':row['version'],'name':manifest['candidate'],
                            'previous':args.expected,'previous_name':'v111',
                            'source_digest':manifest['source_digest'],'at':now()})
            put('deployment',{'phase':'promoted','candidate':row['version'],
                              'champion':args.expected,'experiment':'bounded-delivery-retune-20261107',
                              'note':note,'authorization':'Explicit user delivery request on 2026-11-08'})
    save(statefile,state)
    print(json.dumps({'phase':state['phase'],'version':state.get('version'),'active':d['active']['version'],'remote_status':matches[0]['status'] if matches else None,'receipt':str(statefile)}))

if __name__=='__main__': main()
