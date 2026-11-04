"""Independent host-runtime stress audit using actual collected CL1 inputs.

No games or training started. This exercises scalar-host math, not WASM SIMD;
the latter still requires an engine parity test with the same input fixtures.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np
import torch
from rl_learner_1104.cl1 import CampPointer


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True)
    p.add_argument('--actor',required=True)
    p.add_argument('--raw',required=True)
    p.add_argument('--out',required=True)
    a=p.parse_args()
    source=Path(a.source).resolve();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    wrapper=out/'host.cpp'
    wrapper.write_text('#include "clrl_actor.h"\nextern "C" void jd_forward(const short* x,const float* h,int reset,float* logits,float* hn,unsigned* mask) { clrl_actor::Out o;clrl_actor::forward(x,h,reset!=0,o);*mask=0;for(int i=0;i<13;++i){logits[i]=o.logits[i];if(o.legal[i])*mask|=1u<<i;}for(int i=0;i<clrl_actor::kH;++i)hn[i]=o.h[i];}\n')
    library=out/'actor_host.dylib'
    subprocess.run(['clang++','-std=c++20','-O3','-shared','-fPIC','-I',str(source),str(wrapper),'-o',str(library)],check=True)
    lib=ctypes.CDLL(str(library.resolve()))
    fp=ctypes.POINTER(ctypes.c_float);sp=ctypes.POINTER(ctypes.c_int16)
    lib.jd_forward.argtypes=[sp,fp,ctypes.c_int,fp,fp,ctypes.POINTER(ctypes.c_uint)]
    spec=json.loads(Path(a.actor).read_text());actor=CampPointer(**spec.get('architecture',{})).eval()
    hidden_width=actor.memory.hidden_size
    actor.load_state_dict({k:torch.tensor(v['values']).reshape(v['shape']) for k,v in spec['tensors'].items()},strict=True)
    torch.set_num_threads(2)
    raw=np.fromfile(a.raw,dtype='<i2').reshape(-1,448)
    rng=np.random.default_rng(1104)
    selected=rng.choice(len(raw),1024,replace=True)
    x=np.ascontiguousarray(raw[selected]);h=rng.uniform(-1,1,(1024,hidden_width)).astype(np.float32)
    resets=rng.integers(0,2,1024).astype(bool)
    def native(row,hidden,reset):
        logits=np.empty(13,dtype=np.float32);hn=np.empty(hidden_width,dtype=np.float32);mask=ctypes.c_uint()
        lib.jd_forward(row.ctypes.data_as(sp),hidden.ctypes.data_as(fp),int(reset),logits.ctypes.data_as(fp),hn.ctypes.data_as(fp),ctypes.byref(mask))
        return logits,hn,mask.value
    with torch.no_grad():expected,eh=actor(torch.from_numpy(x),torch.from_numpy(h),torch.from_numpy(resets))
    max_logit=max_hidden=max_logp=0.;argmax_mismatches=mask_mismatches=0
    for i in range(len(x)):
        logits,hn,mask=native(x[i],h[i],resets[i]);want=expected[i].numpy();legal=np.isfinite(want)
        max_logit=max(max_logit,float(np.max(np.abs(logits[legal]-want[legal]))))
        max_hidden=max(max_hidden,float(np.max(np.abs(hn-eh[i].numpy()))))
        argmax_mismatches+=int(np.argmax(logits)!=np.argmax(want))
        mask_mismatches+=int(mask!=sum((1<<j) for j,v in enumerate(legal) if v))
        lp=torch.log_softmax(torch.from_numpy(logits),0);wp=torch.log_softmax(expected[i],0)
        max_logp=max(max_logp,float((lp[legal]-wp[legal]).abs().max()))
    # A long recurrent replay catches drift that unrelated hidden-state fixtures miss.
    th=actor.initial_state(1);ch=np.zeros(hidden_width,dtype=np.float32);drift=0.
    for i in range(min(512,len(raw))):
        row=np.ascontiguousarray(raw[i]);reset=(i==0 or i%127==0)
        with torch.no_grad():_,th=actor(torch.from_numpy(row[None]),th,torch.tensor([reset]))
        _,ch,_=native(row,ch,reset);drift=max(drift,float(np.max(np.abs(ch-th.numpy()[0]))))
    report=dict(kind='HOST_RUNTIME_PARITY_STRESS',cases=1024,recurrent_steps=512,
                source_actor_sha256=hashlib.sha256((source/'clrl_actor.h').read_bytes()).hexdigest(),
                max_logit_error=max_logit,max_hidden_error=max_hidden,max_logp_error=max_logp,
                max_recurrent_hidden_error=drift,argmax_mismatches=argmax_mismatches,mask_mismatches=mask_mismatches,
                ppo_logp_gate_pass=max_logp<=.0002,
                limits='Actual collected observations, random bounded hidden inputs; host scalar only, not WASM SIMD or game strength.')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if mask_mismatches or not report['ppo_logp_gate_pass']:raise SystemExit(1)


if __name__=='__main__':main()
