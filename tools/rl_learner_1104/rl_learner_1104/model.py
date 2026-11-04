"""Schema-configured recurrent actor and separate centralized critic.

Learner core only: no engine adapter or deployable WASM is implied. Entity inputs
must already exclude identifiers and privileged state. Schema is explicit; no
automatic loading of Agent2 layout2/layout4 checkpoints is supported.
"""
import torch
from torch import nn
from torch.distributions import Categorical


def masked_distribution(logits, legal):
    if legal.dtype != torch.bool or legal.shape != logits.shape:
        raise ValueError("legal mask must be bool and match logits")
    if not legal.any(-1).all():
        raise ValueError("every decision needs at least one legal action")
    return Categorical(logits=logits.masked_fill(~legal, -torch.inf))


class Actor(nn.Module):
    def __init__(self, entity_widths, global_width, belief_width, heads,
                 enc_width=8, context_width=32, memory_width=16):
        super().__init__()
        self.names = tuple(sorted(entity_widths))
        self.encoders = nn.ModuleDict({
            k: nn.Sequential(nn.Linear(entity_widths[k], enc_width), nn.ReLU())
            for k in self.names})
        self.context = nn.Sequential(nn.Linear(
            2 * enc_width * len(self.names) + global_width + belief_width,
            context_width), nn.ReLU())
        self.memory = nn.GRUCell(context_width, memory_width)
        # Heads are evaluated conditionally by the executor: later heads receive
        # updated observations/masks after earlier SDK outcomes. This module does
        # not pretend all joint actions are simultaneously legal.
        self.heads = nn.ModuleDict({k: nn.Linear(memory_width, n) for k, n in heads.items()})
        self.memory_width = memory_width

    def forward(self, entities, present, globals_, beliefs, hidden, reset):
        parts = []
        for name in self.names:
            x, mask = entities[name], present[name]
            if mask.dtype != torch.bool or mask.shape != x.shape[:-1]:
                raise ValueError("presence mask shape/type mismatch")
            # Remove absent rows before encoding, including sentinel/NaN padding.
            z = self.encoders[name](x.masked_fill(~mask.unsqueeze(-1), 0))
            count = mask.sum(1, keepdim=True)
            mean = (z * mask.unsqueeze(-1)).sum(1) / count.clamp_min(1)
            maximum = z.masked_fill(~mask.unsqueeze(-1), -torch.inf).max(1).values
            maximum = torch.where(count > 0, maximum, torch.zeros_like(maximum))
            parts.extend((mean, maximum))
        context = self.context(torch.cat(parts + [globals_, beliefs], -1))
        h = self.memory(context, hidden * (~reset.bool()).unsqueeze(-1))
        return {k: head(h) for k, head in self.heads.items()}, h

    def initial_state(self, batch, device=None):
        p = next(self.parameters())
        return torch.zeros(batch, self.memory_width, device=device or p.device, dtype=p.dtype)


class Critic(nn.Module):
    """Separate parameters ensure privileged features cannot enter actor export."""
    def __init__(self, state_width, width=64):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(state_width, width), nn.Tanh(),
                                 nn.Linear(width, width), nn.Tanh(), nn.Linear(width, 1))

    def forward(self, privileged_state):
        return self.net(privileged_state).squeeze(-1)


def joint_statistics(logits, masks, actions, active):
    """Sum conditional log probabilities only over executed active heads.

    Caller must supply logits/masks for each head's actual conditional state.
    Inactive heads may have all-false masks and placeholder action -1.
    """
    first = next(iter(logits.values()))
    logp = first.new_zeros(first.shape[0])
    entropy = logp.clone()
    for name, scores in logits.items():
        selected = active[name].bool()
        if selected.any():
            d = masked_distribution(scores[selected], masks[name][selected])
            chosen = actions[name][selected]
            if not masks[name][selected].gather(1, chosen[:, None]).all():
                raise ValueError("logged action is illegal")
            logp[selected] += d.log_prob(chosen)
            entropy[selected] += d.entropy()
    return logp, entropy


def ppo_loss(new_logp, old_logp, advantages, value, returns, entropy,
             clip=0.2, value_weight=0.5, entropy_weight=0.003):
    """Caller handles recurrent sequence replay/burn-in and valid padding rows."""
    if any(t.requires_grad for t in (old_logp, advantages, returns)):
        raise ValueError("rollout targets must be detached")
    if not all(torch.isfinite(t).all() for t in
               (new_logp, old_logp, advantages, value, returns, entropy)):
        raise ValueError("nonfinite PPO input")
    ratio = (new_logp - old_logp).exp()
    policy = -torch.minimum(ratio * advantages,
                            ratio.clamp(1 - clip, 1 + clip) * advantages).mean()
    value_loss = (value - returns).square().mean()
    return policy + value_weight * value_loss - entropy_weight * entropy.mean()
