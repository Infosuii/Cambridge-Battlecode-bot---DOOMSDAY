"""Independently check every-round state hashes for all completed local cases."""
import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deep_preflight import ROOT


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--node',type=Path,required=True);a=ap.parse_args()
    study=ROOT/'research/deep-2026-10-28';data=json.loads((study/'REPRO_RESULTS.json').read_text(encoding='utf-8'))
    def one(row,kind):
        raw=ROOT/row[kind]['raw_replay'];out=raw.parent/'state-comparison.json'
        env=os.environ.copy();env['NFS_REPLAY_ENGINE']='2.0.0'
        proc=subprocess.run([str(a.node),'--no-warnings','tools/replay/puppet/compare_replays.mjs',row['match_id'],str(raw),str(out)],cwd=ROOT,env=env,capture_output=True,timeout=120)
        if proc.returncode:raise RuntimeError(proc.stderr.decode('utf-8','replace'))
        proof=json.loads(out.read_text(encoding='utf-8'));assert proof['every_round_state_identical'] and proof['replay_bytes_identical']
        return {'card_id':row['card_id'],'match_id':row['match_id'],'kind':kind,**{k:v for k,v in proof.items() if k not in ('samples','match_id')}}
    with cf.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(one,r,k) for r in data['rows'] for k in ('compiled_script_control','frozen_source_test')]
        results=[f.result() for f in cf.as_completed(futures)]
    assert len(results)==24 and data['cases_completed']==12
    result={'cases':12,'losses':10,'controls':2,'comparisons':len(results),'passed':24,'failed':0,'hands_off_used':0,
            'state_samples_compared':sum(r['matched_samples'] for r in results),
            'engine':'2.0.0','source_rebuild_sha256':data['rows'][0]['source_wasm_sha256'],
            'server_wasm_byte_identity':'not available; local source behavioral fidelity verified across full games',
            'rows':sorted(results,key=lambda r:(r['card_id'],r['kind']))}
    (study/'REPRO_STATE_VALIDATION.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':main()
