"""NFS2 context/decision/execution joins. Missing acks and overrides never become on-policy actor samples.

This module prepares data; it never constructs an optimizer or updates parameters. Callers must supply real episode
and provenance group IDs, engine version and synthetic status. A stdout file alone cannot establish data independence.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import numpy as np
from . import records as R
from . import observation as obs

class DatasetError(ValueError):pass

@dataclass
class Dataset:
    rows:list[dict]
    counts:dict
    metadata:dict

def _key(r):return (int(r['champion']),int(r['snapshot']),int(r['obs_hash']),int(r['action_hash']))
def _id(r):return (int(r['champion']),int(r['decision_id']))

def log_probability(logits,legal,chosen):
    logits=np.asarray(logits,dtype=np.float32);legal=np.asarray(legal,dtype=bool)
    if chosen<0 or chosen>=len(logits) or not legal[chosen] or not legal.any():raise DatasetError('invalid sampled choice')
    m=np.max(logits[legal]);total=np.float32(0)
    for x in logits[legal]:total=np.float32(total+np.exp(np.float32(x-m)))
    return np.float32(np.float32(logits[chosen]-m)-np.log(total))

def build_dataset(records, *, episode_id:str,group_id:str,synthetic:bool,engine_version='1.0.3',
                  expected_obs_hash=obs.OBS_SCHEMA_HASH,expected_action_hash=None,provenance=None,logp_tolerance=2e-5) -> Dataset:
    if not episode_id or not group_id:raise DatasetError('explicit episode and provenance group IDs required')
    if engine_version!='1.0.3':raise DatasetError('NFS2 gameplay requires engine1.0.3; no historical adapter is implied')
    contexts={};decisions={};acks={};counts=Counter();action_identity=expected_action_hash
    for record in records:
        # Validate in-memory dictionaries too, using exactly the strict wire interpretation.
        r=R.decode_payload(R.encode_payload(record),expected_obs_hash=expected_obs_hash,expected_action_hash=expected_action_hash)
        if action_identity is None:action_identity=r['action_hash']
        if r['action_hash']!=action_identity:raise DatasetError('mixed action schemas in one dataset episode')
        counts[r['kind']]+=1
        if r['kind']=='context':
            key=_key(r)
            if key in contexts:raise DatasetError('duplicate/colliding snapshot; episode streams must stay distinct')
            try:x=obs.encode_bytes(r['raw'])
            except ValueError as e:raise DatasetError('invalid v2 observation snapshot') from e
            if not np.isfinite(x).all():raise DatasetError('nonfinite encoded observation')
            contexts[key]=(r,x)
        elif r['kind']=='decision':
            key=_id(r)
            if key in decisions:raise DatasetError('duplicate decision ID in champion/episode stream')
            decisions[key]=r
        else:
            key=_id(r)
            if key in acks:
                if acks[key]['outcome']!=0 or r['outcome']==0:raise DatasetError('duplicate final/pending execution acknowledgement')
            acks[key]=r
    rows=[]
    for key,d in decisions.items():
        source=int(d['source']);ack=acks.get(key);context=contexts.get(_key(d));chosen=int(d['chosen'])
        counts['source_'+R.SOURCES[source]]+=1
        label=int(d['teacher']);teacher_id=int(d['teacher_id'])
        counts['teacher_absent' if teacher_id==R.NO_ACTION else 'teacher_outside_candidates' if label<0 else 'teacher_representable']+=1
        reasons=[];execution_ok=False
        if context is None:reasons.append('missing_context')
        elif source==0 and context[0]['round']!=d['round']:raise DatasetError('direct policy used a different-turn snapshot')
        if ack is None:reasons.append('missing_ack')
        else:
            if _key(ack)!=_key(d) or ack['round']!=d['round']:raise DatasetError('ack snapshot/schema/round mismatch')
            if ack['option_id']!=d['option_id']:raise DatasetError('ack option identity mismatch')
            option=ack['outcome']==2 and bool(d['flags']&R.DEFINED_OPTION)
            execution_ok=(ack['outcome']==1 or option) and ack['source']==source and ack['executed_id']==d['selected_id'] and chosen>=0
            if not execution_ok:reasons.append('execution_not_selected_or_undefined')
        sampled=bool(d['sampled'])
        if sampled:
            got=log_probability(d['logits'],d['legal'],chosen)
            if abs(float(got)-float(d['logp']))>logp_tolerance:raise DatasetError('logged behavior logp does not match exact masked logits')
        ppo=bool(context is not None and execution_ok and source==0 and sampled and d['reason']==0)
        # Imitation uses explicitly annotated teacher actions actually executed by this stream, not fabricated labels.
        imitation=bool(context is not None and execution_ok and label>=0 and ack['executed_id']==teacher_id and source!=3)
        if not sampled:reasons.append('not_sampled')
        if source!=0:reasons.append('not_direct_start')
        if d['reason']:reasons.append('decision_fallback_reason')
        for why in set(reasons):counts['excluded_'+why]+=1
        counts['ppo_eligible']+=ppo;counts['imitation_eligible']+=imitation
        rows.append(dict(decision=d,execution=ack,obs=None if context is None else context[1],ppo_mask=ppo,
                         imitation_mask=imitation,execution_ok=execution_ok,episode_id=episode_id,group_id=group_id,
                         synthetic=bool(synthetic),stream=(episode_id,d['champion'],d['head']),exclusions=tuple(sorted(set(reasons)))))
    # A macro can be committed and then interrupted by a later same-turn failure. Its initial ack alone
    # does not establish an executed option trajectory. Missing/truncated endings fail closed.
    endings={}
    for row in rows:
        d=row['decision']
        if d['option_id'] and d['flags']&R.OPTION_END:
            key=(d['champion'],d['head'],d['option_id'])
            if key in endings:raise DatasetError('duplicate option termination')
            endings[key]=row
    for row in rows:
        d=row['decision']
        if not (d['option_id'] and d['flags']&R.OPTION_START):continue
        end=endings.get((d['champion'],d['head'],d['option_id']))
        why=None
        if end is None:why='option_unclosed'
        elif end['decision']['round']<d['round']:raise DatasetError('option termination predates start')
        elif end['decision']['selected_id']!=d['selected_id']:raise DatasetError('option termination changes selected action')
        elif end['decision']['reason'] or end['execution'] is None or end['execution']['reason'] or \
             end['execution']['outcome']!=2 or end['execution']['executed_id']!=d['selected_id'] or \
             not (end['decision']['flags']&R.DEFINED_OPTION) or \
             (end is not row and (end['decision']['source']!=1 or end['execution']['source']!=1)):
            why='option_interrupted'
        if why:
            counts['ppo_eligible']-=row['ppo_mask'];counts['imitation_eligible']-=row['imitation_mask']
            row['ppo_mask']=row['imitation_mask']=False
            row['exclusions']=tuple(sorted(set(row['exclusions'])|{why}));counts['excluded_'+why]+=1
    counts['orphan_ack']=len(set(acks)-set(decisions))
    return Dataset(rows,dict(counts),dict(version=2,format='NFS2',episode_id=episode_id,group_id=group_id,
        synthetic=bool(synthetic),engine_version=engine_version,obs_hash=expected_obs_hash,action_hash=action_identity,
        provenance=dict(provenance or {}),accounting=dict(independent_matches=0 if synthetic else 1,synthetic_episodes=1 if synthetic else 0,decisions=len(rows))))

def from_stdout(text,**kwargs):return build_dataset(R.decode_stdout(text),**kwargs)

def collate(rows:list[dict], *, device='cpu') -> dict:
    import torch
    n=len(rows)
    x=np.zeros((n,obs.OBS_DIM),np.float32);feat=np.zeros((n,R.MAX_K,R.F),np.float32)
    legal=np.zeros((n,R.MAX_K),bool);ids=np.full((n,R.MAX_K),R.NO_ACTION,np.uint32)
    logits=np.full((n,R.MAX_K),-np.inf,np.float32)
    ints={k:np.zeros(n,np.int64) for k in ('head','context','chosen','teacher','round','champion','snapshot','source')}
    lp=np.zeros(n,np.float32);ppo=np.zeros(n,bool);imi=np.zeros(n,bool)
    for i,row in enumerate(rows):
        d=row['decision'];K=d['K']
        if row['obs'] is not None:x[i]=row['obs']
        feat[i,:K]=d['feat'];legal[i,:K]=d['legal'];ids[i,:K]=d['id'];logits[i,:K]=d['logits']
        for k in ints:ints[k][i]=d[k]
        lp[i]=d['logp'];ppo[i]=row['ppo_mask'];imi[i]=row['imitation_mask']
    result={k:torch.as_tensor(v,device=device) for k,v in dict(obs=x,feat=feat,legal=legal,id=ids,behavior_logits=logits,
        behavior_logp=lp,ppo_mask=ppo,imitation_mask=imi,**ints).items()}
    result['metadata']=[{k:row[k] for k in ('episode_id','group_id','synthetic','stream','exclusions')} for row in rows]
    return result

def split_by_group(rows, *, validation_fraction=.2,seed=20261024):
    if not 0<validation_fraction<1:raise DatasetError('validation fraction must be between0 and1')
    train=[];validation=[]
    episode_groups={}
    for row in rows:
        ep=row['episode_id'];group=row['group_id']
        if ep in episode_groups and episode_groups[ep]!=group:raise DatasetError('episode assigned to incompatible provenance groups')
        episode_groups[ep]=group
        u=int.from_bytes(hashlib.sha256(f'{seed}:{group}'.encode()).digest()[:8],'big')/2**64
        (validation if u<validation_fraction else train).append(row)
    assert_disjoint_groups(train,validation)
    return train,validation

def assert_disjoint_groups(a,b):
    if {r['group_id'] for r in a}&{r['group_id'] for r in b} or {r['episode_id'] for r in a}&{r['episode_id'] for r in b}:
        raise DatasetError('training/validation provenance leakage')

def option_intervals(rows):
    """Explicit intervals only. Continued options keep their initiating ID and never create extra policy starts."""
    grouped={}
    for row in rows:
        d=row['decision']
        if not d['option_id']:continue
        key=(row['episode_id'],d['champion'],d['head'],d['option_id'])
        grouped.setdefault(key,[]).append(row)
    result=[]
    for key,items in grouped.items():
        items=sorted(items,key=lambda r:(r['decision']['round'],r['decision']['decision_id']))
        starts=[r for r in items if r['decision']['flags']&R.OPTION_START]
        if len(starts)!=1:raise DatasetError('option requires exactly one explicit start')
        if starts[0] is not items[0]:raise DatasetError('continuation predates its start')
        for r in items[1:]:
            if r['decision']['source']!=1:raise DatasetError('option continuation must retain continued source')
        end=[r for r in items if r['decision']['flags']&R.OPTION_END]
        result.append(dict(key=key,start=starts[0],rows=items,closed=bool(end),duration_rounds=items[-1]['decision']['round']-items[0]['decision']['round']))
    return result

def save_dataset(dataset:Dataset,path) -> tuple[Path,Path]:
    """Save tensor inputs/masks plus a checksummed manifest. Targets/rewards must be supplied separately."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    batch=collate(dataset.rows)
    arrays={k:v.cpu().numpy() for k,v in batch.items() if k!='metadata'}
    np.savez_compressed(path,**arrays)
    if path.suffix!='.npz':path=Path(str(path)+'.npz')
    manifest=path.with_suffix('.manifest.json')
    data=dict(dataset.metadata,counts=dataset.counts,rows=batch['metadata'],sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    manifest.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return path,manifest

def load_arrays(path):
    path=Path(path);meta=json.loads(path.with_suffix('.manifest.json').read_text(encoding='utf-8'))
    if meta['version']!=2 or meta['format']!='NFS2' or hashlib.sha256(path.read_bytes()).hexdigest()!=meta['sha256']:
        raise DatasetError('dataset version/checksum mismatch')
    with np.load(path,allow_pickle=False) as z:arrays={k:z[k].copy() for k in z.files}
    return arrays,meta
