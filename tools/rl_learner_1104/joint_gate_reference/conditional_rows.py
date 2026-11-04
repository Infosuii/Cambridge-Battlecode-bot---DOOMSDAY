"""Strict parser for R1 0ea31bc CNG1 rows; rejects incomplete or ambiguous rows."""
import math,struct
import numpy as np

def f64(s):
    if len(s)!=16:raise ValueError('float64 length')
    return struct.unpack('<d',int(s,16).to_bytes(8,'little'))[0]
def f32s(s):
    if len(s)%8:raise ValueError('float32 length')
    return np.array([int(s[i:i+8],16) for i in range(0,len(s),8)],dtype=np.uint32).view(np.float32)
def parse(line):
    q=line.split()
    if not q or q[0]!='CNG1' or len(q)<12:raise ValueError('not complete CNG1')
    r=dict(zip(('round','slot','body','index','ref','chosen','v92','nn','invoke'),map(int,q[1:10])))
    if r['invoke'] not in (0,1) or r['index']<1 or r['round']<0:raise ValueError('invalid identity/branch')
    if len(q)!=(23 if r['invoke'] else 12):raise ValueError('unexpected/truncated tokens')
    a=f64(q[10]);g=f32s(q[11]);r.update(alpha=a,gate_inputs=g)
    if not 0<a<1 or g.shape!=(6,) or not np.isfinite(g).all():raise ValueError('invalid gate inputs/probability')
    if not r['invoke']:
        if r['chosen']!=r['ref']:raise ValueError('hold must execute reference')
        r['joint_logp']=math.log1p(-a);return r
    if q[12]!='Q':raise ValueError('missing conditional payload')
    n,pub,nu=map(int,q[13:16]);qc=f64(q[16])
    groups=list(bytes.fromhex(q[17]));mp=list(bytes.fromhex(q[18]));nat=f32s(q[19])
    x=np.frombuffer(bytes.fromhex(q[20]),dtype='<i2');ec=np.frombuffer(bytes.fromhex(q[21]),dtype='<i2');ft=np.frombuffer(bytes.fromhex(q[22]),dtype='<i2')
    if not 0<=n<=10 or not 1<=nu<=14 or len(groups)!=nu or len(set(groups))!=nu or len(mp)!=n+1 or max(mp)>=nu:
        raise ValueError('physical support shape')
    if nat.shape!=(n+1,) or x.shape!=(160,) or ec.shape!=(16*n,) or ft.shape!=(4*n,) or not np.isfinite(nat).all():
        raise ValueError('conditional feature shape')
    if pub>r['round'] or r['ref'] not in groups or r['chosen'] not in groups or not 0<qc<=1:
        raise ValueError('invalid chosen/reference/context/probability')
    if set(mp)!=set(range(nu)):raise ValueError('unrepresented physical group')
    # Pad camp slots to10; far is slot10, not the first padding slot.
    ctx=x.astype(np.float32)*np.float32(1/1024)
    camps=np.zeros((10,16),np.float32);camps[:n]=ec.reshape(n,16).astype(np.float32)*np.float32(1/1024)
    fields=ft.reshape(n,4).astype(np.int32);features=np.zeros((10,4),np.float32)
    features[:n,0]=np.where(fields[:,0]<0,256,np.minimum(fields[:,0],256)).astype(np.float32)*np.float32(1/32)
    features[:n,1:3]=np.clip(fields[:,1:3],0,8).astype(np.float32)*np.float32(.25)
    features[:n,3]=(fields[:,3]!=0).astype(np.float32)
    native=np.zeros(11,np.float32);native[:n]=nat[:n];native[10]=nat[n]
    valid=np.zeros(11,bool);valid[:n]=True;valid[10]=True
    mapping=np.zeros(11,np.int64);mapping[:n]=mp[:n];mapping[10]=mp[n]
    r.update(n=n,pub=pub,groups=groups,q_chosen=qc,action=groups.index(r['chosen']),
             context=ctx,camps=camps,features=features,native_logits=native,valid=valid,mapping=mapping,
             joint_logp=math.log(a)+math.log(qc))
    return r

def read(raw):
    rows=[];execution={};skips=np.zeros(4,np.int64);seen=set()
    for b in raw.replace(b'\0',b'\n').splitlines():
        line=b.decode('utf-8','strict')
        if line.startswith('CNG1 '):
            r=parse(line);key=(r['body'],r['index'])
            if key in seen:raise ValueError('replayed CNG1 identity')
            seen.add(key);rows.append(r)
        elif line.startswith('CNX3 '):
            q=line.split()
            if len(q)!=6:raise ValueError('CNX3 shape')
            rnd,slot,body,index,group=map(int,q[1:]);key=(body,index)
            if key in execution:raise ValueError('replayed CNX3')
            execution[key]=dict(round=rnd,slot=slot,group=group)
        elif line.startswith('CNK '):
            q=line.split()
            if len(q)!=8:raise ValueError('CNK shape')
            v=np.array(list(map(int,q[4:])),np.int64)
            if (v<0).any():raise ValueError('negative skips')
            skips+=v
    for body in {r['body'] for r in rows}:
        ix=sorted(r['index'] for r in rows if r['body']==body)
        if ix!=list(range(1,len(ix)+1)):raise ValueError('missing decision index')
    missing=[];reassigned=[]
    for r in rows:
        key=(r['body'],r['index']);e=execution.get(key)
        if e is None:missing.append(key)
        elif e['group']!=r['chosen'] or e['slot']!=r['slot'] or e['round']!=r['round']:reassigned.append(key)
    extra=sorted(set(execution)-seen)
    return rows,dict(missing_execution=missing,reassigned_execution=reassigned,extra_execution=extra,
                     reported_skips=skips.tolist(),execution_verified=not(missing or reassigned or extra),
                     caveat='Emitted row association alone does not establish producer completeness or unflushed final skip counts.')
