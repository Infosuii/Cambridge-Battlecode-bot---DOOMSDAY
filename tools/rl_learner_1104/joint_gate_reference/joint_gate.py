"""Conditional-compute learner math, not an integrated/benchmarked game policy."""
import torch
import torch.nn.functional as F

def joint_logp(gate_logits, invoke, action, conditional_logp):
    """conditional_logp contains ONLY invoked rows, in their original order.
    No expensive q distribution is required for a hold row. action is metadata:
    on hold the executor uses the fixed reference, even if invoke could choose it.
    """
    if invoke.dtype!=torch.bool or invoke.shape!=gate_logits.shape:raise ValueError('invalid gate choices')
    if conditional_logp.shape!=(int(invoke.sum()),):raise ValueError('missing/extra conditional rows')
    out=F.logsigmoid(-gate_logits)
    return out.index_copy(0,invoke.nonzero().flatten(),F.logsigmoid(gate_logits[invoke])+conditional_logp)

def collect(gate_logits,reference,expensive_policy,generator=None,allowed=None):
    """Reference sampler: expensive_policy receives ONLY indices that invoke.
    Resource-disallowed rows are deterministic reference with has_logp=False.
    Probability evaluator in training uses the logged latent gate flag.
    """
    if allowed is None:allowed=torch.ones_like(reference,dtype=torch.bool)
    if allowed.dtype!=torch.bool or allowed.shape!=reference.shape:raise ValueError('resource mask')
    active=allowed.nonzero().flatten()
    invoke=torch.zeros_like(allowed)
    invoke[active]=torch.rand(len(active),generator=generator,device=gate_logits.device)<gate_logits[active].sigmoid()
    ix=invoke.nonzero().flatten();action=reference.clone()
    if len(ix):
        q=expensive_policy(ix)
        if q.ndim!=2 or q.shape[0]!=len(ix) or not torch.isfinite(q).all() or (q<0).any():raise ValueError('conditional support')
        if not torch.allclose(q.sum(-1),torch.ones(len(ix),device=q.device,dtype=q.dtype)):raise ValueError('conditional mass')
        chosen=torch.multinomial(q,1,generator=generator).squeeze(1);action[ix]=chosen
        lp=q.gather(1,chosen[:,None]).squeeze(1).log()
    else:lp=gate_logits.new_empty((0,))
    # Disallowed rows have no stochastic likelihood, not a fabricated policy sample.
    logp=gate_logits.new_full(gate_logits.shape,float('nan'))
    selected_invoke=invoke[active]
    logp[active]=joint_logp(gate_logits[active],selected_invoke,action[active],lp)
    return dict(invoke=invoke,action=action,logp=logp,has_logp=allowed.clone())
