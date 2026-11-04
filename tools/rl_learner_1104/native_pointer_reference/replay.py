"""Exact integer native pointer replay from consumed h1; no optimizer or strength claim."""
from pathlib import Path
import re,json,hashlib,numpy as np
r=Path(__file__).resolve().parents[1];src=r/'native-pointer-audit/bots/submission/src'
s=(src/'nn_weights.h').read_text()
def array(name):
 q=re.search(r'inline constexpr short '+re.escape(name)+r'\[\] = \{([^}]+)\}',s)
 if q is None:raise ValueError(name)
 return np.array([int(x) for x in q.group(1).split(',')],np.int64)
def dense(T,b,x):
 # Input-major, saturating Q15 rounded multiply, THEN saturating add for EACH input.
 T=T.reshape(x.shape[-1],-1);a=np.broadcast_to(b,(len(x),len(b))).copy()
 for i in range(x.shape[-1]):
  prod=np.clip((x[:,i,None]*T[i]+16384)>>15,-32768,32767)
  a=np.clip(a+prod,-32768,32767)
 return a
raw=(r/'runs/native-pointer-fields-A/team-a.stdout').read_bytes();rows=[];rejected=0
for b in raw.replace(b'\0',b'\n').splitlines():
 if not b.startswith(b'JDNATIVE '):continue
 q=b.decode().split()[1:]
 if len(q)!=281:rejected+=1;continue
 p=0
 def take(n,dtype=np.int64):
  global p
  z=np.array(q[p:p+n],dtype=dtype);p+=n;return z
 rnd,body,index,c0=take(4);h1=take(64);oldq=take(16);oldr=take(16);camp=take(170).reshape(10,17);logits=take(11,np.float32)
 rows.append(dict(round=int(rnd),body=int(body),index=int(index),c0=c0,h1=h1,q=oldq,r=oldr,camps=camp[:,1:],present=camp[:,0].astype(bool),logits=logits))
assert rows
h=np.stack([x['h1'] for x in rows]);q=dense(array('kP_target_qW_TQ'),array('kP_target_qbQ'),h)
rr=dense(array('kP_target_kWQ'),np.zeros(16,np.int64),q)
c0=(q*array('kP_target_kbQ')).sum(-1).astype(np.int32).astype(np.int64)
camps=np.stack([x['camps'] for x in rows]);mask=np.stack([x['present'] for x in rows])
z=(camps*rr[:,None,:]).sum(-1).astype(np.int32).astype(np.int64)+c0[:,None]
far=(rr*array('kP_target_EQ')).sum(-1).astype(np.int32).astype(np.int64)+c0
logits=np.concatenate((z,far[:,None]),-1).astype(np.float32)*np.float32(1/262144)
logits[:,:10]=np.where(mask,logits[:,:10],np.float32(-1e9))
qerr=int(np.max(np.abs(q-np.stack([x['q'] for x in rows]))));rerr=int(np.max(np.abs(rr-np.stack([x['r'] for x in rows]))));cerr=int(np.max(np.abs(c0-np.array([x['c0'] for x in rows]))));lerr=float(np.max(np.abs(logits-np.stack([x['logits'] for x in rows]))))
assert qerr==rerr==cerr==0 and lerr==0
report=dict(scope='Actual release native consumed-state pointer replay, NOT new policy/training/playing-strength evidence',
 rows=len(rows),bodies=len({x['body'] for x in rows}),rejected_incomplete_trace_lines=rejected,
 query_integer_max_error=qerr,folded_pointer_integer_max_error=rerr,bias_dot_integer_max_error=cerr,target_float32_logit_max_error=lerr,
 source_weight_header_sha256=hashlib.sha256((src/'nn_weights.h').read_bytes()).hexdigest(),
 diagnostic_wasm_sha256=hashlib.sha256((r/'native-pointer-audit/compiled.wasm').read_bytes()).hexdigest(),
 native_query_trainable_parameters=64*16+16,
 implications=['Can reproduce native target pointer exactly given consumed h1 and camp embeddings without reconstructing old incremental trunk history.',
 'This makes in-place target-query training plausible without adding a second inference network; no trained improvement established.',
 'Changing upstream trunk/encoder weights would invalidate frozen h1 assumptions and requires a larger consumed-state/replay contract.',
 'Training needs fresh stochastic chosen-action/likelihood and complete execution/episode data; these bounded diagnostic rows have no such training labels.',
 'Saturation and per-input rounding order matter; a plain float matrix multiply is not this deployed actor.'])
out=r.parent.parent/'outputs/rl-execution/NATIVE_POINTER_REPLAY.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
np.savez(r/'native_pointer_reference/consumed_inputs.npz',h1=h,camps=camps,present=mask,q=q,r=rr,c0=c0,logits=logits)
