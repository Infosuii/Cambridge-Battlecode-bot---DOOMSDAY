"""One pre-registered, bounded recall-loop diagnostic. No full-game gain claim."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deep_preflight import ROOT
from run_reproductions import CLI,LOCAL,STUDY,run_command,match,sha
from replay_format import parse


def restart_pairs(rows,actor,start,end):
    by={}
    for r in rows:
        if r.get('actor')==actor and start<=r['r']<=end and r['tag']==0:
            by.setdefault(r['r'],[]).append(r['action'])
    return sorted(r for r,a in by.items() if 7 in a and 4 in a)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--node',type=Path,required=True);a=ap.parse_args()
    plan=json.loads((STUDY/'TAKEOVER_PLAN.json').read_text(encoding='utf-8'));mid=plan['match_id'];actor=plan['actor'];take=plan['takeover_round']
    folder=ROOT/'artifacts/tmp/deep-repro/takeover-recall-v1';source=ROOT/'bots/live-69/src'
    old=b'if (state.contains(bc::champion_state::recalling) && win_now() && hp >= max_hp * tune::kDangerHp) {'
    new=(f'if (state.contains(bc::champion_state::recalling) && win_now() && hp >= max_hp * tune::kDangerHp &&\r\n'
         f'        !(my_id == {actor}u && round >= {take} && (w.no_bank || round < tribute_off_until))) {{').encode()
    source_hashes={}
    for p in source.rglob('*'):
        if not p.is_file():continue
        data=p.read_bytes()
        if p.name=='bot.cpp':assert data.count(old)==1;data=data.replace(old,new,1)
        q=folder/'src'/p.relative_to(source);q.parent.mkdir(parents=True,exist_ok=True)
        if q.exists():assert q.read_bytes()==data
        q.write_bytes(data);source_hashes[p.relative_to(source).as_posix()]=hashlib.sha256(data).hexdigest()
    identity={'plan_sha256':sha(STUDY/'TAKEOVER_PLAN.json'),'source_hashes':source_hashes,'scope':f'actor{actor},R>={take}, local diagnostic only'}
    (folder/'diagnostic-identity.json').write_bytes((json.dumps(identity,indent=2)+'\n').encode())
    wasm=folder.with_suffix('.wasm');receipt=folder/'build-receipt.json'
    if receipt.exists():assert json.loads(receipt.read_text(encoding='utf-8'))['wasm_sha256']==sha(wasm)
    else:
        run_command([CLI,'build',folder,'--release','--output',wasm],folder/'build.log')
        receipt.write_bytes((json.dumps(identity|{'wasm_sha256':sha(wasm)},indent=2)+'\n').encode())
    expected=json.loads((LOCAL/'replay-inputs'/(mid+'.json')).read_text(encoding='utf-8'))
    original=LOCAL/'replays/examined'/(mid+'.repl26a');mp=ROOT/expected['map_file']
    enemy=ROOT/'artifacts/tmp/deep-repro/suite-v1/C004/puppet-1.wasm'
    out=folder/'run';trial=match(wasm,enemy,mp,out,original)
    actual_inputs=parse((ROOT/trial['raw_replay']).read_bytes(),mp.read_bytes())
    local_script=out/'actual-inputs.json'
    local_script.write_bytes((json.dumps({'match_id':mid,'raw_replay':trial['raw_replay'],'inputs':actual_inputs,'actor':actor,'window':[take-1,take+9]})+'\n').encode())
    env=os.environ.copy();env['NFS_REPLAY_ENGINE']='2.0.0'
    for script,args,log in [('label_inputs.mjs',[local_script],out/'labels.log'),('compare_replays.mjs',[mid,ROOT/trial['raw_replay'],out/'state-comparison.json'],out/'comparison.log')]:
        r=subprocess.run([str(a.node),'--no-warnings',str(ROOT/'tools/replay/puppet'/script),*[str(x) for x in args]],cwd=ROOT,env=env,capture_output=True,timeout=120)
        log.write_bytes(r.stdout+r.stderr)
        if r.returncode:raise RuntimeError(r.stderr.decode('utf-8','replace'))
    actual=json.loads(local_script.read_text(encoding='utf-8'))
    comparison=json.loads((out/'state-comparison.json').read_text(encoding='utf-8'))
    first=None
    for x,y in zip(expected['inputs'],actual['inputs']):
        if (x['tag'],x['action'],x['args'])!=(y['tag'],y['action'],y['args']):first={'input':x['input'],'round':x['r'],'actor':x['actor'],'expected_action':x['action'],'actual_action':y['action']};break
    assert first and first['round']>=take,'Diagnostic changed the warm-up accepted inputs'
    assert comparison['first_divergence'] is None or comparison['first_divergence']['round']>=take,'Diagnostic changed pre-takeover states'
    bundle=next(p for p in out.glob('*.repl26a') if zipfile.is_zipfile(p))
    with zipfile.ZipFile(bundle) as z:enemylog=z.read('team-b.stdout').replace(b'\0',b'').decode('utf-8','replace')
    rejects=[int(r) for r in re.findall(r'puppet (?:rejected|missing) r=(\d+)',enemylog)]
    first_reject=min(rejects,default=None);valid_end=min(take+9,first_reject-1 if first_reject is not None else take+9)
    start,end=plan['decision_assertion_window'];baseline_pairs=restart_pairs(expected['inputs'],actor,start,end);candidate_pairs=restart_pairs(actual['inputs'],actor,start,end)
    assert len(baseline_pairs)>=3,'Baseline no longer exhibits the recorded failure'
    valid=valid_end>=end
    result={'match_id':mid,'case':'M1-winning-bag-disabled-bank-recall','evidence':'bounded causal diagnostic of decision rule only; not ladder/full-game effect',
            'takeover_round':take,'first_input_divergence':first,'first_state_divergence':comparison['first_divergence'],
            'warm_input_prefix_identical':True,'warm_round_states_identical':True,
            'first_enemy_script_rejection_round':first_reject,'valid_horizon_end':valid_end,'assertion_window':[start,end],
            'baseline_restart_pair_rounds':baseline_pairs,'diagnostic_restart_pair_rounds':candidate_pairs,
            'baseline_fails_assertion':bool(baseline_pairs),'diagnostic_passes_assertion':valid and not candidate_pairs,
            'observations_within_valid_horizon':[r for r in actual['observations'] if r['r']<=valid_end],
            'diagnostic_wasm_sha256':sha(wasm),'source_identity':identity,'outcome_ignored':True,
            'limits':['Only the cancellation inconsistency is tested.','Enemy actions are fixed and cannot respond; no result beyond the bounded horizon is interpreted.','A future production fix must pass full benchmark and held-out gates.']}
    (STUDY/'TAKEOVER_RESULT.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_identity','observations_within_valid_horizon','limits')}))


if __name__=='__main__':main()
