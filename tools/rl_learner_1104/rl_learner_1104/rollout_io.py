"""Strict rlenv-column adapter for the first real own-policy CL1 PPO batch.

The runtime producer owns the bytes and completeness evidence. This adapter
recomputes rewards from public boundary scores, never from teacher-smoke reward.
It rejects missing observations/decisions rather than guessing their contents.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from .cl1 import PREPROCESS_VERSION
from .on_policy import ACTION_SCHEMA, REWARD_SPEC, Trajectory, team_reward, validate


def read_columns(directory):
    p = Path(directory)
    man = json.loads((p/'shard.json').read_text())
    n = man['rows']
    if not isinstance(n, int) or not 0 < n <= 50000:
        raise ValueError('shard rows must be1..50000')
    cols, hashes = {}, {}
    allowed = {'int8','uint8','int16','uint16','int32','uint32','float32'}
    total_bytes = 0
    for name, spec in man['columns'].items():
        if not name.isidentifier() or spec['dtype'] not in allowed:
            raise ValueError('invalid column name/dtype')
        shape = spec['shape']
        if not shape or shape[0] != n or any(not isinstance(i,int) or i < 0 for i in shape):
            raise ValueError('invalid column shape')
        dtype = np.dtype(spec['dtype']).newbyteorder('<')
        expected = int(np.prod(shape)) * dtype.itemsize
        total_bytes += expected
        if total_bytes > 100_000_000:
            raise ValueError('shard exceeds bounded laptop batch')
        file = p/(name+'.bin')
        if file.stat().st_size != expected:
            raise ValueError('column byte count mismatch: '+name)
        data = file.read_bytes()
        hashes[name] = hashlib.sha256(data).hexdigest()
        cols[name] = np.frombuffer(data, dtype=dtype).reshape(shape).copy()
    return man, cols, hashes


def trajectories(man, cols, actor_sha256, *, gamma=.995):
    if man.get('contract_version') != 'rlenv-2' or man.get('observation_point') != 'farm-pre-actor':
        raise ValueError('wrong contract or observation boundary')
    if (man.get('layout'), man.get('action_schema'), man.get('sampling')) != (10, ACTION_SCHEMA, 'complete'):
        raise ValueError('not a complete own-policy CL1 shard')
    policy = man['policy']
    if policy.get('actor_json_sha256') != actor_sha256 or man.get('preprocess') != PREPROCESS_VERSION:
        raise ValueError('actor/preprocess identity mismatch')
    required = ['x_fresh','episode','body_id','boundary','action','executed','mask','logp','has_logp',
                'reset','dt_rounds','terminated','truncated','bootstrap_valid','act_round','feat_round','decision_index']
    if any(k not in cols for k in required):
        raise ValueError('missing rollout columns: '+','.join(k for k in required if k not in cols))
    if cols['x_fresh'].shape != (man['rows'],448):
        raise ValueError('CL1 feature shape mismatch')
    if np.any(cols['episode'] < 0) or np.any(cols['episode'] >= len(man['episodes'])):
        raise ValueError('episode index out of bounds')
    for k in ('boundary','mask','has_logp','reset','terminated','truncated','bootstrap_valid'):
        if not np.all((cols[k] == 0) | (cols[k] == 1)):
            raise ValueError('non-boolean mask/flag: '+k)
    if not np.array_equal(cols['act_round'], cols['feat_round']):
        raise ValueError('observation captured before actual decision round')
    if not np.array_equal(cols['x_fresh'][:,0],cols['act_round']):
        raise ValueError('raw observation round differs from invocation')
    result = []
    for e, info in enumerate(man['episodes']):
        if info.get('ppo_eligible') is not True or info.get('status') not in ('terminated','truncated'):
            raise ValueError('episode is not PPO eligible: '+str(info.get('key')))
        for flag in ('incomplete','fuel_failed','log_cut'):
            if info.get(flag) is not False:
                raise ValueError('missing/failed episode integrity flag: '+flag)
        ix_ep = np.flatnonzero(cols['episode'] == e)
        for body in np.unique(cols['body_id'][ix_ep]):
            rows = ix_ep[cols['body_id'][ix_ep] == body]
            decisions = rows[cols['boundary'][rows] == 0]
            boundary = rows[cols['boundary'][rows] != 0]
            if not len(decisions):
                raise ValueError('body without decisions')
            # Do not sort bad data into apparently valid chronology.
            seq = cols['decision_index'][decisions]
            rounds = cols['act_round'][decisions]
            if np.any(np.diff(seq) != 1) or np.any(np.diff(rounds) <= 0):
                raise ValueError('missing/repeated decision, or unsupported same-round invocations')
            if not np.all(cols['has_logp'][decisions] == 1):
                raise ValueError('own-policy decision lacks behaviour logp')
            x = cols['x_fresh'][decisions]
            nxt = np.empty_like(x)
            nxt[:-1] = x[1:]
            term = cols['terminated'][decisions].astype(bool).tolist()
            trunc = cols['truncated'][decisions].astype(bool).tolist()
            if term[-1]:
                if info['status'] != 'terminated' or len(boundary):
                    raise ValueError('terminal episode/boundary mismatch')
                nxt[-1] = x[-1]  # never bootstrapped at terminal
                final = info['final_scores']
                next_scores = (final['ours'], final['theirs'])
                end_round = info['end_round']
            elif trunc[-1]:
                if len(boundary) != 1 or not cols['bootstrap_valid'][decisions[-1]]:
                    raise ValueError('truncation requires exactly one real final observation')
                nxt[-1] = cols['x_fresh'][boundary[0]]
                next_scores = (int(nxt[-1,1]),int(nxt[-1,2]))
                end_round = int(cols['act_round'][boundary[0]])
            else:
                raise ValueError('missing final boundary')
            durations = cols['dt_rounds'][decisions].astype(int).tolist()
            want = np.diff(np.append(rounds, end_round)).tolist()
            if durations != want:
                raise ValueError('duration disagrees with actual decision/boundary rounds')
            rewards = []
            for i in range(len(x)):
                ns = next_scores if i == len(x)-1 else (int(nxt[i,1]),int(nxt[i,2]))
                outcome = info['terminal_outcome'] if term[i] else 0
                rewards.append(team_reward(int(x[i,1]),int(x[i,2]),*ns,int(x[i,3]),durations[i],
                                           terminal=term[i],outcome=outcome,gamma=gamma))
            meta = dict(sampling='complete',layout=10,action_schema=ACTION_SCHEMA,preprocess=PREPROCESS_VERSION,
                        actor_sha256=actor_sha256,reward_spec=REWARD_SPEC,temperature=man['temperature'],
                        incomplete=False,fuel_failed=False,log_cut=False,policy_wasm_sha256=policy['wasm_sha256'],
                        encoder_sha256=policy['encoder_sha256'],engine_build_hash=info['engine_build_hash'],
                        map_sha256=info['map_hash'],episode_key=info['key'],body_id=int(body),
                        hidden_size=man.get('actor_hidden_size',16))
            t = Trajectory(torch.from_numpy(x.copy()),torch.from_numpy(nxt),
                           torch.from_numpy(cols['action'][decisions].astype(np.int64)),
                           torch.from_numpy(cols['executed'][decisions].astype(np.int64)),
                           torch.from_numpy(cols['mask'][decisions].astype(bool)),
                           torch.from_numpy(cols['logp'][decisions].astype(np.float32)),
                           torch.from_numpy(cols['reset'][decisions].astype(bool)),torch.tensor(rewards),durations,
                           term,trunc,[not v for v in term],meta,
                           torch.from_numpy(cols['h0'][decisions[0]:decisions[0]+1].copy()) if 'h0' in cols else None)
            validate(t,actor_sha256)
            result.append(t)
    if not result:
        raise ValueError('no trajectories')
    return result
