"""Sparse exact-prefix current-source bank-context probes; never a candidate policy."""
import json
import sys
import zipfile
from pathlib import Path
from deep_preflight import ROOT
from deep_detector_report import save
sys.path.insert(0,str(ROOT/'tools/replay/puppet'))
from make_trace_binary import HEADER
from trace_format import decode
from run_reproductions import CLI,run_command,build,match,sha
from replay_format import parse
S=ROOT/'research/followup-v70-2026-10-29';L=ROOT/'artifacts/local-only/followup-v70-2026-10-29'


def main():
    plan=json.loads((S/'TRACE_PLAN.json').read_text(encoding='utf-8'));rows=[];source=L/'source/src'
    manifest=json.loads((S/'MANIFEST.json').read_text(encoding='utf-8'))['rows']
    for case in plan['cases']:
        mid=case['match_id'];folder=ROOT/'artifacts/tmp/followup-v70/bank-traces'/case['map'];contents={p.name:p.read_bytes() for p in source.iterdir() if p.is_file()}
        contents['deep_trace.h']=(f"#define DT_FROM {case['from']}\n#define DT_UNTIL {case['until']}\n#define DT_ACTOR {case['actor']}u\n"+HEADER).replace('\n','\r\n').encode()
        contents['common.h']=b'#include "deep_trace.h"\r\n'+contents['common.h']
        needle=b'        bc::end_turn();';assert contents['main.cpp'].count(needle)==1;contents['main.cpp']=contents['main.cpp'].replace(needle,b'        if(deeptrace::n) deeptrace::flush(bc::round_number());\r\n'+needle)
        anchor=b'    debug_block({ std::printf("M %d %u %s %d\\n", round, my_id, mode, target_group); });';assert contents['bot.cpp'].count(anchor)==1
        line=b'    DT3(17,ally_score,enemy_score,w.no_bank,w.altar_gated,tribute_off_until,hp,max_hp,gems,tune::kDangerHp,tune::kChannelGuard,state.contains(bc::champion_state::recalling),state.contains(bc::champion_state::submitting_gems),tune::kTributeCarry,force_tribute);\r\n'
        contents['bot.cpp']=contents['bot.cpp'].replace(anchor,line+anchor)
        for name,data in contents.items():
            p=folder/'src'/name;p.parent.mkdir(parents=True,exist_ok=True)
            if p.exists():assert p.read_bytes()==data
            p.write_bytes(data)
        wasm=folder.with_suffix('.wasm');run_command([CLI,'build',folder,'--release','--output',wasm],folder/'build.log')
        script=json.loads((L/'replay-inputs'/(mid+'.json')).read_text(encoding='utf-8'));meta=next(r for r in manifest if r['match_id']==mid);own=0 if meta['our_side']=='a' else 1;enemy=build(script,1-own,folder/'enemy');mp=ROOT/script['map_file'];original=L/'replays'/(mid+'.repl26a')
        trial=match(wasm if own==0 else enemy,enemy if own==0 else wasm,mp,folder/'run',original);actual=parse((ROOT/trial['raw_replay']).read_bytes(),mp.read_bytes());first=None
        for x,y in zip(script['inputs'],actual):
            if (x['tag'],x['action'],x['args'])!=(y['tag'],y['action'],y['args']):first={'input':x['input'],'round':x['r'],'actor':x['actor'],'expected_action':x['action'],'actual_action':y['action']};break
        if first is None and len(script['inputs'])!=len(actual):first={'round':script['inputs'][min(len(actual),len(script['inputs'])-1)]['r'],'reason':'input lengths differ'}
        bundle=next(p for p in (folder/'run').glob('*.repl26a') if zipfile.is_zipfile(p))
        with zipfile.ZipFile(bundle) as z:raw=z.read('team-'+meta['our_side']+'.stdout')
        (folder/'run/trace.bin').write_bytes(raw);records=decode(raw);cut=first['round'] if first else 100000;trusted=[r for r in records if r['r']<cut and r['emitted_round']<cut]
        contexts=[r for r in trusted if r['stage']=='BANK_CONTEXT'];conflict=[r for r in contexts if r['values']['recalling'] and (r['values']['no_bank'] or r['r']<r['values']['off_until']) and r['values']['own_score']+r['values']['bag']>=1000 and r['values']['hp']>=r['values']['maxhp']*r['values']['danger']]
        result=case|{'trace_replay_byte_exact':trial['replay_bytes_identical'],'first_input_divergence':first,'window_trusted':cut>case['until'],'trace_wasm_sha256':sha(wasm),'logged_records':len(records),'trusted_records':len(trusted),'bank_disable_conflict_contexts':conflict,'trusted_trace':trusted,'original_replay_sha256':trial['original_sha256']};rows.append(result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('trusted_trace','bank_disable_conflict_contexts')}|{'conflict_turns':len(conflict)}),flush=True)
    save(S/'CURRENT_BANK_TRACES.json',{'source':'downloaded unmodified v70 plus diagnostic logging only','plan_sha256':sha(S/'TRACE_PLAN.json'),'operational_failed_attempts':['First split trace produced a native summary but CLI bundle publication failed at the long UUID-based output path. That folder is preserved; no trace was interpreted. Reran at a shorter map-based path.'],'rows':rows})
if __name__=='__main__':main()
