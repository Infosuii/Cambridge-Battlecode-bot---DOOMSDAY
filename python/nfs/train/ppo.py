"""On-policy PPO with the exact runtime decision semantics.

Runtime (CONTRACTS 3.2): logit_k = prior_k + R * tanh(r_k / R) for legal k, -inf otherwise; candidate 0 = teacher;
`active` heads in the `training` profile SAMPLE from softmax(logits) and log logp_behaviour of the executed choice;
deployment takes the argmax (ties -> lowest index -> teacher). `shadow` records always execute the teacher.

Which records enter the probability ratio (`ratio_mask`): kind=decision, mode=active, sampled=1, reason=ok,
K>0, chosen legal, finite logp, observation present (if the head uses shared context) and not a forced step.
Everything else (fallbacks, budget skips, shadow, deterministic argmax decisions) still contributes its reward to the
stream but is never treated as a stochastic policy action.

Multi-turn commitments (e.g. an objective kept for up to 40 rounds) - `commitment_mode`:
- 'option' (default): the runtime logs ONE decision when an option starts; the forced continuation steps are not
  decisions. The interval reward R_i is the discounted sum over the option's rounds and bootstrapping uses
  gamma^tau_i with tau_i = rounds until the stream's next decision (SMDP). If forced-step records exist
  (reason in `forced_reasons`) they are merged into the preceding option: R <- R_i + gamma^tau_i R_{i+1},
  tau <- tau_i + tau_{i+1}, exactly preserving discounting.
- 'exclude_forced': forced-step records stay as separate SMDP steps for the critic/GAE but are masked out of the
  ratio, entropy and KL (their behaviour probability is 1 for the committed choice, not the policy's).
Streams: one per (match, side, champion, head) - agents and heads never share GAE recursions.
GAE with variable gaps: delta_i = R_i + gamma^tau_i (1-done_i) V_{i+1} - V_i,
                        A_i = delta_i + gamma^tau_i * lambda * (1-done_i) A_{i+1}   (lambda per decision step).
"""
from __future__ import annotations

import inspect
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import torch
from torch import nn

from .auth import require_authorization
from .common import Deadline

ROOT = Path(__file__).resolve().parents[3]
MODE_OFF, MODE_SHADOW, MODE_ACTIVE = 0, 1, 2
NEG_INF = float('-inf')


class PolicyParityError(RuntimeError):
    """Torch log-probabilities disagree with the behaviour log-probabilities logged by the C++ runtime."""


def head_names() -> dict[int, str]:
    d = json.loads((ROOT / 'schemas/heads.json').read_text(encoding='utf-8'))
    return {h['id']: h['name'] for h in d['heads']}


def reason_codes() -> dict:
    """Reason enum: B's nfs.records exports it when available; otherwise 0 = ok and everything else = fallback."""
    try:
        import nfs.records as rec  # noqa: WPS433 - B-owned, optional
        for n in ('REASONS', 'REASON_NAMES', 'Reason'):
            v = getattr(rec, n, None)
            if isinstance(v, dict):
                return {int(k): str(val) for k, val in v.items()}
            if v is not None and hasattr(v, '__members__'):
                return {int(m.value): name for name, m in v.__members__.items()}
    except ImportError:
        pass
    hdr = ROOT / 'bot/src/nn_head.h'                       # B's enum: kReasonName[...] = {"ok", ...}
    if hdr.exists():
        import re
        m = re.search(r'kReasonName\[[^\]]*\]\s*=\s*\{([^}]*)\}', hdr.read_text(encoding='utf-8'))
        if m:
            return dict(enumerate(re.findall(r'"([^"]+)"', m[1])))
    return {0: 'ok'}


def runtime_logits_reference(prior, residual, legal, R: float):
    """Reference implementation of the C++ logit formula (torch or numpy)."""
    if isinstance(prior, np.ndarray):
        z = prior + R * np.tanh(residual / R)
        return np.where(legal.astype(bool), z, -np.inf)
    z = prior + R * torch.tanh(residual / R)
    return z.masked_fill(~legal.bool(), NEG_INF)


def call_head_logits(model, head: str, h, feat, legal, prior, context=None):
    """PolicyNet.head_logits with the runtime call-site context code when the model accepts it (B's PolicyNet takes
    an optional `context`). The record feature width must equal the model's head width (schema mismatch otherwise)."""
    hc = getattr(model, 'head_cfg', {}).get(head)
    if hc is not None and hc.get('F') is not None and feat.shape[-1] != int(hc['F']):
        if feat.shape[-1] > int(hc['F']) or not getattr(model, 'allow_feature_padding', False):
            raise ValueError(f'{head}: record feature width {feat.shape[-1]} != model F {hc["F"]} (schema mismatch)')
    try:
        accepts = model.__dict__.setdefault('_nfs_ctx_kw', 'context' in inspect.signature(model.head_logits).parameters)
    except (TypeError, ValueError):
        accepts = False
    if accepts and context is not None:
        return model.head_logits(head, h, feat, legal, prior, context=context)
    return model.head_logits(head, h, feat, legal, prior)


def masked_log_softmax(logits: torch.Tensor) -> torch.Tensor:
    finite = torch.isfinite(logits)
    safe = torch.where(finite, logits, torch.full_like(logits, -1e30))
    out = safe - torch.logsumexp(safe, -1, keepdim=True)
    return torch.where(finite, out, torch.full_like(out, NEG_INF))


def masked_entropy(logp: torch.Tensor) -> torch.Tensor:
    p = logp.exp()
    return -(torch.where(torch.isfinite(logp), p * logp, torch.zeros_like(logp))).sum(-1)


@dataclass
class PPOConfig:
    gamma: float = 0.9997
    lam: float = 0.95
    clip: float = 0.2
    epochs: int = 4
    minibatch: int = 512
    lr: float = 1e-4
    critic_lr: float = 3e-4
    ent_coef: float = 0.003
    vf_coef: float = 0.5
    max_grad_norm: float = 0.5
    target_kl: float = 0.02            # stop the update when approx KL > 1.5 * target_kl
    parity_tol: float = 2e-3
    commitment_mode: str = 'option'    # 'option' | 'exclude_forced'
    forced_reasons: tuple = ()         # reason codes marking forced continuation steps (runtime-defined)
    budget_reasons: tuple = (3,)       # nn_head.h Reason::kBudget
    heads: tuple = ()                  # head names to optimise (empty = all present)
    head_weights: dict = field(default_factory=dict)   # per-head actor-loss weights (0 = ablated)
    teacher_kl_coef: float = 0.0       # optional KL(pi || softmax(prior)) anchor to the teacher prior
    normalize_adv: bool = True
    device: str = 'auto'


# --------------------------------------------------------------------------------------------- streams and GAE
def merge_forced(rows: list[dict], gamma: float, forced: set) -> list[dict]:
    """Option semantics: fold forced continuation steps into the preceding logged option (exact discounting)."""
    out = []
    for r in rows:
        if out and r['reason'] in forced:
            o = out[-1]
            o['reward'] = o['reward'] + (gamma ** o['tau']) * r['reward']
            o['tau'] = o['tau'] + r['tau']
            o['done'] = r['done']
            o['merged'] = o.get('merged', 0) + 1
        else:
            out.append(dict(r))
    return out


def gae(rewards, values, taus, dones, gamma: float, lam: float, bootstrap: float = 0.0):
    """Generalised advantage estimation over one SMDP stream with variable gaps."""
    n = len(rewards)
    adv = np.zeros(n, np.float64)
    nxt_v, nxt_a = bootstrap, 0.0
    for i in reversed(range(n)):
        disc = gamma ** float(taus[i]) * (1.0 - float(dones[i]))
        delta = rewards[i] + disc * nxt_v - values[i]
        nxt_a = delta + disc * lam * nxt_a
        adv[i] = nxt_a
        nxt_v = values[i]
    return adv, adv + np.asarray(values, np.float64)


def streams_from_shard(shard, cfg: PPOConfig) -> list[list[int]]:
    m = shard.meta
    key = defaultdict(list)
    for i in range(len(shard)):
        key[(int(m['match_index'][i]), int(m['side'][i]), int(m['champion'][i]), int(shard.inputs['head'][i]))].append(i)
    return [sorted(v, key=lambda i: (int(m['round'][i]), int(m['seq'][i]))) for _, v in sorted(key.items())]


# --------------------------------------------------------------------------------------------- batch
@dataclass
class Batch:
    obs: torch.Tensor
    obs_valid: torch.Tensor
    feat: torch.Tensor
    legal: torch.Tensor
    prior: torch.Tensor
    K: torch.Tensor
    F: torch.Tensor
    head: torch.Tensor
    context: torch.Tensor
    chosen: torch.Tensor
    logp_b: torch.Tensor
    logit_b: torch.Tensor
    ratio_mask: torch.Tensor
    adv: torch.Tensor
    ret: torch.Tensor
    old_v: torch.Tensor
    value_mask: torch.Tensor
    stats: dict

    def __len__(self):
        return len(self.chosen)


def ratio_mask_np(shard, cfg: PPOConfig) -> tuple[np.ndarray, dict]:
    i, t, m = shard.inputs, shard.targets, shard.meta
    K = i['K'].astype(int)
    chosen = t['chosen'].astype(int)
    rows = np.arange(len(shard))
    in_range = (chosen >= 0) & (chosen < np.maximum(K, 1))
    legal_chosen = np.zeros(len(shard), bool)
    legal_chosen[in_range] = i['legal'][rows[in_range], chosen[in_range]]
    forced = np.isin(m['reason'], list(cfg.forced_reasons)) if cfg.forced_reasons else np.zeros(len(shard), bool)
    budget = np.isin(m['reason'], list(cfg.budget_reasons)) if cfg.budget_reasons else np.zeros(len(shard), bool)
    names = head_names()
    allowed = np.ones(len(shard), bool)
    index = json.loads((ROOT / 'schemas/heads.json').read_text(encoding='utf-8'))['heads']
    requires_obs = np.isin(i['head'], [h['id'] for h in index if h.get('uses_shared_context', True)])
    if cfg.heads:
        allowed = np.isin(i['head'], [k for k, v in names.items() if v in cfg.heads])
    mask = ((m['mode'] == MODE_ACTIVE) & (m['sampled'] == 1) & (m['reason'] == 0) & (K > 0) & legal_chosen
            & np.isfinite(t['logp_behaviour']) & ((i['obs_valid'] == 1) | ~requires_obs) & ~forced & allowed)
    n = max(1, len(shard))
    stats = dict(rows=len(shard), ratio_rows=int(mask.sum()),
                 invalid_action_rate=float((~legal_chosen & (K > 0)).sum() / n),
                 fallback_rate=float((m['reason'] != 0).sum() / n), budget_skip_rate=float(budget.sum() / n),
                 forced_rate=float(forced.sum() / n), shadow_rate=float((m['mode'] == MODE_SHADOW).sum() / n),
                 deterministic_active_rate=float(((m['mode'] == MODE_ACTIVE) & (m['sampled'] == 0)).sum() / n),
                 missing_obs_rate=float(((i['obs_valid'] == 0) & requires_obs).sum() / n),
                 reason_counts={reason_codes().get(int(k), f'reason_{int(k)}'): int(v)
                                for k, v in zip(*np.unique(m['reason'], return_counts=True))})
    return mask, stats


def compute_advantages(shard, critic, cfg: PPOConfig, dev) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    with torch.no_grad():
        v = critic(torch.as_tensor(shard.inputs['obs'], device=dev).float(),
                   torch.as_tensor(shard.inputs['head'], device=dev)).cpu().numpy().astype(np.float64)
    adv = np.zeros(len(shard)); ret = np.zeros(len(shard))
    forced = set(cfg.forced_reasons)
    merged = 0
    t, m = shard.targets, shard.meta
    for idxs in streams_from_shard(shard, cfg):
        rows = [dict(i=i, reward=float(t['reward'][i]), tau=float(t['tau'][i]), done=float(t['done'][i]),
                     reason=int(m['reason'][i])) for i in idxs]
        if cfg.commitment_mode == 'option' and forced:
            rows = merge_forced(rows, cfg.gamma, forced)
            merged += len(idxs) - len(rows)
        elif cfg.commitment_mode not in ('option', 'exclude_forced'):
            raise ValueError(f'unknown commitment_mode {cfg.commitment_mode}')
        a, r = gae([x['reward'] for x in rows], [v[x['i']] for x in rows], [x['tau'] for x in rows],
                   [x['done'] for x in rows], cfg.gamma, cfg.lam)
        for x, ai, ri in zip(rows, a, r):
            adv[x['i']], ret[x['i']] = ai, ri
    kept = np.zeros(len(shard), bool)
    for idxs in streams_from_shard(shard, cfg):
        for i in idxs:
            kept[i] = not (cfg.commitment_mode == 'option' and forced and int(m['reason'][i]) in forced)
    return adv, ret, v, dict(merged_forced_steps=merged, value_rows=int(kept.sum()), kept=kept)


def make_batch(shard, critic, cfg: PPOConfig, dev) -> Batch:
    mask, stats = ratio_mask_np(shard, cfg)
    adv, ret, v, info = compute_advantages(shard, critic, cfg, dev)
    stats.update({k: v_ for k, v_ in info.items() if k != 'kept'})
    T = lambda a, dt=None: torch.as_tensor(np.asarray(a), device=dev) if dt is None else torch.as_tensor(np.asarray(a), device=dev).to(dt)
    i, t = shard.inputs, shard.targets
    b = Batch(obs=T(i['obs'], torch.float32), obs_valid=T(i['obs_valid']).bool(), feat=T(i['feat'], torch.float32),
              legal=T(i['legal']).bool(), prior=T(i['prior'], torch.float32), K=T(i['K']).long(), F=T(i['F']).long(),
              head=T(i['head']).long(), context=T(i['context']).long(), chosen=T(t['chosen']).long(), logp_b=T(t['logp_behaviour'], torch.float32),
              logit_b=T(shard.meta['logit_behaviour'], torch.float32) if 'logit_behaviour' in shard.meta else T(np.zeros((len(shard), 1)), torch.float32),
              ratio_mask=T(mask & info['kept']).bool(), adv=T(adv, torch.float32), ret=T(ret, torch.float32),
              old_v=T(v, torch.float32), value_mask=T(info['kept']).bool(), stats=stats)
    return b


# --------------------------------------------------------------------------------------------- policy evaluation
def policy_logp(model, b: Batch, idx: torch.Tensor, names: dict[int, str], return_logits: bool = False):
    """Log-probability of the chosen action, entropy and full log-softmax for rows `idx`, grouped per head
    (each head has its own K/F); calls the contract API PolicyNet.encode / head_logits."""
    n = len(idx)
    logp = torch.zeros(n, device=b.obs.device)
    ent = torch.zeros(n, device=b.obs.device)
    tkl = torch.zeros(n, device=b.obs.device)
    full = torch.full((n, b.feat.shape[1]), NEG_INF, device=b.obs.device)
    h_all = model.encode(b.obs[idx])
    heads = b.head[idx]
    for hid in torch.unique(heads).tolist():
        sel = (heads == hid).nonzero(as_tuple=True)[0]
        rows = idx[sel]
        Kh = int(b.K[rows].max().clamp(min=1))
        Fh = int(b.F[rows].max().clamp(min=1))
        legal = b.legal[rows, :Kh] & (torch.arange(Kh, device=b.obs.device)[None, :] < b.K[rows, None])
        logits = call_head_logits(model, names[hid], h_all[sel], b.feat[rows, :Kh, :Fh], legal, b.prior[rows, :Kh],
                                  b.context[rows])
        full[sel, :Kh] = logits
        lsm = masked_log_softmax(logits)
        logp[sel] = lsm.gather(1, b.chosen[rows, None].clamp(0, Kh - 1)).squeeze(1)
        ent[sel] = masked_entropy(lsm)
        prior_l = masked_log_softmax(b.prior[rows, :Kh].masked_fill(~legal, NEG_INF))
        p = lsm.exp()
        tkl[sel] = torch.where(torch.isfinite(lsm), p * (lsm - prior_l), torch.zeros_like(p)).sum(-1)
    if return_logits:
        return logp, ent, tkl, full
    return logp, ent, tkl


def parity_check(model, b: Batch, names, tol: float) -> float:
    idx = b.ratio_mask.nonzero(as_tuple=True)[0]
    if len(idx) == 0:
        return 0.0
    with torch.no_grad():
        lp, _, _, z = policy_logp(model, b, idx, names, return_logits=True)
    err = float((lp - b.logp_b[idx]).abs().max())
    if b.logit_b.shape[1] == z.shape[1]:                  # logged C++ logits (nn_log.h v1 trailer), when present
        logged = b.logit_b[idx]
        has = logged.abs().sum(1) > 0
        fin = torch.isfinite(z) & has[:, None]
        if fin.any():
            lerr = float((z[fin] - logged[fin]).abs().max())
            if not math.isfinite(lerr) or lerr > tol:
                raise PolicyParityError(f'C++/torch logit mismatch {lerr:.3g} > {tol}')
            err = max(err, lerr)
    if not math.isfinite(err) or err > tol:
        raise PolicyParityError(f'C++/torch behaviour logp mismatch {err:.3g} > {tol} on {len(idx)} sampled rows; '
                                'the training data were not produced by this policy/preprocessing')
    return err


def explained_variance(pred: np.ndarray, target: np.ndarray) -> float:
    var = np.var(target)
    return float('nan') if var < 1e-12 else float(1.0 - np.var(target - pred) / var)


def ppo_update(model, critic, actor_opt, critic_opt, shard, cfg: PPOConfig, *, authorized: bool,
               time_limit_minutes: float | None, deadline: Deadline | None = None) -> dict:
    """One PPO update on freshly collected on-policy data (a shard produced by the current actor)."""
    minutes = require_authorization(authorized, time_limit_minutes, 'rl')
    deadline = deadline or Deadline.from_minutes(minutes)
    dev = next(model.parameters()).device
    names = head_names()
    b = make_batch(shard, critic, cfg, dev)
    parity = parity_check(model, b, names, cfg.parity_tol)
    idx_all = b.ratio_mask.nonzero(as_tuple=True)[0]
    adv = b.adv.clone()
    if cfg.normalize_adv and len(idx_all) > 1:
        a = adv[idx_all]
        adv[idx_all] = (a - a.mean()) / a.std().clamp(min=1e-6)
    v_rows = b.value_mask.nonzero(as_tuple=True)[0]
    hw = torch.ones(13, device=dev)
    for k, name in names.items():
        if name in cfg.head_weights:
            hw[k] = float(cfg.head_weights[name])
    metrics = dict(parity_max_abs_logp_error=parity, epochs_run=0, early_stop_kl=False, minibatches=0)
    kls, clips, ents, gns, als, cls = [], [], [], [], [], []
    stop = False
    for epoch in range(cfg.epochs):
        if deadline.expired():
            metrics['stopped_by_deadline'] = True
            break
        perm = idx_all[torch.randperm(len(idx_all), device=dev)] if len(idx_all) else idx_all
        for mb in (perm.split(cfg.minibatch) if len(perm) else []):
            lp, ent, tkl = policy_logp(model, b, mb, names)
            log_ratio = lp - b.logp_b[mb]
            ratio = log_ratio.exp()
            w = hw[b.head[mb]]
            s1, s2 = ratio * adv[mb], ratio.clamp(1 - cfg.clip, 1 + cfg.clip) * adv[mb]
            actor = -(w * torch.minimum(s1, s2)).sum() / w.sum().clamp(min=1e-6)
            loss = actor - cfg.ent_coef * (w * ent).mean() + cfg.teacher_kl_coef * (w * tkl).mean()
            actor_opt.zero_grad()
            loss.backward()
            gn = float(nn.utils.clip_grad_norm_(model.parameters(), cfg.max_grad_norm))
            actor_opt.step()
            with torch.no_grad():
                kl = float(((ratio - 1) - log_ratio).mean())
            kls.append(kl); clips.append(float(((ratio - 1).abs() > cfg.clip).float().mean()))
            ents.append(float(ent.mean().detach())); gns.append(gn); als.append(float(actor.detach()))
            metrics['minibatches'] += 1
            if kl > 1.5 * cfg.target_kl:
                stop = True
                break
        # critic on every value row (including non-ratio rows: their rewards are real)
        for mb in v_rows[torch.randperm(len(v_rows), device=dev)].split(cfg.minibatch):
            vpred = critic(b.obs[mb], b.head[mb])
            closs = cfg.vf_coef * nn.functional.smooth_l1_loss(vpred, b.ret[mb])
            critic_opt.zero_grad(); closs.backward()
            nn.utils.clip_grad_norm_(critic.parameters(), cfg.max_grad_norm); critic_opt.step()
            cls.append(float(closs.detach()))
        metrics['epochs_run'] = epoch + 1
        if stop:
            metrics['early_stop_kl'] = True
            break
    with torch.no_grad():
        vm = b.value_mask.cpu().numpy()
        vnew = critic(b.obs, b.head).cpu().numpy()[vm]
    ret = b.ret.cpu().numpy()[vm]
    chosen = b.chosen.cpu().numpy()
    heads = b.head.cpu().numpy()
    dist = {}
    for hid in np.unique(heads):
        sel = heads == hid
        c = Counter(chosen[sel].tolist())
        dist[names.get(int(hid), str(hid))] = dict(rows=int(sel.sum()), off_teacher_rate=float((chosen[sel] != 0).mean()),
                                                   choice_hist={int(k): int(v) for k, v in sorted(c.items())})
    comp = {k[2:]: float(np.asarray(shard.targets[k]).sum()) for k in shard.targets if k.startswith('r_')}
    mean = lambda x: float(np.mean(x)) if x else float('nan')
    metrics.update(
        approx_kl=mean(kls), max_kl=max(kls) if kls else float('nan'), clip_frac=mean(clips), entropy=mean(ents),
        grad_norm=mean(gns), actor_loss=mean(als), critic_loss=mean(cls),
        explained_variance_before=explained_variance(b.old_v.cpu().numpy()[vm], ret),
        explained_variance_after=explained_variance(vnew, ret),
        critic_mae=float(np.mean(np.abs(vnew - ret))) if len(ret) else float('nan'),
        reward_components=comp, action_distribution=dist, **b.stats,
        note='loss decrease is not gameplay evidence; evaluate with the engine gates (deployed argmax AND sampled)')
    return metrics
