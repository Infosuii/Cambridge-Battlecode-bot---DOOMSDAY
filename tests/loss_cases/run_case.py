"""Evaluate a real-loss decision invariant on an exact warm-prefix local replay."""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/replay'))
sys.path.insert(0,str(ROOT/'tools/replay/puppet'))
from replay_format import parse


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--case',type=Path,required=True);ap.add_argument('--replay',type=Path,required=True);ap.add_argument('--node',type=Path,required=True);ap.add_argument('--expect',choices=['pass','fail'],default='pass');a=ap.parse_args()
    case=json.loads(a.case.read_text(encoding='utf-8'));mid=case['match_id']
    source=json.loads((ROOT/'artifacts/local-only/deep-2026-10-28/replay-inputs'/(mid+'.json')).read_text(encoding='utf-8'))
    assert source['partition']=='examined' and source['validation']['replay_bytes_identical']
    work=Path(tempfile.mkdtemp(prefix='loss-case-',dir=ROOT/'artifacts/tmp'))
    actual_raw=work/'actual.repl26a';actual_raw.write_bytes(a.replay.read_bytes())
    inputs=parse(actual_raw.read_bytes(),(ROOT/case['map_file']).read_bytes())
    script=work/'actual-inputs.json';script.write_bytes((json.dumps({'match_id':mid,'raw_replay':actual_raw.relative_to(ROOT).as_posix(),'inputs':inputs,'actor':case['actor'],'window':[case['takeover_round']-1,case['takeover_round']+9]})+'\n').encode())
    env=os.environ.copy();env['NFS_REPLAY_ENGINE']='2.0.0'
    for tool,args in [('label_inputs.mjs',[script]),('compare_replays.mjs',[mid,actual_raw,work/'comparison.json'])]:
        p=subprocess.run([str(a.node),'--no-warnings',str(ROOT/'tools/replay/puppet'/tool),*[str(v) for v in args]],cwd=ROOT,env=env,capture_output=True,timeout=120)
        if p.returncode:raise RuntimeError(p.stderr.decode('utf-8','replace'))
        if tool=='label_inputs.mjs':
            labelled=json.loads(script.read_text(encoding='utf-8'))
            assert labelled['final']['outcome']!=0,'Invalid case: incomplete replay is not an evaluated candidate'
            assert labelled['final']['round']>=case['assertion_window'][1],'Invalid case: assertion window was not observed'
    actual=json.loads(script.read_text(encoding='utf-8'));comparison=json.loads((work/'comparison.json').read_text(encoding='utf-8'))
    first=None
    for x,y in zip(source['inputs'],actual['inputs']):
        if (x['tag'],x['action'],x['args'])!=(y['tag'],y['action'],y['args']):first=x['r'];break
    prefix_ok=(first is None or first>=case['takeover_round']) and (comparison['first_divergence'] is None or comparison['first_divergence']['round']>=case['takeover_round'])
    assert prefix_ok,'Invalid case: replay diverged before the required warm takeover state'
    lo,hi=case['assertion_window']
    native=json.loads((ROOT/'artifacts/local-only/deep-2026-10-28/replays/examined'/(mid+'.summary.json')).read_text(encoding='utf-8'))
    ours=next(c['team'] for c in native['roster']['champions'] if c['id']==case['actor'])
    enemy_ids={c['id'] for c in native['roster']['champions'] if c['team']!=ours}
    def enemy_sequence(rows):
        return [(r['r'],r['actor'],r['tag'],r['action'],r['args']) for r in rows if r.get('actor') in enemy_ids and lo<=r['r']<=hi]
    assert enemy_sequence(source['inputs'])==enemy_sequence(actual['inputs']),'Invalid case: enemy accepted script changed within the assertion window'
    by={}
    for r in actual['inputs']:
        if r.get('actor')==case['actor'] and lo<=r['r']<=hi and r['tag']==0:by.setdefault(r['r'],[]).append(r['action'])
    pairs=sorted(r for r,actions in by.items() if 7 in actions and 4 in actions)
    passed=len(pairs)<=case['maximum_restart_pairs']
    result={'case':case['id'],'valid_warm_prefix':True,'enemy_accepted_script_unchanged_in_assertion':True,'assertion_passed':passed,'restart_rounds':pairs,'expected':a.expect,'expectation_met':passed==(a.expect=='pass')}
    (work/'result.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result))
    if not result['expectation_met']:raise SystemExit(1)


if __name__=='__main__':main()
