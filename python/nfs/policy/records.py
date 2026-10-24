"""Strict NFS2 direct-policy codec. NFS1 is never reinterpreted; full wire: agents/v2_records/WIRE.md."""
from __future__ import annotations
import base64
import binascii
import struct
import numpy as np

MAGIC=0x3253464E
VERSION=2
MAX_PAYLOAD=8192
MAX_K=16
F=12
NO_ACTION=0xffffffff
KINDS={0:'context',1:'decision',2:'execution'}
SOURCES={0:'direct_policy',1:'continued_option',2:'teacher_fallback',3:'safety_override'}
OUTCOMES={0:'pending',1:'executed',2:'defined_option',3:'guard_refused',4:'overridden',5:'failed'}
HEADS={1:'strategy',2:'objective',3:'role',4:'bank',5:'shop',6:'move',7:'combat',8:'engage'}
OPTION_START=1
OPTION_END=2
DEFINED_OPTION=4
HEADER=struct.Struct('<IHHIIIiIIQ')
DECISION=struct.Struct('<HHHhhBBBBHQIIfIIII')
EXECUTION=struct.Struct('<IBBHQII')

class RecordError(ValueError): pass

def checksum(payload: bytes) -> int:
    h=2166136261
    for b in payload: h=((h^b)*16777619)&0xffffffff
    return h

def _numeric(value,lookup):
    if isinstance(value,str):
        for n,name in lookup.items():
            if name==value:return n
        raise RecordError(f'unknown enum {value}')
    return int(value)

def validate_record(r: dict) -> None:
    try:
        kind=_numeric(r['kind'],KINDS)
        if kind not in KINDS:raise RecordError('unknown kind')
        if int(r.get('version',VERSION))!=VERSION:raise RecordError('not NFS2')
        if not 0<int(r['obs_hash'])<2**32 or not 0<int(r['action_hash'])<2**32:raise RecordError('missing schema identity')
        if not 0<=int(r['round'])<2**31:raise RecordError('round out of range')
        for k in ('champion','snapshot'):
            if not 0<=int(r[k])<2**32:raise RecordError(f'{k} out of range')
        did=int(r.get('decision_id',0))
        if not 0<=did<2**64 or (kind==0)!=(did==0):raise RecordError('decision ID/kind mismatch')
        if kind==0:
            raw=r['raw']
            if not isinstance(raw,(bytes,bytearray)) or not 0<len(raw)<=MAX_PAYLOAD-48:raise RecordError('raw context bound')
            return
        source=_numeric(r['source'],SOURCES)
        if source not in SOURCES:raise RecordError('unknown source')
        if not 0<=int(r.get('reason',0))<65536:raise RecordError('reason bound')
        if not 0<=int(r.get('option_id',0))<2**64:raise RecordError('option ID bound')
        if kind==2:
            if _numeric(r['outcome'],OUTCOMES) not in OUTCOMES:raise RecordError('unknown execution outcome')
            for key in ('executed_id','action_fuel','log_fuel'):
                if not 0<=int(r.get(key,NO_ACTION if key=='executed_id' else 0))<2**32:raise RecordError(key+' bound')
            return
        K=int(r['K']); chosen=int(r.get('chosen',-1));teacher=int(r.get('teacher',-1));flags=int(r.get('flags',0))
        if int(r['head']) not in HEADS or not 0<=K<=MAX_K or int(r.get('F',F))!=F:raise RecordError('head/shape bound')
        if not 0<=int(r.get('context',0))<=3 or int(r.get('sampled',0)) not in (0,1):raise RecordError('context/sample bound')
        if not 0<=flags<=7 or (flags and not r.get('option_id',0)):raise RecordError('option flags need ID')
        if chosen < -1 or chosen>=K or teacher < -1 or teacher>=K:raise RecordError('selected/teacher bound')
        if source==0 and chosen<0:raise RecordError('direct policy has no selected action')
        if r.get('sampled',0) and (chosen<0 or source!=0):raise RecordError('only direct starts are policy samples')
        ids=np.asarray(r['id'])
        legal=np.asarray(r['legal'])
        feat=np.asarray(r['feat'],dtype=np.float32)
        logits=np.asarray(r['logits'],dtype=np.float32)
        if ids.shape!=(K,) or legal.shape!=(K,) or feat.shape!=(K,F) or logits.shape!=(K,):raise RecordError('array shape mismatch')
        if (K and ids.dtype.kind not in 'iu') or np.any(ids<0) or np.any(ids>=NO_ACTION) or (K>1 and np.any(ids[1:]<=ids[:-1])):raise RecordError('IDs must be canonical distinct stable actions')
        if not np.isin(legal,[0,1]).all():raise RecordError('mask must be binary')
        if chosen>=0 and (not legal[chosen] or int(r['selected_id'])!=int(ids[chosen])):raise RecordError('selected ID/mask mismatch')
        if teacher>=0 and not legal[teacher]:raise RecordError('teacher annotation is illegal')
        teacher_id=int(r.get('teacher_id',NO_ACTION))
        if not 0<=teacher_id<2**32:raise RecordError('teacher ID bound')
        if teacher>=0 and teacher_id!=int(ids[teacher]):raise RecordError('teacher annotation ID mismatch')
        if teacher<0 and teacher_id!=NO_ACTION and teacher_id in ids:raise RecordError('representable teacher requires explicit index')
        if not 0<=int(r.get('selected_id',NO_ACTION))<2**32:raise RecordError('selected ID bound')
        logp=float(r.get('logp',0))
        if not np.isfinite(logp) or logp>1e-5:raise RecordError('invalid behavior logp')
        if not np.isfinite(feat).all() or np.isnan(logits).any() or np.isposinf(logits).any() or not np.isfinite(logits[legal.astype(bool)]).all():raise RecordError('nonfinite model input/output')
        fuel=r.get('fuel',{})
        for key in ('candidate','observation','inference','log'):
            if not 0<=int(fuel.get(key,0))<2**32:raise RecordError('fuel bound')
    except (KeyError,TypeError,OverflowError) as e:
        raise RecordError(f'missing/invalid NFS2 field: {e}') from e

def encode_payload(r: dict) -> bytes:
    validate_record(r)
    kind=_numeric(r['kind'],KINDS)
    if kind==0:
        body=struct.pack('<I',len(r['raw']))+bytes(r['raw'])
    elif kind==2:
        body=EXECUTION.pack(r.get('executed_id',NO_ACTION),_numeric(r['outcome'],OUTCOMES),_numeric(r['source'],SOURCES),r.get('reason',0),r.get('option_id',0),r.get('action_fuel',0),r.get('log_fuel',0))
    else:
        fuel=r.get('fuel',{})
        body=DECISION.pack(r['head'],r['K'],r.get('F',F),r.get('chosen',-1),r.get('teacher',-1),r.get('context',0),int(r.get('sampled',0)),_numeric(r['source'],SOURCES),r.get('flags',0),r.get('reason',0),r.get('option_id',0),r.get('selected_id',NO_ACTION),r.get('teacher_id',NO_ACTION),r.get('logp',0),*[fuel.get(k,0) for k in ('candidate','observation','inference','log')])
        body+=np.asarray(r['id'],dtype='<u4').tobytes()+np.asarray(r['legal'],dtype='u1').tobytes()+np.asarray(r['logits'],dtype='<f4').tobytes()+np.asarray(r['feat'],dtype='<f4').tobytes()
    payload=HEADER.pack(MAGIC,VERSION,kind,HEADER.size+len(body)+4,r['obs_hash'],r['action_hash'],r['round'],r['champion'],r['snapshot'],r.get('decision_id',0))+body
    if len(payload)+4>MAX_PAYLOAD:raise RecordError('record too large')
    return payload+struct.pack('<I',checksum(payload))

def decode_payload(payload: bytes, *, expected_obs_hash=None,expected_action_hash=None) -> dict:
    if not HEADER.size+4<=len(payload)<=MAX_PAYLOAD:raise RecordError('payload bounds')
    magic,version,kind,size,obs,action,rnd,champ,snapshot,did=HEADER.unpack_from(payload)
    if magic!=MAGIC or version!=VERSION:raise RecordError('unsupported magic/version; NFS1 is separate')
    if kind not in KINDS or size!=len(payload):raise RecordError('kind/length mismatch')
    if checksum(payload[:-4])!=struct.unpack_from('<I',payload,len(payload)-4)[0]:raise RecordError('record checksum mismatch')
    if expected_obs_hash is not None and obs!=expected_obs_hash:raise RecordError('observation schema mismatch')
    if expected_action_hash is not None and action!=expected_action_hash:raise RecordError('action schema mismatch')
    r=dict(version=version,kind=KINDS[kind],obs_hash=obs,action_hash=action,round=rnd,champion=champ,snapshot=snapshot,decision_id=did)
    body=memoryview(payload)[HEADER.size:-4]
    if kind==0:
        if len(body)<4:raise RecordError('short context')
        n=struct.unpack_from('<I',body)[0]
        if n!=len(body)-4:raise RecordError('raw context length mismatch')
        r['raw']=bytes(body[4:])
    elif kind==2:
        if len(body)!=EXECUTION.size:raise RecordError('execution size')
        values=EXECUTION.unpack(body)
        r.update(zip(('executed_id','outcome','source','reason','option_id','action_fuel','log_fuel'),values))
    else:
        if len(body)<DECISION.size:raise RecordError('short decision')
        keys=('head','K','F','chosen','teacher','context','sampled','source','flags','reason','option_id','selected_id','teacher_id','logp','candidate_fuel','observation_fuel','inference_fuel','log_fuel')
        r.update(zip(keys,DECISION.unpack_from(body)))
        K=r['K'];f=r['F']
        if K>MAX_K or f!=F or len(body)!=DECISION.size+K*(9+4*F):raise RecordError('decision dimensions/size')
        off=DECISION.size
        def take(dtype,n):
            nonlocal off
            result=np.frombuffer(body,dtype=dtype,count=n,offset=off).copy();off+=result.nbytes;return result
        r['id']=take('<u4',K);r['legal']=take('u1',K);r['logits']=take('<f4',K);r['feat']=take('<f4',K*F).reshape(K,F)
        r['fuel']={k:r.pop(k+'_fuel') for k in ('candidate','observation','inference','log')}
    validate_record(r)
    return r

def encode_line(r: dict) -> str:
    return 'NFS2 '+base64.b64encode(encode_payload(r)).decode('ascii')+'\n'

def decode_line(line: str,**expected) -> dict:
    line=line.replace('\0','').strip()
    if not line.startswith('NFS2 '):raise RecordError('not an NFS2 line')
    encoded=line[5:]
    if len(encoded)>4*((MAX_PAYLOAD+2)//3):raise RecordError('base64 record bound')
    try:payload=base64.b64decode(encoded,validate=True)
    except (binascii.Error,ValueError) as e:raise RecordError('bad base64') from e
    return decode_payload(payload,**expected)

def decode_stdout(text: str, *, strict=True, stats=None, **expected) -> list[dict]:
    result=[]
    for line in text.replace('\0','').splitlines():
        if not line.startswith('NFS2 '):continue
        try:result.append(decode_line(line,**expected))
        except RecordError:
            if stats is not None:stats['invalid']=stats.get('invalid',0)+1
            if strict:raise
    return result

parse_text=decode_stdout
