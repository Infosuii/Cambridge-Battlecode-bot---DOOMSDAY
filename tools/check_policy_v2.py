"""Bounded official direct-policy plumbing checks. No training, collection dataset or submission.

Per-game replay/stdout remains local under artifacts/tmp. Only concise evidence receipts may be shared.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
sys.path.insert(0,str(ROOT/'tools'))
from nfs import engine
from nfs.policy import records,observation,candidates
from nfs.policy import dataset as policy_dataset
from install_policy_v2 import install,PROFILES,HEAD_IDS

def validate_records(recs,model_dir,episode):
    """Replay real records through the exported CPU model. No optimizer or parameter update."""
    import numpy as np
    import torch
    from nfs.policy.export import load_model
    ds=policy_dataset.build_dataset(recs,episode_id=episode,group_id='untrained-plumbing-only',
        synthetic=False,expected_action_hash=candidates.ACTION_SCHEMA_HASH)
    model=load_model(model_dir);checked=0;max_error=0.
    with torch.no_grad():
        for row in ds.rows:
            d=row['decision'];K=d['K']
            if d['source']!=0 or not K or row['obs'] is None:continue
            z=model(torch.tensor(row['obs'][None]),records.HEADS[d['head']],torch.tensor(d['feat'][None]),
                    torch.tensor(d['legal'][None],dtype=torch.bool),torch.tensor([d['context']])).numpy()[0]
            legal=np.asarray(d['legal'],dtype=bool)
            error=float(np.max(np.abs(z[legal]-d['logits'][legal])))
            max_error=max(max_error,error);checked+=1
            if not np.allclose(z[legal],d['logits'][legal],rtol=2e-5,atol=2e-6):
                raise ValueError('actual NFS2 logits differ from exported direct model')
    return dict(passed=True,counts=ds.counts,logits_checked=checked,max_logit_error=max_error,training_updates=0)

def run(profile,maps,sides=('A',),opponents=('original',),build_only=False,model_dir=None,seed=20261024,record_head='all'):
    protocol=ROOT/'evaluation/policy_v2_protocol.json'
    lock=json.loads((ROOT/'evaluation/policy_v2_protocol.lock.json').read_text())
    digest=hashlib.sha256(protocol.read_bytes()).hexdigest()
    if digest!=lock['sha256']:raise ValueError('v2 framework protocol changed after freeze')
    declared=json.loads(protocol.read_text())
    amendment=ROOT/'evaluation/policy_v2_integration_amendment.json'
    amendment_digest=hashlib.sha256(amendment.read_bytes()).hexdigest()
    if amendment_digest!=json.loads(amendment.with_suffix('.lock.json').read_text())['sha256']:
        raise ValueError('v2 integration amendment changed after freeze')
    choice=ROOT/'evaluation/policy_v2_choice_amendment.json'
    choice_digest=hashlib.sha256(choice.read_bytes()).hexdigest()
    if choice_digest!=json.loads(choice.with_suffix('.lock.json').read_text())['sha256']:
        raise ValueError('v2 choice amendment changed after freeze')
    training_amendment=ROOT/'evaluation/policy_v2_training_plumbing_amendment.json'
    training_digest=hashlib.sha256(training_amendment.read_bytes()).hexdigest()
    if training_digest!=json.loads(training_amendment.with_suffix('.lock.json').read_text())['sha256']:
        raise ValueError('v2 training plumbing amendment changed after freeze')
    training=json.loads((ROOT/'evaluation/schedules/map_partitions.json').read_text())['partitions']['training']
    if not set(maps)<=set(training):raise ValueError('framework checks require reused training-partition maps')
    stamp=str(time.time_ns());dest=ROOT/'artifacts/tmp/policy_v2_checks'/profile/stamp
    install(dest,profile,model_dir,seed,record_head)
    def event(kind,**fields):
        with (dest/'metrics.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(dict(event=kind,time_unix=time.time(),**fields))+'\n')
    event('build_start',profile=profile,record_head=record_head)
    wasm=engine.official_build(dest,dest/'bot.wasm')
    event('build_complete',wasm_sha256=engine.sha256(wasm))
    result=dict(label=declared['label'],profile=profile,record_head=record_head,seed=seed,source_sha256=engine.tree_sha256(dest/'src'),
        wasm_sha256=engine.sha256(wasm),protocol_sha256=digest,amendment_sha256=amendment_digest,release=True,fuel='official default',
        choice_amendment_sha256=choice_digest,training_amendment_sha256=training_digest,map_label='reused_benchmark',training_games=0,parameter_updates=0,games=[])
    result['planned_games']=0 if build_only else len(opponents)*len(maps)*len(sides)
    engine.write_json(dest/'receipt.json',result)
    for opponent in (() if build_only else opponents):
        ref=ROOT/f'references/builds/{opponent}.wasm'
        for name in maps:
            for side in sides:
                folder=dest/'matches'/f'{name}-{opponent}-{side}'
                event('game_start',map=name,opponent=opponent,side=side,folder=str(folder))
                match=engine.run_match(wasm if side=='A' else ref,ref if side=='A' else wasm,
                    engine.MAPS/(name+'.map26a'),folder,candidate_side=side)
                stdout=engine.team_stdout(folder,side)
                invalid={}
                rec=records.decode_stdout(stdout,strict=False,stats=invalid,expected_obs_hash=observation.OBS_SCHEMA_HASH,
                                          expected_action_hash=candidates.ACTION_SCHEMA_HASH)
                row=dict(match.row(),opponent=opponent,invalid_records=invalid.get('invalid',0),stdout_bytes=len(stdout.encode()))
                row['records']={kind:sum(r['kind']==kind for r in rec) for kind in ('context','decision','execution')}
                row['opportunities']=[dict(zip(('round','champion','head','starts','direct','continued','fallback','overrides','skipped','interrupted'),map(int,x)))
                    for x in re.findall(r'NPO2 round=(\d+) champion=(\d+) head=(\d+) starts=(\d+) direct=(\d+) continued=(\d+) fallback=(\d+) overrides=(\d+) skipped=(\d+) interrupted=(\d+)',stdout)]
                row['costs']=[dict(zip(('round','champion','head','candidate','decision','execution','total','refused','resets','prepare_failed'),map(int,x)))
                    for x in re.findall(r'NPC2 round=(\d+) champion=(\d+) head=(\d+) candidate=(\d+) decision=(\d+) execution=(\d+) total=(\d+) refused=(\d+) resets=(\d+) prepare_failed=(\d+)',stdout)]
                latest={(r['champion'],r['head']):r for r in row['opportunities']}
                row['ownership_snapshot']=dict(partial=True,reason='periodic cumulative reports; final turns may be absent',
                    by_champion_head=list(latest.values()))
                if rec:
                    try:row['dataset_validation']=validate_records(rec,dest/'model',f'{name}-{opponent}-{side}')
                    except ValueError as exc:row['dataset_validation']=dict(passed=False,error=str(exc),training_updates=0)
                row['bot_error_lines']=[x for x in stdout.splitlines() if 'bot error:' in x]
                result['games'].append(row)
                engine.write_json(dest/'receipt.json',result)
                event('game_complete',map=name,opponent=opponent,side=side,faults=row['faults'],fuel_exhausted=row['fuel_exhausted'],
                      invalid_records=row['invalid_records'],records=row['records'])
    engine.write_json(dest/'receipt.json',result)
    event('collection_complete',games=len(result['games']),receipt=str(dest/'receipt.json'))
    print(json.dumps(dict(receipt=str(dest/'receipt.json'),wasm=str(wasm),games=len(result['games'])),indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',choices=PROFILES,default='direct_record')
    p.add_argument('--maps',nargs='+',default=['00rows'])
    p.add_argument('--sides',nargs='+',choices=['A','B'],default=['A'])
    p.add_argument('--opponents',nargs='+',choices=['original','v47','first-hour'],default=['original'])
    p.add_argument('--build-only',action='store_true')
    p.add_argument('--model-dir',type=Path)
    p.add_argument('--seed',type=int,default=20261024)
    p.add_argument('--record-head',choices=('all',*HEAD_IDS),default='all')
    a=p.parse_args();run(a.profile,a.maps,a.sides,a.opponents,a.build_only,a.model_dir,a.seed,a.record_head)
