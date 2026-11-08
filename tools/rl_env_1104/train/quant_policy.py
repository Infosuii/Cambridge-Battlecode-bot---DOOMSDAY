"""Native-anchored straight-through policy updates for the quantized actor.

At collection weights the distribution is exactly the logged native policy.
For updates, float-logit differences supply a local differentiable surrogate.
This is not a claim of bit-exact new-weight quantized inference; frozen native
release games remain the strength test. Never erase faults or trajectory rows.
"""
import torch
import torch.nn.functional as F

def anchored(native_logits,current_float,old_float):
    return native_logits+(current_float-old_float)

def validate(native_logits,actions,logged_logp,temperature,tolerance=2e-4):
    if native_logits.ndim!=2 or native_logits.shape[1]!=11 or not torch.isfinite(native_logits).all():
        raise ValueError('Missing/non-finite native target logits')
    lp=F.log_softmax(native_logits/temperature,-1).gather(1,actions[:,None]).squeeze(1)
    error=(lp-logged_logp).abs()
    if not torch.isfinite(error).all() or float(error.max())>tolerance:
        raise ValueError('Native probability provenance mismatch: '+str(float(error.max())))
    return error
