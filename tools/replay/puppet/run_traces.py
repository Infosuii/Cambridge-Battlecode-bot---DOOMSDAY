"""Run bounded traces and stop interpretation at the first accepted-input/state divergence."""
import argparse
import concurrent.futures as cf
import json
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deep_preflight import ROOT
from make_trace import make
from make_trace_binary import make as make_binary
from make_trace_tail import make as make_tail
from make_trace_channel import make as make_channel
from make_trace_bank_tail import make as make_bank_tail
from trace_format import decode as decode_numeric
from run_reproductions import CLI, LOCAL, STUDY, run_command, match, sha
from replay_format import parse


def compare(mid, raw, output, node):
    run_command([node, '--no-warnings', ROOT / 'tools/replay/puppet/compare_replays.mjs', mid, raw, output], output.with_suffix('.log'))
    d=json.loads(output.read_text(encoding='utf-8'))
    return {k:v for k,v in d.items() if k!='samples'}


def run_case(case, suite, node, format):
    cid=case['card_id'];folder=suite/cid;identity=({'numeric':make_binary,'tail':make_tail,'channel':make_channel,'bank-tail':make_bank_tail,'verbose':make}[format])(case,folder);wasm=folder.with_suffix('.wasm')
    receipt=folder/'build-receipt.json'
    if receipt.exists():
        old=json.loads(receipt.read_text(encoding='utf-8'));assert old['source_hashes']==identity['source_hashes'] and old['wasm_sha256']==sha(wasm)
    else:
        run_command([CLI,'build',folder,'--release','--output',wasm],folder/'build.log')
        receipt.write_bytes((json.dumps(identity|{'wasm_sha256':sha(wasm)},indent=2)+'\n').encode())
    own=0 if case['side']=='a' else 1
    enemy=ROOT/'artifacts/tmp/deep-repro/suite-v1'/cid/f'puppet-{1-own}.wasm'
    spec=json.loads((LOCAL/'replay-inputs'/(case['match_id']+'.json')).read_text(encoding='utf-8'))
    original=LOCAL/'replays/examined'/(case['match_id']+'.repl26a');mp=ROOT/spec['map_file']
    out=suite/(cid+'-run')
    run=match(wasm if own==0 else enemy,enemy if own==0 else wasm,mp,out,original)
    state=compare(case['match_id'],ROOT/run['raw_replay'],out/'state-comparison.json',node)
    actual=parse((ROOT/run['raw_replay']).read_bytes(),mp.read_bytes())
    expected=spec['inputs'];first=None
    for a,b in zip(expected,actual):
        if (a['tag'],a['action'],a['args'])!=(b['tag'],b['action'],b['args']):
            first={'input':a['input'],'round':a['r'],'phase':a['phase'],'actor':a['actor'],'expected':{'tag':a['tag'],'action':a['action'],'args':a['args']},'actual':b};break
    if first is None and len(expected)!=len(actual):
        n=min(len(expected),len(actual));first={'input':n+1,'round':expected[min(n,len(expected)-1)]['r'],'reason':'length differs'}
    import zipfile
    bundle=next(p for p in out.glob('*.repl26a') if zipfile.is_zipfile(p))
    with zipfile.ZipFile(bundle) as z:
        rawlog=z.read('team-'+case['side']+'.stdout')
    if format in ('numeric','tail','channel','bank-tail'):
        (out/'trace.bin').write_bytes(rawlog)
        lines=decode_numeric(rawlog)
        log='\n'.join('DT '+str(r['r'])+' '+str(r['actor'])+' '+r['stage']+' '+json.dumps(r['values']) for r in lines)
    else:
        log=rawlog.replace(b'\0',b'').decode('utf-8','replace')
        lines=[l for l in log.splitlines() if l.startswith('DT ')]
    (out/'trace.txt').write_bytes(log.encode())
    cutoff=first['round'] if first else None
    trusted=[l for l in lines if cutoff is None or
             ((l['r']<cutoff and l.get('emitted_round') is not None and l['emitted_round']<cutoff) if isinstance(l,dict) else int(l.split()[1])<cutoff)]
    return case|{'trace_actor':identity['trace_actor'],'trace_from':identity['trace_from'],'trace_until':identity['trace_until'],
                 'run':run,'state_comparison':state,'first_input_divergence':first,
                 'logged_lines':len(lines),'trusted_lines_before_divergence':len(trusted),
                 'trace_window_complete_before_divergence':cutoff is None or cutoff>identity['trace_until'],
                 'trusted_trace':trusted,'trace_file':(out/'trace.txt').relative_to(ROOT).as_posix()}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--suite',default='artifacts/tmp/deep-repro/trace-v1');ap.add_argument('--format',choices=['verbose','numeric','tail','channel','bank-tail'],default='verbose');ap.add_argument('--workers',type=int,default=2);ap.add_argument('--cards',nargs='*');ap.add_argument('--node',required=True,type=Path);a=ap.parse_args()
    suite=(ROOT/a.suite).resolve();assert suite.is_relative_to(ROOT/'artifacts') and 1<=a.workers<=4
    plan=json.loads((STUDY/'REPRO_PLAN.json').read_text(encoding='utf-8'))
    cases=[r for r in plan['rows'] if not a.cards or r['card_id'] in a.cards]
    result_path=STUDY/({'numeric':'TRACE_RESULTS_NUMERIC.json','tail':'TRACE_RESULTS_TAIL.json','channel':'TRACE_RESULTS_CHANNEL.json','bank-tail':'TRACE_RESULTS_BANK_TAIL.json','verbose':'TRACE_RESULTS.json'}[a.format]);results=json.loads(result_path.read_text(encoding='utf-8'))['rows'] if result_path.exists() else []
    with cf.ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures=[pool.submit(run_case,c,suite,a.node,a.format) for c in cases]
        for f in cf.as_completed(futures):
            r=f.result();results=[x for x in results if x['match_id']!=r['match_id']]+[r]
            result={'cases':len(results),'hands_off_used':0,'byte_exact_traces':sum(r['run']['replay_bytes_identical'] for r in results),
                    'complete_trusted_windows':sum(r['trace_window_complete_before_divergence'] for r in results),
                    'rule':'Only lines strictly before first accepted-input divergence are trusted; retain state divergence separately.',
                    'rows':sorted(results,key=lambda r:r['card_id'])}
            result_path.write_bytes((json.dumps(result,indent=2)+'\n').encode())
            print(json.dumps({'card':r['card_id'],'byte_exact':r['run']['replay_bytes_identical'],'first_input_divergence':r['first_input_divergence'],'trusted_window':r['trace_window_complete_before_divergence'],'trusted_lines':r['trusted_lines_before_divergence']}),flush=True)


if __name__=='__main__':main()
