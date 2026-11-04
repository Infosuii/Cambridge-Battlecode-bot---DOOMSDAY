"""Exact Q15 fast path with conservative fallback; opt-in, not active trial code.
A parallel prefix check proves that sequential add-saturation is inactive.
Unsafe batches retain the reference recurrence and its STE derivative.
"""
import torch
from qat_pointer import dense_q15 as reference_dense

def dense_q15(T,b,x):
    xx=x.to(torch.float64);ww=T.to(torch.float64);bb=b.to(torch.float64)
    raw=(xx[:,:,None]*ww[None,:,:]+16384)/32768
    rounded=raw+(raw.floor()-raw).detach()
    prod=rounded.clamp(-32768,32767)
    with torch.no_grad():
        prefix=prod.detach().cumsum(1)+bb.detach()[None,None,:]
        safe=bool(((prefix>=-32768)&(prefix<=32767)).all())
    if not safe:return reference_dense(T,b,x)
    return bb[None,:]+prod.sum(1)
