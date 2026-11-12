"""JNP2 TARGET-COMMAND rows, not physical execution rows or old CNG1 data."""
import math,struct,numpy as np

def f64(s):
 if len(s)!=16:raise ValueError('float64 bits')
 return struct.unpack('<d',int(s,16).to_bytes(8,'little'))[0]
def f32(s):
 if len(s)%8:raise ValueError('float32 bits')
 return np.array([int(s[i:i+8],16) for i in range(0,len(s),8)],np.uint32).view(np.float32)
def read(raw):
 rows=[];done={};seen=set();skips=np.zeros(4,np.int64)
 for line in raw.replace(b'\0',b'').splitlines():
  q=line.decode('utf-8','strict').split()
  if not q:continue
  if q[0]=='JNP2':
   if len(q)!=20:raise ValueError('truncated/extra JNP2 tokens')
   r=dict(zip(('round','slot','body','index','v92','reference','chosen','n','pub','h1_at','engine_round'),map(int,q[1:12])))
   n=r['n'];p=f64(q[12]);t=f32(q[13]);b=f32(q[14]);groups=list(bytes.fromhex(q[15]));mask=q[16];nat=f32(q[17]);h=np.frombuffer(bytes.fromhex(q[18]),dtype='<i2');ec=np.frombuffer(bytes.fromhex(q[19]),dtype='<i2')
   if not 0<=n<=10 or len(groups)!=n+1 or len(mask)!=n+1 or set(mask)-{'0','1'} or nat.shape!=(n+1,) or h.shape!=(64,) or ec.shape!=(n*16,) or t.shape!=(1,) or b.shape!=(1,):raise ValueError('JNP2 shape')
   if not np.isfinite(nat).all() or not 0<p<=1 or not t[0]>0 or not np.isfinite(b).all():raise ValueError('JNP2 probabilities/configuration')
   if not (0<=r['pub']<=r['round']<=r['engine_round'] and 0<=r['h1_at']<=r['engine_round']) or r['index']<1:raise ValueError('JNP2 context/identity')
   valid=np.zeros(11,bool);valid[:n]=[x=='1' for x in mask[:n]];valid[10]=mask[n]=='1'
   gp=groups[:n]+[-1]*(10-n)+[groups[n]]
   support=[gp[j] for j in range(11) if valid[j]]
   if len(support)!=len(set(support)) or r['v92'] not in support or r['chosen'] not in support:raise ValueError('noncanonical physical support')
   vslot=next(j for j in range(11) if valid[j] and gp[j]==r['v92']);action=next(j for j in range(11) if valid[j] and gp[j]==r['chosen'])
   camps=np.zeros((10,16),np.int16);camps[:n]=ec.reshape(n,16)
   present=np.zeros(10,bool);present[:n]=True
   native=np.full(11,-1e9,np.float32);native[:n]=nat[:n];native[10]=nat[n]
   r.update(probability=p,old_logp=math.log(p),temperature=float(t[0]),bonus=float(b[0]),groups=gp,valid=valid,vslot=vslot,action=action,h1=h,camps=camps,present=present,native_logits=native)
   key=r['body'],r['index']
   if key in seen:raise ValueError('replayed command')
   seen.add(key);rows.append(r)
  elif q[0]=='JND1':
   if len(q)!=5:raise ValueError('completion marker shape')
   body,index,rnd,fuel=map(int,q[1:]);key=body,index
   if key in done:raise ValueError('replayed completion')
   done[key]=(rnd,fuel)
  elif q[0]=='CNK':
   if len(q)!=8:raise ValueError('CNK shape')
   v=np.array(list(map(int,q[4:])),np.int64)
   if (v<0).any():raise ValueError('negative skip count')
   skips+=v
 for body in {r['body'] for r in rows}:
  ix=sorted(r['index'] for r in rows if r['body']==body)
  if ix!=list(range(1,len(ix)+1)):raise ValueError('missing command indices')
 missing=sorted(seen-set(done));extra=sorted(set(done)-seen)
 overruns=[(r['body'],r['index']) for r in rows if (r['body'],r['index']) in done and done[r['body'],r['index']][0]!=r['engine_round']]
 return rows,dict(missing_completion=missing,extra_completion=extra,logging_round_overruns=overruns,
  min_fuel_at_completion_marker=min([v[1] for v in done.values()],default=None),reported_skips=skips.tolist(),
  producer_markers_complete=not(missing or extra),action_semantics='sampled target command to frozen downstream executor, which may cancel/reassign; NOT executed action label')
