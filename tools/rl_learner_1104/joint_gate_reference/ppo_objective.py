"""Joint-route PPO objective for a conditional actor; no game-data adapter.

Call only with ALL admitted stochastic gate rows from validated complete games.
Resource-masked deterministic decisions are excluded. Conditional logp entries
exist ONLY for invoked rows, in gate-row order. No q inference on hold is needed.
"""
import torch
import torch.nn.functional as F
from joint_gate import joint_logp


def objective(gate_logits, invoke, conditional_logp, old_logp, returns, games,
              clip=.1, gate_entropy_coefficient=.003):
    if games < 1 or not 0 < clip < 1:
        raise ValueError('invalid games/clip')
    if gate_logits.ndim != 1 or len(gate_logits) == 0:
        raise ValueError('empty or nonvector stochastic batch')
    for x in (old_logp, returns):
        if x.shape != gate_logits.shape or not torch.isfinite(x).all():
            raise ValueError('invalid likelihood/return rows')
    if old_logp.requires_grad or returns.requires_grad:
        raise ValueError('behavior likelihoods and returns must be detached')
    if not torch.isfinite(gate_logits).all() or not torch.isfinite(conditional_logp).all():
        raise ValueError('nonfinite new policy')
    if (old_logp > 1e-6).any() or (conditional_logp > 1e-6).any():
        raise ValueError('log probabilities cannot be positive')
    lp = joint_logp(gate_logits, invoke, None, conditional_logp)
    log_ratio = lp - old_logp
    ratio = log_ratio.exp()
    if not torch.isfinite(ratio).all():
        raise ValueError('nonfinite importance ratios')
    clipped = ratio.clamp(1-clip, 1+clip)
    surrogate = torch.minimum(ratio*returns, clipped*returns)
    # Exact Bernoulli entropy at each visited state. This explicitly excludes
    # conditional-q entropy; q is unavailable on holds. No fabricated full entropy.
    alpha = gate_logits.sigmoid()
    gate_entropy = -(alpha*F.logsigmoid(gate_logits) + (1-alpha)*F.logsigmoid(-gate_logits))
    loss = -(surrogate + gate_entropy_coefficient*gate_entropy).sum()/games
    with torch.no_grad():
        diagnostics = dict(
            rows=len(lp), invoked=int(invoke.sum()),
            mean_gate_probability=alpha.mean().item(),
            mean_gate_entropy=gate_entropy.mean().item(),
            clip_fraction=((ratio-1).abs() > clip).float().mean().item(),
            sampled_joint_kl_log=(old_logp-lp).mean().item(),
            sampled_joint_kl_k3=(torch.expm1(log_ratio)-log_ratio).mean().item(),
            max_sampled_logp_change=log_ratio.abs().max().item())
    return loss, diagnostics


def exact_gate_kl(old_logits, new_logits):
    """Exact Bernoulli old||new at logged states, NOT full joint/physical KL."""
    a = old_logits.sigmoid()
    return a*(F.logsigmoid(old_logits)-F.logsigmoid(new_logits)) + (1-a)*(F.logsigmoid(-old_logits)-F.logsigmoid(-new_logits))
