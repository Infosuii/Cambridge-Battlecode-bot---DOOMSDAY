"""Machine-operable training operations: bounded comparison, baseline audit, status and action inspection.

No training, promotion or submission happens in this module. Engine comparisons use official release/default fuel.
"""
from __future__ import annotations
import copy
from collections import deque
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from nfs import engine
from .training import ROOT,writable
from .export import load_blob,export_model
from . import records as R
import torch

NEURAL_MACROS=('A2_MLDRAFT','A2_MLPLAN','A2_CAMPNET','A2_ENEMY_NET','A2_POLICY','A2_MOVENET','A2_TILENET',
               'APEX_TS_LEARNED','APEX_TS_LOCALNET')
DEFAULT_BASELINE=ROOT/'artifacts/baselines/heuristic-v1'

def baseline_source(destination):
    """Original deterministic gameplay plus its existing heuristic draft, all neural switches disabled."""
    destination=writable(destination)
    if destination.exists():raise FileExistsError('fresh baseline directory required')
    sys.path.insert(0,str(ROOT/'tools'))
    from install_models import install
    src=engine.make_bot_dir(ROOT/'bot/src',destination)/'src';install('release',src,quiet=True)
    p=src/'common.h';text=p.read_text(encoding='utf-8')
    for name in NEURAL_MACROS:
        text,count=re.subn(r'(?m)^(\s*#\s*define\s+'+name+r')\s+[^\r\n]+',r'\g<1> 0',text)
        if not count:raise ValueError('baseline audit lost macro '+name)
    p.write_text(text,encoding='utf-8',newline='\n')
    compiler=engine.PATHS['native_cxx'];env=dict(os.environ,PATH=str(Path(compiler).parent)+os.pathsep+os.environ.get('PATH',''))
    result=subprocess.run([compiler,'-std=c++20','-dM','-E','-I'+str(ROOT/'sdk/cpp'),str(src/'main.cpp')],
                          cwd=ROOT,capture_output=True,text=True,env=env,timeout=60)
    if result.returncode:raise ValueError('baseline preprocessing audit failed: '+result.stderr[-2000:])
    actual=dict(re.findall(r'^#define[ \t]+(\w+)[ \t]+([^\r\n]+)',result.stdout,re.M))
    checked=(*NEURAL_MACROS,'NN_ANY_HEAD','NN_POLICY_V2','NN_TRAINING','NN_POLICY_LOG','NN_POLICY_SAMPLE')
    if any(actual.get(k)!='0' for k in checked):
        raise ValueError('non-neural baseline macro audit failed: '+str({k:actual.get(k) for k in checked if actual.get(k)!='0'}))
    receipt=dict(kind='heuristic_non_neural_baseline',source_sha256=engine.tree_sha256(src),
        neural_macros={k:actual[k] for k in checked},lab_exports_stripped=True,
        drafting='existing deterministic heuristic lineup/map tables; inherited trained draft disabled',
        comparison_note='a separate full-bot baseline, not byte-equivalent to original; original has trained drafting')
    engine.write_json(destination/'baseline.json',receipt)
    return destination,receipt

def build_baseline(out):
    out=writable(out)
    if out.exists():raise FileExistsError('baseline versions are immutable; use a new version directory')
    out.mkdir(parents=True);bot,audit=baseline_source(out/'bot')
    wasm=engine.official_build(bot,out/'baseline.wasm')
    bundle=out/'baseline.zip';engine._run([engine.CLI,'bundle',bot,'--output',bundle])
    manifest=dict(version=1,kind='heuristic_non_neural_baseline',wasm='baseline.wasm',wasm_sha256=engine.sha256(wasm),
        zip='baseline.zip',zip_sha256=engine.sha256(bundle),audit=audit,cli_version=engine.cli_version(),
        release=True,fuel='official default',submitted=False,training_games=0,parameter_updates=0)
    engine.write_json(out/'manifest.json',manifest);return manifest

def load_baseline(path=DEFAULT_BASELINE):
    path=Path(path).resolve();manifest=json.loads((path/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('kind')!='heuristic_non_neural_baseline' or any(v!='0' for v in manifest['audit']['neural_macros'].values()):
        raise ValueError('baseline neural audit invalid')
    for key in ('wasm','zip'):
        file=(path/manifest[key]).resolve()
        if not file.is_relative_to(path) or engine.sha256(file)!=manifest[key+'_sha256']:
            raise ValueError('frozen baseline hash/path mismatch')
    return manifest,path/manifest['wasm']

def comparison_plan(candidate,previous,maps,sides=('A','B'),max_games=8):
    if not maps or len(set(maps))!=len(maps) or not sides or len(set(sides))!=len(sides) or not set(sides)<={'A','B'}:
        raise ValueError('unique maps and valid sides required')
    partitions=json.loads((ROOT/'evaluation/schedules/map_partitions.json').read_text())['partitions']
    allowed=set(partitions['training'])|set(partitions['selection'])
    if not set(maps)<=allowed:raise ValueError('final/unregistered maps refused; use the frozen final-evaluation gate')
    if not 1<=max_games<=24:raise ValueError('comparison bound must be1..24 games')
    candidate=Path(candidate).resolve();manifest,_=load_blob(candidate)
    baseline,_=load_baseline()
    versions=[]
    for index,path in enumerate(previous):
        path=Path(path).resolve();old,_=load_blob(path)
        versions.append(dict(name=f'previous_{index}',model_dir=str(path),checksum=old['checksum'],status=old['status'],
                             same_weights_control=old['checksum']==manifest['checksum']))
    games=len(maps)*len(sides)*(len(versions)+1)
    if games>max_games:raise ValueError(f'comparison requires{games} games, exceeds bound{max_games}')
    return dict(candidate=str(candidate),candidate_checksum=manifest['checksum'],candidate_status=manifest['status'],
        framework_source_sha256=engine.tree_sha256(ROOT/'bot/src'),
        baseline_version=str(DEFAULT_BASELINE),baseline_wasm_sha256=baseline['wasm_sha256'],
        opponents=[dict(name='heuristic_non_neural',kind='non_neural_baseline'),*versions],maps=maps,sides=list(sides),
        games=games,max_games=max_games,release=True,fuel='official default',map_label='reused_benchmark',
        promotion_authorized=False,parameter_updates=0)

def compare(candidate,previous,maps,out,*,sides=('A','B'),max_games=8,seed=20261024,max_seconds=300):
    if not 1<=max_seconds<=1800:raise ValueError('comparison time bound must be1..1800 seconds')
    deadline=time.monotonic()+max_seconds
    def remaining():
        value=int(deadline-time.monotonic())
        if value<1:raise TimeoutError('comparison wall-clock bound reached')
        return value
    plan=comparison_plan(candidate,previous,maps,sides,max_games);out=writable(out)
    protocol=ROOT/'evaluation/policy_v2_operations_protocol.json'
    digest=engine.sha256(protocol)
    if digest!=json.loads(protocol.with_suffix('.lock.json').read_text())['sha256']:
        raise ValueError('operations protocol changed after freeze')
    plan['operations_protocol_sha256']=digest
    if out.exists():raise FileExistsError('fresh comparison output required')
    out.mkdir(parents=True);engine.write_json(out/'plan.json',plan)
    sys.path.insert(0,str(ROOT/'tools'))
    from install_policy_v2 import install
    def event(kind,**fields):
        with (out/'metrics.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(dict(event=kind,time_unix=time.time(),**fields))+'\n')
    event('comparison_start',games=plan['games'],candidate_checksum=plan['candidate_checksum'])
    bot=install(out/'candidate','direct_evaluation',Path(candidate),seed)
    candidate_wasm=engine.official_build(bot,out/'candidate.wasm',timeout=remaining())
    baseline,baseline_wasm=load_baseline();audit=baseline['audit']
    opponents=[('heuristic_non_neural',baseline_wasm)]
    for item in plan['opponents'][1:]:
        bot=install(out/item['name'],'direct_evaluation',Path(item['model_dir']),seed)
        opponents.append((item['name'],engine.official_build(bot,out/(item['name']+'.wasm'),timeout=remaining())))
    if engine.tree_sha256(ROOT/'bot/src')!=plan['framework_source_sha256']:
        raise ValueError('framework source changed during comparison; freeze code before training operations')
    receipt=dict(label='model comparison; unvalidated framework check unless separately promoted',plan=plan,
        candidate_wasm_sha256=engine.sha256(candidate_wasm),baseline_audit=audit,
        opponent_sha256={name:engine.sha256(wasm) for name,wasm in opponents},games=[],summary={},parameter_updates=0,promotion_eligible=False)
    for name,opponent in opponents:
        for map_name in maps:
            for side in sides:
                folder=out/'games'/f'{name}-{map_name}-{side}'
                event('game_start',opponent=name,map=map_name,side=side,folder=str(folder))
                result=engine.run_match(candidate_wasm if side=='A' else opponent,opponent if side=='A' else candidate_wasm,
                    engine.MAPS/(map_name+'.map26a'),folder,candidate_side=side,timeout=remaining()).row()
                result['opponent']=name;receipt['games'].append(result);event('game_complete',**result)
                engine.write_json(out/'comparison.json',receipt)
    for name,_ in opponents:
        rows=[g for g in receipt['games'] if g['opponent']==name]
        receipt['summary'][name]=dict(games=len(rows),win_rate=sum(g['win'] for g in rows)/len(rows),
            mean_gem_margin=sum(g['gems']-g['opponent_gems'] for g in rows)/len(rows),
            bot_faults=sum(g['faults'] for g in rows),fuel_exhausted=sum(g['fuel_exhausted'] for g in rows),
            opponent_fuel_exhausted=sum(g['opponent_fuel_exhausted'] for g in rows))
    receipt['implementation_passed']=all(not g['faults'] and g['fuel_exhausted']<=1.25*g['opponent_fuel_exhausted']+4 for g in receipt['games'])
    event('comparison_complete',implementation_passed=receipt['implementation_passed'],summary=receipt['summary'])
    engine.write_json(out/'comparison.json',receipt);return receipt

def validate_evaluation_config(config,model_dir):
    config=json.loads(Path(config).read_text(encoding='utf-8'))
    every=int(config.get('every_epochs',2));maximum=int(config.get('max_evaluations',2))
    if not 1<=every<=4 or not 1<=maximum<=4:raise ValueError('invalid evaluation cadence/bound')
    comparison_plan(model_dir,[model_dir],config.get('maps',['00rows']),max_games=int(config.get('max_games',8)))
    if not 1<=int(config.get('max_seconds',120))<=300:raise ValueError('invalid automatic evaluation time bound')
    return config

def evaluate_epoch(actor,run,epoch,head,config,deadline=None):
    """Optional regular validation during an authorized real training run. Never select/promote on its own."""
    config=json.loads(Path(config).read_text(encoding='utf-8'))
    every=int(config.get('every_epochs',2));maximum=int(config.get('max_evaluations',2))
    if every<1 or not 1<=maximum<=4:raise ValueError('invalid evaluation cadence/bound')
    if epoch%every:return None
    done=list((run/'evaluations').glob('*/comparison.json'))
    if len(done)>=maximum:return None
    export=run/'exports'/f'epoch-{epoch:04d}'
    frozen=copy.deepcopy(actor).cpu()
    behavior,_=load_blob(run/'behavior')
    trained=sorted(set(behavior['provenance'].get('trained_heads',[]))|{head})
    export_model(frozen,'policy_v2_checkpoint',export,'trained',dict(synthetic=False,trained_heads=trained,updated_head=head,shared_encoder_frozen=True,
        source='authorized epoch export; not promoted',checkpoint_epoch=epoch))
    previous=run/'behavior'
    older=sorted((run/'exports').glob('epoch-*'))
    if len(older)>1:previous=older[-2]
    seconds=int(config.get('max_seconds',120))
    if deadline is not None:seconds=min(seconds,max(1,int(deadline-time.time())))
    result=compare(export,[previous],config.get('maps',['00rows']),run/'evaluations'/f'epoch-{epoch:04d}',
                   max_games=int(config.get('max_games',8)),max_seconds=seconds)
    return dict(epoch=epoch,comparison=str(run/'evaluations'/f'epoch-{epoch:04d}'/'comparison.json'),
                implementation_passed=result['implementation_passed'],summary=result['summary'])

def status(run):
    run=Path(run).resolve();index=run/'checkpoint.json';report=run/'report.json';events=deque(maxlen=10)
    if (run/'metrics.jsonl').exists():
        with (run/'metrics.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                try:events.append(json.loads(line))
                except json.JSONDecodeError:pass # An in-progress final write is not a completed event.
    checkpoint=json.loads(index.read_text()) if index.exists() else None
    if checkpoint:
        path=(run/checkpoint['checkpoint']).resolve()
        if not path.is_relative_to(run):raise ValueError('checkpoint index escapes run directory')
        checkpoint['checksum_valid']=path.exists() and engine.sha256(path)==checkpoint['sha256']
    result=json.loads(report.read_text()) if report.exists() else None
    if result is not None:result['history_entries']=len(result.pop('history',[]))
    collection=None
    if (run/'receipt.json').exists():
        c=json.loads((run/'receipt.json').read_text());games=c.get('games',[])
        collection=dict(profile=c.get('profile'),planned_games=c.get('planned_games'),completed_games=len(games),
            faults=sum(g['faults'] for g in games),invalid_records=sum(g.get('invalid_records',0) for g in games))
    return dict(run=str(run),checkpoint=checkpoint,last_events=list(events),collection=collection,
        report=result,
        deadline_expired=bool(checkpoint and time.time()>=checkpoint['absolute_deadline']))

def inspect_game(folder,side='A',tail=20):
    if side not in ('A','B') or not 1<=tail<=200:raise ValueError('invalid side/tail')
    folder=Path(folder);text=engine.team_stdout(folder,side);stats={}
    recs=R.decode_stdout(text,strict=False,stats=stats)
    decisions=[r for r in recs if r['kind']=='decision'];acks={(r['champion'],r['decision_id']):r for r in recs if r['kind']=='execution'}
    rows=[]
    for d in decisions[-tail:]:
        ack=acks.get((d['champion'],d['decision_id']))
        rows.append(dict(round=d['round'],champion=d['champion'],head=R.HEADS[d['head']],source=R.SOURCES[d['source']],
            selected_id=d['selected_id'],chosen=d['chosen'],candidates=d['K'],sampled=bool(d['sampled']),logp=d['logp'],
            execution=None if ack is None else dict(outcome=ack['outcome'],executed_id=ack['executed_id'],reason=ack['reason'])))
    summary=json.loads((folder/'summary.json').read_text()) if (folder/'summary.json').exists() else None
    return dict(folder=str(folder.resolve()),side=side,invalid_records=stats.get('invalid',0),decisions=len(decisions),
                actions=rows,match=None if summary is None else summary['match'])

def list_checkpoints(run):
    run=Path(run).resolve()
    return dict(run=str(run),checkpoints=[dict(path=str(p),epoch=int(p.stem.split('-')[-1]),bytes=p.stat().st_size,
        sha256=engine.sha256(p)) for p in sorted((run/'checkpoints').glob('epoch-[0-9][0-9][0-9][0-9].pt'))])

def list_versions(root):
    root=Path(root).resolve();rows=[]
    for pattern in ('*/export/manifest.json','*/exports/epoch-*/manifest.json'):
        for p in sorted(root.glob(pattern)):
            manifest,_=load_blob(p.parent)
            rows.append(dict(path=str(p.parent),name=manifest['name'],checksum=manifest['checksum'],status=manifest['status'],
                trained_heads=manifest['provenance'].get('trained_heads',[]),synthetic=bool(manifest['provenance'].get('synthetic'))))
    return dict(root=str(root),versions=rows)

def export_checkpoint(checkpoint,out):
    """Recover an export after a crash/deadline without resuming optimization or changing the registry."""
    from .model import DirectPolicyNet,HEAD_IDS
    state=torch.load(checkpoint,map_location='cpu',weights_only=True)
    if state.get('version')!=3 or state.get('head') not in HEAD_IDS:raise ValueError('unsupported checkpoint')
    out=writable(out)
    if out.exists():raise FileExistsError('fresh checkpoint export directory required')
    model=DirectPolicyNet(state['config']);model.load_state_dict(state['actor'])
    synthetic=bool(state.get('synthetic'));trained=not synthetic and int(state.get('updates',0))>0
    manifest=export_model(model,'policy_v2_recovered',out,'trained' if trained else 'untrained',dict(
        synthetic=synthetic,source='checkpoint recovery export; no optimization',trained_heads=[state['head']] if trained else [],
        parameter_updates=int(state.get('updates',0)),checkpoint_sha256=engine.sha256(checkpoint)))
    return dict(out=str(out),checksum=manifest['checksum'],status=manifest['status'],parameter_updates_now=0)
