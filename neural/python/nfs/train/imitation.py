"""Imitation pretraining: per-head cross-entropy to the teacher label over masked candidates + value regression.

- Logits are produced through the contract API (PolicyNet.encode / head_logits), i.e. exactly the runtime formula
  prior + R*tanh(r/R) with illegal = -inf, so the trained residual is the one deployed.
- Label = `targets.teacher` (candidate 0 for the inherited teacher by convention; other teachers, e.g. instrumented
  v47 rollouts, may log other indices). Because the runtime prior already ranks the teacher first, imitating the own
  teacher mainly sharpens/regularises the residual; it does not by itself create a stronger policy.
- Per-head loss weights (`head_weights`, 0 = ablated head) and value loss weight (`value_weight`, 0 = ablated).
- Grouped validation: train and validation shards must come from disjoint grouped partitions (final_eval refused);
  early stopping restores the best validation state. Validation metrics are not gameplay evidence.
"""
from __future__ import annotations

import copy
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np
import torch
from torch import nn

from .auth import require_authorization
from .common import Deadline, EarlyStopper, assert_disjoint_partitions, device as pick_device
from .ppo import call_head_logits, head_names, masked_log_softmax
from .value import ValueConfig, value_loss, unique_obs_rows


@dataclass
class ImitationConfig:
    lr: float = 3e-4
    weight_decay: float = 1e-4
    batch_size: int = 512
    max_epochs: int = 30
    patience: int = 4
    min_delta: float = 1e-4
    head_weights: dict = field(default_factory=dict)   # name -> weight; missing = 1.0; 0 = ablated
    value_weight: float = 0.25
    prior_dropout: float = 0.0                        # probability of zeroing priors during training rows
    device: str = 'auto'
    seed: int = 1


def _tensors(shard, dev):
    i, t = shard.inputs, shard.targets
    T = lambda a, dt: torch.as_tensor(np.asarray(a), device=dev).to(dt)
    K = T(i['K'], torch.long)
    teacher = T(t['teacher'], torch.long)
    legal = T(i['legal'], torch.bool)
    rows = torch.arange(len(K), device=dev)
    ok = (K > 0) & (teacher >= 0) & (teacher < K)
    ok = ok & legal[rows, teacher.clamp(0, legal.shape[1] - 1)]
    return dict(obs=T(i['obs'], torch.float32), feat=T(i['feat'], torch.float32), legal=legal,
                prior=T(i['prior'], torch.float32), K=K, F=T(i['F'], torch.long), head=T(i['head'], torch.long),
                context=T(i['context'], torch.long),
                teacher=teacher, ok=ok)


def imitation_loss(model, d: dict, idx: torch.Tensor, names: dict, cfg: ImitationConfig, train: bool = False):
    h_all = model.encode(d['obs'][idx])
    total, wsum = 0.0, 0.0
    per = {}
    for hid in torch.unique(d['head'][idx]).tolist():
        w = float(cfg.head_weights.get(names[hid], 1.0))
        if w == 0.0:
            continue
        sel = (d['head'][idx] == hid).nonzero(as_tuple=True)[0]
        rows = idx[sel]
        Kh = int(d['K'][rows].max().clamp(min=1)); Fh = int(d['F'][rows].max().clamp(min=1))
        legal = d['legal'][rows, :Kh] & (torch.arange(Kh, device=idx.device)[None, :] < d['K'][rows, None])
        prior = d['prior'][rows, :Kh]
        if train and cfg.prior_dropout > 0:
            drop = torch.rand(len(rows), 1, device=idx.device) < cfg.prior_dropout
            prior = torch.where(drop, torch.zeros_like(prior), prior)
        lsm = masked_log_softmax(call_head_logits(model, names[hid], h_all[sel], d['feat'][rows, :Kh, :Fh], legal, prior,
                                                  d['context'][rows]))
        ce = -lsm.gather(1, d['teacher'][rows, None]).squeeze(1)
        loss = ce.mean()
        acc = float((lsm.argmax(1) == d['teacher'][rows]).float().mean())
        per[names[hid]] = dict(ce=float(loss.detach()), acc=acc, rows=len(rows))
        total = total + w * loss
        wsum += w
    return (total / max(wsum, 1e-9) if wsum else torch.zeros((), device=idx.device, requires_grad=True)), per


def pretrain(model, train_shard, val_shard, cfg: ImitationConfig, *, authorized: bool,
             time_limit_minutes: float | None, deadline: Deadline | None = None) -> dict:
    minutes = require_authorization(authorized, time_limit_minutes, 'pretrain')
    deadline = deadline or Deadline.from_minutes(minutes)
    assert_disjoint_partitions(train_shard.manifest, val_shard.manifest)
    dev = pick_device(cfg.device)
    torch.manual_seed(cfg.seed)
    model.to(dev)
    names = head_names()
    dt, dv = _tensors(train_shard, dev), _tensors(val_shard, dev)
    tr_idx, va_idx = dt['ok'].nonzero(as_tuple=True)[0], dv['ok'].nonzero(as_tuple=True)[0]
    if len(tr_idx) == 0 or len(va_idx) == 0:
        raise ValueError('pretrain needs labelled decision rows in both partitions')
    vcfg = ValueConfig()
    vrow_t = torch.as_tensor(unique_obs_rows(train_shard), device=dev)
    vrow_v = torch.as_tensor(unique_obs_rows(val_shard), device=dev)
    outcome_t = torch.as_tensor(train_shard.targets['outcome'], device=dev).float()
    margin_t = torch.as_tensor(train_shard.targets['margin'], device=dev).float()
    outcome_v = torch.as_tensor(val_shard.targets['outcome'], device=dev).float()
    margin_v = torch.as_tensor(val_shard.targets['margin'], device=dev).float()
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    stop = EarlyStopper(cfg.patience, cfg.min_delta)
    best = copy.deepcopy(model.state_dict())
    history = []

    def val_metrics():
        model.eval()
        with torch.no_grad():
            l, per = imitation_loss(model, dv, va_idx, names, cfg)
            vl = 0.0
            if cfg.value_weight and len(vrow_v):
                v, _ = value_loss(model, dv['obs'][vrow_v], outcome_v[vrow_v], margin_v[vrow_v], vcfg)
                vl = float(v)
        return float(l) + cfg.value_weight * vl, per, vl

    base, base_per, _ = val_metrics()
    for epoch in range(cfg.max_epochs):
        if deadline.expired():
            break
        model.train()
        for mb in tr_idx[torch.randperm(len(tr_idx), device=dev)].split(cfg.batch_size):
            loss, _ = imitation_loss(model, dt, mb, names, cfg, train=True)
            if cfg.value_weight and len(vrow_t):
                vm = vrow_t[torch.randint(len(vrow_t), (min(len(vrow_t), cfg.batch_size),), device=dev)]
                vl, _ = value_loss(model, dt['obs'][vm], outcome_t[vm], margin_t[vm], vcfg)
                loss = loss + cfg.value_weight * vl
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
        score, per, vl = val_metrics()
        history.append(dict(epoch=epoch, val_objective=score, val_value=vl, per_head=per))
        if stop.step(score, epoch):
            best = copy.deepcopy(model.state_dict())
        if stop.stop:
            break
    model.load_state_dict(best)
    return dict(initial_val_objective=base, initial_per_head=base_per, history=history,
                early_stopping=stop.state_dict(), train_rows=int(len(tr_idx)), val_rows=int(len(va_idx)),
                caveat='validation imitation loss is not gameplay evidence; promotion requires engine gates')
