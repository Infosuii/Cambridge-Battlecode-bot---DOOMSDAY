"""Compile the user-supplied v47 ZIP unchanged and run a frozen 80-game comparison."""
import argparse, hashlib, json, re, shutil, zipfile
from pathlib import Path
import train

ROOT=train.ROOT
SOURCE=Path('C:/Users/omdha/Downloads/bot.zip')
EXPECTED='fd502869d770d00c35f36e8f5031d15e2a41b08c257f7fc4211937451a1cda15'

def prepare(workers):
    folder=ROOT/'opponents/v47-supplied';folder.mkdir(parents=True,exist_ok=True)
    if train.sha(SOURCE)!=EXPECTED:raise ValueError('Supplied v47 ZIP changed; preserve identity before proceeding')
    snapshot=folder/'source.zip'
    if not snapshot.exists():shutil.copyfile(SOURCE,snapshot)
    if train.sha(snapshot)!=EXPECTED:raise ValueError('Stored v47 source hash differs')
    with zipfile.ZipFile(snapshot) as z:
        for entry in z.infolist():
            if entry.is_dir():continue
            target=(folder/entry.filename).resolve()
            if not target.is_relative_to(folder.resolve()):raise ValueError('Unsafe source archive path')
            raw=z.read(entry)
            if target.exists() and target.read_bytes()!=raw:raise ValueError('Extracted source was modified')
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    src=folder/'src';wasm=train.compile_bot(src,ROOT/'builds/v47-supplied.wasm',workers)
    macros=train.command([train.SDK/'bin/clang++.exe','-std=c++20','-msimd128','-fwasm-exceptions',
                         '-I'+str(train.ARENA/'sdk/cpp'),'-dM','-E','-x','c++',src/'common.h'])
    (folder/'effective-macros.txt').write_text(macros,encoding='utf-8')
    names=['A2_MLDRAFT','A2_MLPLAN','A2_CAMPNET','A2_POLICY','A2_ASSESS','A2_ENEMY_NET',
           'A2_MOVENET','A2_TILENET','APEX_TS_LOCALNET','APEX_OPP_MODEL','NOVA_LEARNER','A2_LAB']
    settings={}
    for name in names:
        m=re.search(r'^#define '+re.escape(name)+r' (.*)$',macros,re.M)
        settings[name]=m[1] if m else 'not defined in this source'
    learner=(src/'learner.h').read_text(encoding='utf-8')
    manifest=dict(label='v47 as identified by the user; no embedded version identifier verified',
                  original_zip_sha256=EXPECTED,source_unchanged=True,wasm_sha256=train.sha(wasm),
                  compiler=str(train.SDK/'bin/clang++.exe'),sdk=str(train.ARENA/'sdk/cpp'),
                  effective_switches=settings,draft_network_file_present=(src/'draft_net.h').exists(),
                  lab_learner_zero_initialized='inline float w_lab[16] = {};' in learner,
                  note='Existing learned tuning knobs are distinct from an active neural policy.')
    train.write(folder/'manifest.json',manifest);print(json.dumps(manifest),flush=True)
    return wasm,manifest

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--workers',type=int,default=20);args=parser.parse_args()
    opponent,manifest=prepare(args.workers)
    if args.prepare_only:return
    history_path=ROOT/'historical-training/final.json'
    if not history_path.exists():raise RuntimeError('Finish historical branch selection before v47 comparison')
    history=json.loads(history_path.read_text())
    neural=ROOT/'release/bot_neural_history.wasm' if history.get('status')=='evaluated' else ROOT/'release/bot_neural.wasm'
    verification=ROOT/('verification-history.json' if history.get('status')=='evaluated' else 'verification.json')
    if not verification.exists():raise RuntimeError('Selected release must be verified before benchmarking')
    protocol=json.loads((ROOT/'protocol.json').read_text())
    maps=sorted(map(Path,protocol['training_maps']+protocol['selection_maps']+protocol['final_holdout_maps']))
    strata={Path(p).stem:k for k in ['training_maps','selection_maps','final_holdout_maps'] for p in protocol[k]}
    frozen=ROOT/'evaluation/v47-schedule.json'
    schedule=dict(candidate=str(neural),candidate_sha256=train.sha(neural),opponent=str(opponent),
                  opponent_sha256=train.sha(opponent),opponent_source_zip_sha256=EXPECTED,
                  release=True,fuel='official default, no override',games=2*len(maps),maps=len(maps),
                  purpose='Separate evaluation only; no training or checkpoint selection against v47.',
                  map_hashes={m.stem:train.sha(m) for m in maps})
    if frozen.exists() and json.loads(frozen.read_text())!=schedule:raise ValueError('Frozen v47 schedule changed')
    train.write(frozen,schedule)
    jobs=[]
    for i,m in enumerate(maps):
        for side in ['A','B']:
            a,b=(neural,opponent) if side=='A' else (opponent,neural)
            jobs.append(dict(a=a,b=b,map_path=m,candidate_side=side,folder=ROOT/f'runs/v47-comparison/m{i:02d}-{side}'))
    results=train.run_jobs(jobs,args.workers)
    summary=train.summarize(results)
    by_stratum={k:train.summarize([r for r in results if strata[r['map']]==k]) for k in set(strata.values())}
    for r in results:
        d=r['summary'];opposite='teamB' if r['side']=='A' else 'teamA'
        r['opponent_faults']=d['diagnostics']['botFaults'][opposite]
    report=dict(status='complete',summary=summary,by_map_partition=by_stratum,
                opponent_faults=sum(r['opponent_faults'] for r in results),schedule=schedule,
                v47_source_audit=manifest,rows=[{k:v for k,v in r.items() if k!='summary'} for r in results],
                limitations=['The 80 games cover 40 deterministic maps and both sides, not 80 independent maps.',
                  '26 maps were used for gameplay training and six for checkpoint selection; the eight-map subset is reported separately.',
                  'v47 was introduced only after training; no v47 results selected or trained this checkpoint.',
                  'Version identity is based on the user-provided ZIP, pinned by SHA-256.'])
    train.write(ROOT/'v47-comparison.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['rows','v47_source_audit','schedule']},indent=2),flush=True)

if __name__=='__main__':main()
