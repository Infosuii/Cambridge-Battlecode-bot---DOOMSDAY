"""Warm-state map-profile ablation on one loss and a non-profile control."""
import argparse
import json
import os
import re
import subprocess
import zipfile
from pathlib import Path
from run_reproductions import ROOT,CLI,LOCAL,STUDY,run_command,match,sha
from replay_format import parse


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--node',required=True,type=Path);a=ap.parse_args()
    plan=json.loads((STUDY/'MASKING_PLAN.json').read_text(encoding='utf-8'));results=[]
    reproduction=json.loads((STUDY/'REPRO_PLAN.json').read_text(encoding='utf-8'))
    for entry in plan['cases']:
        case=next(c for c in reproduction['rows'] if c['card_id']==entry['card_id']);cid=case['card_id'];mid=case['match_id'];actor=entry['actor'];take=entry['takeover_round']
        folder=ROOT/'artifacts/tmp/deep-repro/masking-v1'/cid
        source=ROOT/'bots/live-69/src';contents={p.relative_to(source).as_posix():p.read_bytes() for p in source.rglob('*') if p.is_file()}
        anchor=b'#if A2_LAB\r\n    {\r\n        // Engine-lab joint search'
        assert contents['bot.cpp'].count(anchor)==1
        inject=(f'#if A2_LAB\r\n    if (my_id == {actor}u && round >= {take}) {{\r\n'
                '        static constexpr float deep_defaults[lab::kKnobs] = {A2_KNOBS};\r\n'
                '        for (int deep_k = 0; deep_k < lab::kKnobs; ++deep_k) lab::knobs[deep_k] = deep_defaults[deep_k];\r\n'
                '    }\r\n#endif\r\n').encode()
        contents['bot.cpp']=contents['bot.cpp'].replace(anchor,inject+anchor,1)
        for name,data in contents.items():
            q=folder/'src'/name;q.parent.mkdir(parents=True,exist_ok=True)
            if q.exists():assert q.read_bytes()==data
            q.write_bytes(data)
        wasm=folder.with_suffix('.wasm')
        run_command([CLI,'build',folder,'--release','--output',wasm],folder/'build.log')
        expected=json.loads((LOCAL/'replay-inputs'/(mid+'.json')).read_text(encoding='utf-8'));mp=ROOT/expected['map_file']
        own=0 if case['side']=='a' else 1;enemy=ROOT/'artifacts/tmp/deep-repro/suite-v1'/cid/f'puppet-{1-own}.wasm';out=folder/'run'
        trial=match(wasm if own==0 else enemy,enemy if own==0 else wasm,mp,out,LOCAL/'replays/examined'/(mid+'.repl26a'))
        raw=ROOT/trial['raw_replay'];inputs=parse(raw.read_bytes(),mp.read_bytes());script=out/'actual-inputs.json'
        script.write_bytes((json.dumps({'match_id':mid,'raw_replay':trial['raw_replay'],'inputs':inputs,'actor':actor,'window':[take-1,take+9]})+'\n').encode())
        env=os.environ.copy();env['NFS_REPLAY_ENGINE']='2.0.0'
        for tool,args in [('label_inputs.mjs',[script]),('compare_replays.mjs',[mid,raw,out/'comparison.json'])]:
            p=subprocess.run([str(a.node),'--no-warnings',str(ROOT/'tools/replay/puppet'/tool),*[str(x) for x in args]],cwd=ROOT,env=env,capture_output=True,timeout=120)
            if p.returncode:raise RuntimeError(p.stderr.decode('utf-8','replace'))
        actual=json.loads(script.read_text(encoding='utf-8'));comparison=json.loads((out/'comparison.json').read_text(encoding='utf-8'));first=None
        for x,y in zip(expected['inputs'],actual['inputs']):
            if (x['tag'],x['action'],x['args'])!=(y['tag'],y['action'],y['args']):first={'input':x['input'],'round':x['r'],'actor':x['actor'],'expected':x,'actual':y};break
        prefix=(first is None or first['round']>=take) and (comparison['first_divergence'] is None or comparison['first_divergence']['round']>=take)
        bundle=next(p for p in out.glob('*.repl26a') if zipfile.is_zipfile(p))
        with zipfile.ZipFile(bundle) as z:log=z.read('team-'+('b' if own==0 else 'a')+'.stdout').replace(b'\0',b'').decode('utf-8','replace')
        reject=min((int(v) for v in re.findall(r'puppet (?:rejected|missing) r=(\d+)',log)),default=None)
        cap=min(take+9,reject-1 if reject else take+9) if prefix else None
        values=re.search(rb'#define A2_KNOBS ([^\r\n]+)',contents['common.h']).group(1).decode()
        result=entry|{'match_id':mid,'source_wasm_sha256':sha(wasm),'warm_prefix_valid':prefix,'first_input_divergence':first,'first_state_divergence':comparison['first_divergence'],'first_enemy_rejection':reject,'valid_horizon_end':cap,'byte_identical_full_replay':trial['replay_bytes_identical'],'default_A2_values':[float(v) for v in values.split(',')],
                      'observations':[] if cap is None else [v for v in actual['observations'] if v['r']<=cap], 'outcome_ignored':True}
        results.append(result);print(json.dumps({k:result[k] for k in ('card_id','warm_prefix_valid','first_input_divergence','valid_horizon_end','byte_identical_full_replay')}),flush=True)
    (STUDY/'MASKING_RESULTS.json').write_bytes((json.dumps({'hands_off_used':0,'plan_sha256':sha(STUDY/'MASKING_PLAN.json'),'rows':results},indent=2)+'\n').encode())


if __name__=='__main__':main()
