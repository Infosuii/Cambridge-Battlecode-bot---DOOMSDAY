"""Convert a completed Mac integration game to a fully attributed PPO shard.

Uses the pinned R1 column writer/parser, then independently verifies actual
runtime decision counters. No game is launched, no failed row is censored.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bundle',required=True);ap.add_argument('--summary',required=True)
    ap.add_argument('--actor',required=True);ap.add_argument('--bot',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--map',required=True);ap.add_argument('--side',default='A');a=ap.parse_args()
    project=Path(__file__).resolve().parent/'mac-project'
    sys.path.insert(0,str(project/'tools/rl_env_1104_mac_e3'))
    import collect_policy as P
    import contract as C
    source=Path(a.bot)/'src';spec=json.loads(Path(a.actor).read_text());summary=json.loads(Path(a.summary).read_text())
    h=hashlib.sha256()
    for name in P.ENCODER_FILES:h.update(name.encode()+b'\0'+(source/name).read_bytes())
    encoder_hash=h.hexdigest();tree=hashlib.sha256()
    for file in sorted(source.iterdir()):
        if file.is_file():tree.update(file.name.encode()+b'\0'+file.read_bytes())
    wasm=Path(a.bot)/'.cambc/build/bot-injected.wasm'
    actor_hash=sha(a.actor);wasm_hash=sha(wasm)
    base=dict(layout=10,action_schema='target13-cl1-nofarm-v1',sampling='complete',stale_block=False,hidden_size=0,
              actor_hidden_size=spec['hidden'],decision_index=True,preprocess=spec['preprocess'],temperature=1.,
              observation_point='farm-pre-actor',data_origin='engine',reward_spec='jd-teamwin-potential-v1',
              run_ns=Path(a.out).name,log_limit=P.K.LOG_LIMIT,
              policy=dict(name='jd-cl1-e3-compact-budget',actor_json_sha256=actor_hash,wasm_sha256=wasm_hash,
                          encoder_sha256=encoder_hash,build='debug',flags=['CLRL_ACT=1','CLRL_MIN_DECISION_FUEL=72000','CLRL_HOLD_ROUNDS=8'],
                          source_parent_commit='ccfea3421e0dd379e2929803804e067d2bea3749',local_source_tree_sha256=tree.hexdigest(),
                          architecture=spec['architecture'],seed=1104),
              executor=dict(version='jd-macro-budget-hold-v1',minimum_fuel=72000,hold_rounds=8,invalid_target_event=True,
                            holds='physical World group target; no invented model decision/logp'),
              engine=dict(cambc='4.0.0',engine=summary['match']['engineVersion'],build_hash=summary['match']['engineBuildHash']))
    key='|'.join([sha(a.map),wasm_hash,actor_hash,a.side])
    meta=dict(key=key,map_file=str(a.map),map_file_sha256=sha(a.map),side=a.side,build_mode='debug',
              opponent=dict(name='v92',wasm_sha256=sha(project/'bots/jd-cl1-teacher/.cambc/build/bot-injected.wasm')))
    meta,cols,dec=P.episode(a.bundle,summary,a.side,meta)
    with zipfile.ZipFile(a.bundle) as z:lines=z.read('team-'+a.side.lower()+'.stdout').replace(b'\0',b'').decode('utf8','replace').splitlines()
    counters={};holds=0;bad_counter=0
    for line in lines:
        q=line.split()
        if line.startswith('CLQ1 '):
            try:
                if len(q)!=4:raise ValueError()
                key=(int(q[1]),int(q[2]))
                if key in counters:raise ValueError()
                counters[key]=int(q[3])
            except Exception:bad_counter+=1
        elif line.startswith('CLH1 '):holds+=1
    actual=[counters.get((d['round'],d['body'])) for d in dec]
    if actual!=cols['decision_index'] or len(counters)!=len(dec) or bad_counter:
        meta.update(ppo_eligible=False,incomplete=True,reward_complete=False)
        meta['problems'].append('actual runtime decision counter/row coverage mismatch')
    meta.update(runtime_counter_rows=len(counters),runtime_hold_rows=holds)
    # The official CLI does not emit a completed summary for a round-capped game.
    if summary['match']['outcome'] not in ('teamA','teamB','draw'):
        meta.update(ppo_eligible=False,incomplete=True,reward_complete=False)
        meta['problems'].append('not a completed terminal outcome')
    out=Path(a.out)
    if out.exists():raise ValueError('new run namespace required')
    writer=C.ShardWriter(str(out),base);writer.add_episode(meta,cols);shard=writer.flush()
    m,c=C.load_shard(shard,use_numpy=False);errors=C.validate(m,c)
    if errors:raise ValueError('; '.join(errors[:5]))
    report=dict(shard=shard,rows=m['rows'],episode=meta,actor_sha256=actor_hash,policy_wasm_sha256=wasm_hash,
                local_source_tree_sha256=tree.hexdigest(),validation='OK')
    (out/'collection_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
