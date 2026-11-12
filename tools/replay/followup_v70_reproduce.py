"""Verify current-source fidelity on one ranked loss and one control win; no interventions."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from deep_preflight import ROOT
from deep_detector_report import save
sys.path.insert(0,str(ROOT/'tools/replay/puppet'))
from replay_format import parse
from run_reproductions import build,match
STUDY='followup-v70-2026-10-29';S=ROOT/'research'/STUDY;L=ROOT/'artifacts/local-only'/STUDY
CASES=['2c139f84-3f74-4d5b-925f-aa4484776f80','2425dc90-76c7-4818-a3c4-db2fe40d4f70']
TRACE_CASES=['9c7c4fcd-c4d5-4ed6-ad94-c21dc6a756ad','951e9c30-fc77-4241-991c-23cac3abfd09']


def prepare():
    old=ROOT/'tools/replay/puppet/validate_inputs.mjs';text=old.read_text(encoding='utf-8')
    text=text.replace("from '../engine.mjs'","from './engine.mjs'").replace("'../../..'","'../..'")
    text=text.replace('deep-2026-10-28',STUDY).replace("'CANDIDATE_MANIFEST.json'","'PUPPET_MANIFEST.json'").replace("'examined'","'exploratory'")
    needle="const raw=fs.readFileSync(path.join(LOCAL,'replays',entry.partition,entry.match_id+'.repl26a'));"
    replacement="const raw=fs.readFileSync(entry.partition==='calibration-excluded'?path.join(ROOT,'artifacts/local-only/deep-2026-10-28/replays/calibration-excluded',entry.match_id+'.repl26a'):path.join(LOCAL,'replays',entry.match_id+'.repl26a'));"
    assert needle in text;text=text.replace(needle,replacement)
    target=ROOT/'tools/replay/followup_v70_validate_inputs.mjs';target.write_bytes(('// Derived from the frozen validator; only study paths and exploratory allowlist differ.\n'+text).encode())
    current=json.loads((S/'MANIFEST.json').read_text(encoding='utf-8'))['rows'];oldrows=json.loads((ROOT/'research/deep-2026-10-28/CANDIDATE_MANIFEST.json').read_text(encoding='utf-8'))['rows']
    entries=[r|{'partition':'exploratory'} for r in current if r['match_id'] in CASES+TRACE_CASES]+[r for r in oldrows if r['partition']=='calibration-excluded']
    save(S/'PUPPET_MANIFEST.json',{'purpose':'fidelity and two deduplicated winning-bag loop traces; five old excluded calibration games only','rows':entries})
    maps={p.stem.replace('-','').replace('_',''):p for p in (ROOT/'maps/local-benchmarks').glob('*.map26a')}
    for r in entries:
        mid=r['match_id'];folder=L/'replays' if r['partition']=='exploratory' else ROOT/'artifacts/local-only/deep-2026-10-28/replays/calibration-excluded'
        raw=(folder/(mid+'.repl26a')).read_bytes();native=json.loads((folder/(mid+'.summary.json')).read_text(encoding='utf-8'));mp=maps[r['map'].replace('-','').replace('_','')];mb=mp.read_bytes();inputs=parse(raw,mb);assert len(inputs)==native['match']['finalInput']
        script={'match_id':mid,'partition':r['partition'],'map_file':mp.relative_to(ROOT).as_posix(),'map_sha256':hashlib.sha256(mb).hexdigest(),'replay_sha256':hashlib.sha256(raw).hexdigest(),'roster':[{'id':c['id'],'team':0 if c['team']=='teamA' else 1} for c in native['roster']['champions']],'inputs':inputs}
        save(L/'replay-inputs'/(mid+'.json'),script)
    print(json.dumps({'calibration':5,'current_fidelity_cases':CASES}))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['prepare','validate','run']);ap.add_argument('--node',type=Path);a=ap.parse_args()
    if a.mode=='prepare':prepare();return
    manifest=json.loads((S/'PUPPET_MANIFEST.json').read_text(encoding='utf-8'));env=os.environ.copy();env['NFS_REPLAY_ENGINE']='2.0.0'
    if a.mode=='validate':
        for partition in ('calibration-excluded','exploratory'):
            paths=[L/'replay-inputs'/(r['match_id']+'.json') for r in manifest['rows'] if r['partition']==partition]
            p=subprocess.run([str(a.node),'--no-warnings',str(ROOT/'tools/replay/followup_v70_validate_inputs.mjs'),*[str(p) for p in paths]],cwd=ROOT,env=env,capture_output=True,timeout=120)
            print(p.stdout.decode('utf-8','replace'))
            if p.returncode:raise RuntimeError(p.stderr.decode('utf-8','replace'))
        return
    rows=[];source=ROOT/'artifacts/tmp/followup-v70/plain.wasm'
    for mid in CASES:
        meta=next(r for r in manifest['rows'] if r['match_id']==mid);script=json.loads((L/'replay-inputs'/(mid+'.json')).read_text(encoding='utf-8'));folder=ROOT/'artifacts/tmp/followup-v70/fidelity'/mid;mp=ROOT/script['map_file']
        puppets=[build(script,t,folder/f'puppet-{t}') for t in (0,1)];original=L/'replays'/(mid+'.repl26a');both=match(*puppets,mp,folder/'both-scripted',original)
        side=0 if meta['our_side']=='a' else 1;inputs=puppets[:];inputs[side]=source;live=match(*inputs,mp,folder/'source',original)
        row={'match_id':mid,'map':meta['map'],'result':meta['result'],'source_wasm_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'both_scripted':both,'downloaded_source':live};rows.append(row)
        print(json.dumps({'match_id':mid,'both_script_exact':both['replay_bytes_identical'],'current_source_exact':live['replay_bytes_identical']}),flush=True)
    save(S/'SOURCE_FIDELITY.json',{'cases':2,'source_unmodified':True,'both_script_exact':sum(r['both_scripted']['replay_bytes_identical'] for r in rows),'current_source_exact':sum(r['downloaded_source']['replay_bytes_identical'] for r in rows),'rows':rows})
if __name__=='__main__':main()
