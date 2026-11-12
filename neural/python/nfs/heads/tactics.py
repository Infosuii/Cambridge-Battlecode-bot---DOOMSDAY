"""Pure Python twin of nn_tactics.h candidate preprocessing (synthetic parity fixtures).

Coordinates passed to these builders are already in C's canonical team frame. IDs stay world/handle identifiers
for deterministic execution and are not model inputs. Inputs are bounded teacher-first candidates from the exact
runtime generator; this module preserves the legal mask and never infers API legality from scores.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
HEADS = ('move','combat','engage','ward','ts_leaf')

def belief_sector(dx: int, dy: int) -> int:
    ax,ay=abs(dx),abs(dy)
    if max(ax,ay)>16: return 8
    if dx==dy==0: return 0
    if ax*1000000<ay*414214: return 0 if dy>=0 else 4
    if ay*1000000<ax*414214: return 2 if dx>=0 else 6
    return (1 if dy>=0 else 3) if dx>=0 else (7 if dy>=0 else 5)

def bounded_belief(logit: float) -> np.float32:
    x=np.float32(logit)
    return np.float32(x/np.float32(np.float32(1)+abs(x))) if np.isfinite(x) else np.float32(0)

def schema(head: str) -> dict:
    if head not in HEADS:
        raise ValueError(head)
    return json.loads((ROOT/'schemas/heads'/f'{head}.json').read_text(encoding='utf-8'))

def normalise(raw, head: str) -> np.ndarray:
    spec=schema(head)
    x=np.asarray(raw,dtype=np.float32)
    if x.shape[-1:] != (spec['F'],):
        raise ValueError('feature width mismatch')
    scale=np.asarray([f['scale'] for f in spec['features']],dtype=np.float32)
    with np.errstate(invalid='ignore'):
        y=x/scale
        # C++ preserves non-finite values for nnh rejection rather than turning them into apparently valid numbers.
        return np.where(np.isfinite(x),np.clip(y,np.float32(-1),np.float32(1)),x).astype(np.float32)

def build(head: str, raw, ids=None, legal=None, context: int=0) -> dict:
    if head=='ts_leaf':
        raise ValueError('ts_leaf is a scalar leaf, use normalise(raw, "ts_leaf")')
    spec=schema(head); x=np.asarray(raw,dtype=np.float32)
    if x.ndim!=2 or x.shape[1]!=spec['F']:
        raise ValueError('expected [K,F]')
    if not 0<=context<len(spec['contexts']):
        raise ValueError('context out of range')
    n=min(len(x),16)
    ids=np.arange(n,dtype=np.uint32) if ids is None else np.asarray(ids,dtype=np.uint32)[:n]
    legal=np.ones(n,dtype=np.uint8) if legal is None else np.asarray(legal,dtype=np.uint8)[:n]
    if len(ids)!=n or len(legal)!=n:
        raise ValueError('ID/mask length mismatch')
    prior=np.full(n,-np.float32(spec['teacher_margin']),dtype=np.float32)
    if n:
        prior[0]=0
    return dict(head=spec['id'],K=n,F=spec['F'],context=context,id=ids,legal=legal,prior=prior,feat=normalise(x[:n],head))

def teacher_label(record: dict) -> int:
    """NFS1 teacher index is fixed at zero; it is an imitation label, not an outcome endorsement."""
    if record.get('head_name',record.get('head')) not in (*HEADS,6,7,8,9,12):
        raise ValueError('not an E head')
    if int(record.get('teacher',0))!=0:
        raise ValueError('teacher-first contract violated')
    return 0
