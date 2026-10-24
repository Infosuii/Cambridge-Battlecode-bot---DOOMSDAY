"""Compact v2 observation twin. Payload is normalized f32; no privileged reconstruction."""
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
SCHEMA=json.loads((ROOT/'schemas/policy_observation_v2.json').read_text(encoding='utf-8'))
OBS_DIM=173
OBS_SCHEMA_HASH=SCHEMA['obs_schema_hash']
def _schema_hash(schema):
    payload={k:v for k,v in schema.items() if k!='obs_schema_hash'}
    h=2166136261
    for b in json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode():
        h=((h^b)*16777619)&0xffffffff
    return h
if OBS_SCHEMA_HASH!=_schema_hash(SCHEMA):
    raise ValueError('compact observation schema hash mismatch')
def encode(self_raw,ally_raw,ally_mask,enemy_raw,enemy_mask):
    self_raw=np.asarray(self_raw,np.float32)
    ally_raw=np.asarray(ally_raw,np.float32);enemy_raw=np.asarray(enemy_raw,np.float32)
    ally_mask=np.asarray(ally_mask);enemy_mask=np.asarray(enemy_mask)
    if (self_raw.shape!=(40,) or ally_raw.shape!=(5,10) or enemy_raw.shape!=(6,12)
        or ally_mask.shape!=(5,) or enemy_mask.shape!=(6,)):
        raise ValueError('compact observation shape mismatch')
    out=np.zeros(OBS_DIM,np.float32)
    def row(raw,spec):
        v=np.asarray(raw,np.float32)
        if not np.isfinite(v).all():raise ValueError('nonfinite observation')
        return np.clip(v/np.asarray([f['scale'] for f in spec],np.float32),-4,4)
    out[:40]=row(self_raw,SCHEMA['self'])
    for i,m in enumerate(ally_mask):
        if m not in (0,1):raise ValueError('bad ally mask')
        if m:out[40+i*10:50+i*10]=row(ally_raw[i],SCHEMA['ally']);out[90+i]=1
    for i,m in enumerate(enemy_mask):
        if m not in (0,1):raise ValueError('bad enemy mask')
        if m:out[95+i*12:107+i*12]=row(enemy_raw[i],SCHEMA['enemy']);out[167+i]=1
    return out
def encode_bytes(data):
    if len(data)!=4*OBS_DIM:raise ValueError('compact observation length mismatch')
    x=np.frombuffer(data,dtype='<f4').copy()
    if not np.isfinite(x).all() or (np.abs(x)>4).any():raise ValueError('invalid normalized observation')
    if not np.isin(x[90:95],[0,1]).all() or not np.isin(x[167:173],[0,1]).all():raise ValueError('invalid observation mask')
    for i,m in enumerate(x[90:95]):
        if not m and np.any(x[40+i*10:50+i*10]):raise ValueError('nonzero padded ally')
    for i,m in enumerate(x[167:173]):
        if not m and np.any(x[95+i*12:107+i*12]):raise ValueError('nonzero padded enemy')
    return x
