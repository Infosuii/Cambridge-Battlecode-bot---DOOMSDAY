"""Dimension-checked exact-float32 C++ export for original or compact CL1 actor."""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def literal(v):
    v=struct.unpack('<f',struct.pack('<f',v))[0]
    if v!=v or v in (float('inf'),float('-inf')):raise ValueError('nonfinite tensor')
    return v.hex()+'f'


def main():
    p=argparse.ArgumentParser();p.add_argument('actor');p.add_argument('out');a=p.parse_args()
    raw=Path(a.actor).read_bytes();j=json.loads(raw);sha=hashlib.sha256(raw).hexdigest()
    if j['format']!='jd-cl1-pointer-f32-v1' or j['preprocess']!='jd-cl1-af91-v1':raise ValueError('wrong format')
    arch=j.get('architecture',dict(enc_width=8,context_width=32,memory_width=16,pointer_width=16))
    e,c,h,pw=[arch[k] for k in ('enc_width','context_width','memory_width','pointer_width')]
    if any(v%4 or not 4<=v<=48 for v in (e,c,h,pw)) or 3*h>48:raise ValueError('unsupported SIMD dimensions')
    if j['hidden']!=h or j['pool_order']!=['ally','altar','camp','enemy']:raise ValueError('ABI mismatch')
    dims={}
    for name,w in [('ally',20),('altar',4),('camp',19),('enemy',23)]:
        dims[f'encoders.{name}.weight']=(f'enc_{name}_w',[e,w])
        dims[f'encoders.{name}.bias']=(f'enc_{name}_b',[e])
    dims.update({'context.weight':('ctx_w',[c,58+8*e]),'context.bias':('ctx_b',[c]),
                 'memory.weight_ih':('gru_wih',[3*h,c]),'memory.weight_hh':('gru_whh',[3*h,h]),
                 'memory.bias_ih':('gru_bih',[3*h]),'memory.bias_hh':('gru_bhh',[3*h]),
                 'pointer.weight':('ptr_w',[pw,e+h]),'pointer.bias':('ptr_b',[pw]),
                 'score.weight':('score_w',[1,pw]),'score.bias':('score_b',[1]),
                 'none.weight':('none_w',[1,h]),'none.bias':('none_b',[1])})
    if set(dims)!=set(j['tensors']):raise ValueError('unexpected tensor set')
    lines=['#pragma once','// Exact float32 runtime weights; training provenance is in actor.json.','namespace clrl_w {',
           f'inline constexpr char kActorSha256[]="{sha}";',
           f'inline constexpr int kEnc={e}, kContext={c}, kHidden={h}, kPointer={pw};']
    def array(name,values):return 'inline constexpr float '+name+'[]={'+','.join(literal(v) for v in values)+'};'
    for key,(name,shape) in dims.items():
        t=j['tensors'][key]
        if t['shape']!=shape:raise ValueError('tensor shape mismatch: '+key)
        values=t['values']
        if len(values)!=__import__('math').prod(shape):raise ValueError('tensor length mismatch')
        lines.append(array(name,values))
        if len(shape)==2 and shape[0]>1:
            nout,nin=shape;lines.append(array(name+'t',[values[o*nin+i] for i in range(nin) for o in range(nout)]))
    lines.append('}')
    Path(a.out).write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(actor_sha256=sha,architecture=arch,header=a.out)))


if __name__=='__main__':main()
