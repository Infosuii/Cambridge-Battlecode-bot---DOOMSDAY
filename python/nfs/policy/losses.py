"""Direct masked imitation/PPO math. Computes losses only; never runs an optimizer or learning job.

Callers must use NFS2 dataset masks: only acknowledged executed or explicitly defined guarded options enter PPO.
Continuation, argmax, missing ack, fallback and safety-override rows are excluded by that mask.
"""
from __future__ import annotations
import torch

def _zero(logits):return torch.where(torch.isfinite(logits),logits,torch.zeros_like(logits)).sum()*0

def masked_log_probs(logits,legal):
    if logits.ndim!=2 or legal.shape!=logits.shape:raise ValueError('logits/mask shape mismatch')
    if not bool(((legal==0)|(legal==1)).all()):raise ValueError('nonbinary legality mask')
    legal=legal.bool()
    if torch.isnan(logits).any() or torch.isposinf(logits).any() or not bool(torch.isfinite(logits[legal]).all()):raise ValueError('nonfinite legal logits')
    valid=legal.any(-1)
    if logits.shape[-1]==0:return logits,valid
    masked=logits.masked_fill(~legal,float('-inf'))
    safe=torch.where(valid[:,None],masked,torch.zeros_like(masked))
    return torch.log_softmax(safe,dim=-1).masked_fill(~legal,float('-inf')),valid

def selected_logp(logits,legal,chosen):
    lp,valid=masked_log_probs(logits,legal)
    if chosen.shape!=(len(logits),):raise ValueError('chosen shape')
    if not logits.shape[-1]:return logits.sum(-1),valid
    bounded=(chosen>=0)&(chosen<logits.shape[-1]);index=chosen.clamp(0,logits.shape[-1]-1)
    valid=valid&bounded&legal.bool().gather(1,index[:,None]).squeeze(1)
    out=torch.zeros_like(logits[:,0]);out[valid]=lp[valid,index[valid]]
    return out,valid

def imitation_loss(logits,legal,teacher,*,imitation_mask):
    logp,valid=selected_logp(logits,legal,teacher)
    if imitation_mask.shape!=valid.shape:raise ValueError('imitation eligibility shape')
    valid=valid&imitation_mask.bool()
    return (-logp[valid].mean() if valid.any() else _zero(logits)),dict(samples=int(valid.sum()))

def ppo_loss(logits,legal,chosen,old_logp,advantages,*,ppo_mask,clip_epsilon=.2,entropy_coefficient=0.0):
    if not 0<clip_epsilon<1:raise ValueError('clip epsilon')
    logp,valid=selected_logp(logits,legal,chosen)
    if any(x.shape!=valid.shape for x in (old_logp,advantages,ppo_mask)):raise ValueError('PPO vector shape')
    valid=valid&ppo_mask.bool()&torch.isfinite(old_logp)&torch.isfinite(advantages)
    if not valid.any():return _zero(logits),dict(samples=0,entropy=0.,approx_kl=0.,clip_fraction=0.)
    delta=logp[valid]-old_logp[valid];ratio=torch.exp(delta)
    # An overflow indicates an invalid/stale behavior pairing. Do not silently clip it into an apparently valid run.
    if not torch.isfinite(ratio).all():raise ValueError('nonfinite policy ratio')
    clipped=ratio.clamp(1-clip_epsilon,1+clip_epsilon)
    actor=-torch.minimum(ratio*advantages[valid],clipped*advantages[valid]).mean()
    lp,_=masked_log_probs(logits[valid],legal[valid]);mask=legal[valid].bool()
    safe_lp=torch.where(mask,lp,torch.zeros_like(lp));entropy=-(torch.exp(lp)*safe_lp).sum(-1).mean()
    loss=actor-entropy_coefficient*entropy
    return loss,dict(samples=int(valid.sum()),entropy=float(entropy.detach()),approx_kl=float(((ratio-1)-delta).mean().detach()),
        clip_fraction=float(((ratio-1).abs()>clip_epsilon).float().mean().detach()))

def critic_loss(values,returns,*,mask):
    if values.shape!=returns.shape or mask.shape!=values.shape:raise ValueError('critic target shape')
    valid=mask.bool()&torch.isfinite(values)&torch.isfinite(returns)
    return ((values[valid]-returns[valid]).square().mean() if valid.any() else _zero(values))

def smdp_returns(interval_rewards,gaps,*,gamma=.9997,bootstrap=0.):
    if len(interval_rewards)!=len(gaps) or not 0<gamma<=1:raise ValueError('SMDP shape/discount')
    if any(int(g)<1 for g in gaps):raise ValueError('strict positive decision intervals required')
    out=[];v=float(bootstrap)
    for reward,gap in reversed(list(zip(interval_rewards,gaps))):
        v=float(reward)+(gamma**int(gap))*v;out.append(v)
    return list(reversed(out))

def smdp_gae(interval_rewards,values,next_values,gaps,terminated,*,gamma=.9997,gae_lambda=.95):
    """Variable-duration option GAE, with independent streams supplied by the caller; no hidden state is mixed."""
    n=len(values)
    if any(len(x)!=n for x in (interval_rewards,next_values,gaps,terminated)) or not 0<gamma<=1 or not 0<=gae_lambda<=1:
        raise ValueError('SMDP GAE shapes/discount')
    if any(int(g)<1 for g in gaps):raise ValueError('strict positive decision intervals required')
    advantage=[0.]*n;carry=0.
    for i in reversed(range(n)):
        alive=0. if terminated[i] else 1.;discount=gamma**int(gaps[i])
        delta=float(interval_rewards[i])+alive*discount*float(next_values[i])-float(values[i])
        carry=delta+alive*((gamma*gae_lambda)**int(gaps[i]))*carry;advantage[i]=carry
    return advantage,[float(values[i])+advantage[i] for i in range(n)]
