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
from install_policy_v2 import install,PROFILES

def run(profile,maps,sides=('A',),opponents=('original',),build_only=False):
    protocol=ROOT/'evaluation/policy_v2_protocol.json'
    lock=json.loads((ROOT/'evaluation/policy_v2_protocol.lock.json').read_text())
    digest=hashlib.sha256(protocol.read_bytes()).hexdigest()
    if digest!=lock['sha256']:raise ValueError('v2 framework protocol changed after freeze')
    declared=json.loads(protocol.read_text())
    training=json.loads((ROOT/'evaluation/schedules/map_partitions.json').read_text())['partitions']['training']
    if not set(maps)<=set(training):raise ValueError('framework checks require reused training-partition maps')
    stamp=str(time.time_ns());dest=ROOT/'artifacts/tmp/policy_v2_checks'/profile/stamp
    install(dest,profile)
    wasm=engine.official_build(dest,dest/'bot.wasm')
    result=dict(label=declared['label'],profile=profile,source_sha256=engine.tree_sha256(dest/'src'),
        wasm_sha256=engine.sha256(wasm),protocol_sha256=digest,release=True,fuel='official default',
        map_label='reused_benchmark',training_games=0,parameter_updates=0,games=[])
    for opponent in (() if build_only else opponents):
        ref=ROOT/f'references/builds/{opponent}.wasm'
        for name in maps:
            for side in sides:
                folder=dest/'matches'/f'{name}-{opponent}-{side}'
                match=engine.run_match(wasm if side=='A' else ref,ref if side=='A' else wasm,
                    engine.MAPS/(name+'.map26a'),folder,candidate_side=side)
                stdout=engine.team_stdout(folder,side)
                invalid={}
                rec=records.decode_stdout(stdout,strict=False,stats=invalid,expected_obs_hash=observation.OBS_SCHEMA_HASH,
                                          expected_action_hash=candidates.ACTION_SCHEMA_HASH)
                row=dict(match.row(),opponent=opponent,invalid_records=invalid.get('invalid',0),stdout_bytes=len(stdout.encode()))
                row['records']={kind:sum(r['kind']==kind for r in rec) for kind in ('context','decision','execution')}
                row['opportunities']=[dict(zip(('round','head','starts','direct','continued','fallback','overrides'),map(int,x)))
                    for x in re.findall(r'NPO2 round=(\d+) head=(\d+) starts=(\d+) direct=(\d+) continued=(\d+) fallback=(\d+) overrides=(\d+)',stdout)]
                row['costs']=[dict(zip(('round','head','candidate','decision','execution','total','refused'),map(int,x)))
                    for x in re.findall(r'NPC2 round=(\d+) head=(\d+) candidate=(\d+) decision=(\d+) execution=(\d+) total=(\d+) refused=(\d+)',stdout)]
                row['bot_error_lines']=[x for x in stdout.splitlines() if 'bot error:' in x]
                result['games'].append(row)
                engine.write_json(dest/'receipt.json',result)
    engine.write_json(dest/'receipt.json',result)
    print(json.dumps(dict(receipt=str(dest/'receipt.json'),wasm=str(wasm),games=len(result['games'])),indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',choices=PROFILES,default='direct_record')
    p.add_argument('--maps',nargs='+',default=['00rows'])
    p.add_argument('--sides',nargs='+',choices=['A','B'],default=['A'])
    p.add_argument('--opponents',nargs='+',choices=['original','v47','first-hour'],default=['original'])
    p.add_argument('--build-only',action='store_true')
    a=p.parse_args();run(a.profile,a.maps,a.sides,a.opponents,a.build_only)
