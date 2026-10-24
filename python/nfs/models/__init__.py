"""PolicyNet: shared observation encoder + every learned head (agent B; CONTRACTS section 4).

Exactly the C++ forward pass of bot/src/nn_model.h (see that header and agents/B/REPORT.md "Numerics"):
  encoder  g = act(x_sg @ G1 + b); a_r = act(ally_r @ A1 + b), e_r = act(enemy_r @ E1 + b) (valid rows);
           h = act([g, mean(a), max(a), mean(e), max(e)] @ C1 + b)
  candidate u = b1 + h @ Wh + emb[context];  r_k = act(u + f_k @ Wf) @ w2 + b2;  logit_k = prior_k + R*act(r_k/R)
  value    y = act(b1 + h @ Wh) @ W2 + b2
  leaf     R * act(r / R) with r as for one candidate.
Weights are stored [in, out] (``x @ W``), exactly the C++ row-major blob order (``layout``).
``activation`` is the C++ rtanh. Matmul summation order differs from the sequential C++ order, so Torch agrees
within float tolerance; ``nfs.models.reference`` is the bit-exact numpy twin.
"""
from __future__ import annotations

import math

import numpy as np
import torch
from torch import nn

from .config import HEAD_NAMES, VALUE_OUTPUTS, load_config, resolve_config  # noqa: F401
from .rt import act_torch

__all__ = ['PolicyNet', 'build_model', 'activation', 'layout', 'segments', 'init_untrained', 'load_config',
           'resolve_config', 'HEAD_NAMES']


def activation(x):
    """The exact C++ activation (rtanh): clamp(x,-3,3); y = x(27+x^2)/(27+9x^2); clamp(y,-1,1)."""
    return act_torch(x)


def layout(cfg: dict) -> list[tuple[str, tuple[int, ...]]]:
    """Canonical parameter order of the exported f32 blob: encoder, then heads by id. Names are state_dict keys."""
    o, e = cfg['obs'], cfg['encoder']
    G, E, C = e['global_hidden'], e['entity_hidden'], e['ctx']
    out = [('enc.g1_w', (o['self_global_dim'], G)), ('enc.g1_b', (G,)),
           ('enc.a1_w', (o['ally_dim'], E)), ('enc.a1_b', (E,)),
           ('enc.e1_w', (o['enemy_dim'], E)), ('enc.e1_b', (E,)),
           ('enc.c1_w', (G + 4 * E, C)), ('enc.c1_b', (C,))]
    for h in cfg['heads']:
        p, H = f'heads.{h["name"]}.', h['hidden']
        if h['uses_ctx']:
            out.append((p + 'wh', (C, H)))
        if h['F']:
            out.append((p + 'wf', (h['F'], H)))
        if h['n_ctx']:
            out.append((p + 'emb', (h['n_ctx'], H)))
        out += [(p + 'b1', (H,)), (p + 'w2', (H, h['n_out'])), (p + 'b2', (h['n_out'],))]
    return out


def segments(cfg: dict) -> dict[str, tuple[int, int]]:
    """Float ranges [begin, end) of the encoder ('enc') and of every head (by name) in the blob."""
    seg, off = {}, 0
    for name, shape in layout(cfg):
        n = int(np.prod(shape))
        key = 'enc' if name.startswith('enc.') else name.split('.')[1]
        b, _ = seg.get(key, (off, off))
        seg[key] = (b, off + n)
        off += n
    return seg


class PolicyNet(nn.Module):
    """Shared encoder + every head; dims from a resolved config (``nfs.models.load_config``)."""

    def __init__(self, cfg: dict):
        super().__init__()
        if 'heads' not in cfg or isinstance(cfg['heads'], dict):
            raise ValueError('PolicyNet needs a resolved config (nfs.models.load_config / resolve_config)')
        self.cfg = cfg
        self.head_cfg = {h['name']: h for h in cfg['heads']}
        self.enc = nn.ParameterDict()
        self.heads = nn.ModuleDict({h['name']: nn.ParameterDict() for h in cfg['heads']})
        for name, shape in layout(cfg):
            p = nn.Parameter(torch.zeros(shape, dtype=torch.float32))
            if name.startswith('enc.'):
                self.enc[name[4:]] = p
            else:
                _, head, key = name.split('.')
                self.heads[head][key] = p
        o = cfg['obs']
        self.S, self.Ra, self.Da, self.Re, self.De = (o['self_global_dim'], o['ally_rows'], o['ally_dim'],
                                                       o['enemy_rows'], o['enemy_dim'])
        self.obs_dim = o['obs_dim']

    # ------------------------------------------------------------------ encoder
    def _pool(self, rows, mask, w, b):
        a = activation(rows @ w + b)                                    # [B, R, E]
        m = mask > 0.5                                                  # [B, R]
        n = m.sum(dim=1, keepdim=True)                                  # [B, 1]
        mf = m.unsqueeze(-1).to(a.dtype)
        mean = (a * mf).sum(dim=1) / n.clamp(min=1).to(a.dtype)
        mx = a.masked_fill(~m.unsqueeze(-1), float('-inf')).amax(dim=1) if a.shape[1] else a.sum(dim=1)
        mx = torch.where(n > 0, mx, torch.zeros_like(mx))
        return mean, mx

    def encode(self, obs):
        """obs [B, kObsDim] float32 -> h [B, ctx]."""
        S, Ra, Da, Re, De = self.S, self.Ra, self.Da, self.Re, self.De
        B = obs.shape[0]
        i = 0
        sg = obs[:, i:i + S]; i += S
        ally = obs[:, i:i + Ra * Da].reshape(B, Ra, Da); i += Ra * Da
        amask = obs[:, i:i + Ra]; i += Ra
        enemy = obs[:, i:i + Re * De].reshape(B, Re, De); i += Re * De
        emask = obs[:, i:i + Re]
        e = self.enc
        g = activation(sg @ e['g1_w'] + e['g1_b'])
        am, ax = self._pool(ally, amask, e['a1_w'], e['a1_b'])
        em, ex = self._pool(enemy, emask, e['e1_w'], e['e1_b'])
        return activation(torch.cat([g, am, ax, em, ex], dim=1) @ e['c1_w'] + e['c1_b'])

    # ------------------------------------------------------------------ heads
    def _pre(self, name, h, context, batch):
        p, hc = self.heads[name], self.head_cfg[name]
        u = p['b1'].expand(batch, -1)
        if hc['uses_ctx']:
            u = u + h @ p['wh']
        if hc['n_ctx']:
            ctx = torch.zeros(batch, dtype=torch.long, device=u.device) if context is None else context.long()
            u = u + p['emb'][ctx]
        return u

    def head_residual(self, head, h, feat, context=None):
        """Raw residual r [B, K] (before the bound)."""
        p, hc = self.heads[head], self.head_cfg[head]
        u = self._pre(head, h, context, feat.shape[0])                  # [B, H]
        z = activation(u.unsqueeze(1) + feat @ p['wf'])                 # [B, K, H]
        return (z @ p['w2']).squeeze(-1) + p['b2']

    def head_logits(self, head, h, feat, legal, prior, context=None):
        """feat [B,K,F], legal [B,K] bool, prior [B,K] -> logits [B,K]; illegal = -inf.
        `context` (optional, [B] long) is the call-site context code (Decision::context); default 0."""
        hc = self.head_cfg[head]
        if hc['kind'] != 'candidate':
            raise ValueError(f'{head} is not a candidate head')
        R = float(hc['R'])
        r = self.head_residual(head, h, feat, context)
        logits = prior + R * activation(r / R)
        return logits.masked_fill(~legal.bool(), float('-inf'))

    def _value(self, name, h):
        p = self.heads[name]
        return activation(self._pre(name, h, None, h.shape[0])) @ p['w2'] + p['b2']

    def values(self, h) -> dict:
        y = self._value('value', h)
        return {k: y[:, i] for i, k in enumerate(self.cfg.get('value_outputs', VALUE_OUTPUTS))}

    def belief(self, h):
        """[B, n_sectors] logits."""
        return self._value('belief', h)

    def leaf(self, h, feat, context=None):
        """ts_leaf bounded residual [B] for feat [B, F]."""
        R = float(self.head_cfg['ts_leaf']['R'])
        r = self.head_residual('ts_leaf', h, feat.unsqueeze(1), context).squeeze(1)
        return R * activation(r / R)


def build_model(cfg: dict) -> PolicyNet:
    if 'heads' in cfg and isinstance(cfg['heads'], list):
        return PolicyNet(cfg)
    return PolicyNet(resolve_config(cfg))


@torch.no_grad()
def init_untrained(model: PolicyNet, seed: int, zero_residual: bool = True) -> PolicyNet:
    """Synthetic, seeded, UNTRAINED initialisation (no data involved).

    Weights ~ U(-1/sqrt(fan_in), 1/sqrt(fan_in)), biases 0, context embeddings U(-0.1, 0.1).
    zero_residual=True zeroes the residual output layer (w2, b2) of every candidate and leaf head, so every logit equals
    its teacher prior and every leaf residual is 0 (teacher-neutral by construction). Value/belief heads stay random.
    """
    g = torch.Generator().manual_seed(int(seed))
    for name, _ in layout(model.cfg):
        p = model.state_dict()[name]
        if name.endswith('_b') or name.endswith('.b1') or name.endswith('.b2'):
            p.zero_()
        elif name.endswith('.emb'):
            p.copy_((torch.rand(p.shape, generator=g) * 2 - 1) * 0.1)
        else:
            bound = 1.0 / math.sqrt(p.shape[0])
            p.copy_((torch.rand(p.shape, generator=g) * 2 - 1) * bound)
    if zero_residual:
        for h in model.cfg['heads']:
            if h['kind'] in ('candidate', 'leaf'):
                model.heads[h['name']]['w2'].zero_()
                model.heads[h['name']]['b2'].zero_()
    return model
