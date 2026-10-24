"""Team value / outcome models with grouped validation, and the PPO critic.

- `Critic`: state-value function for PPO over the encoded observation (+ head one-hot, since each head's SMDP has its
  own decision times). Trained only inside ppo.update.
- `train_value`: fits PolicyNet.values() ('win_logit' vs outcome, 'margin' vs final gem margin) on record shards with
  a grouped train/validation split and early stopping. Rows are de-duplicated per (match, side, champion, round), so
  turns with many decisions are not over-weighted.
- `DraftOutcomeModel` / `train_draft_outcome`: observational draft-composition outcome model from archive summaries
  (engine 1.0.2 + 1.0.3, scope draft_observational). Labels are confounded by team strength: winning drafts are
  correlated with strong teams, not proven good choices. Never a gameplay label.
Every training function requires explicit authorization (nfs.train.auth) and an absolute deadline.
"""
from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field

import numpy as np
import torch
from torch import nn

from .auth import require_authorization
from .common import Deadline, EarlyStopper, assert_disjoint_partitions, device as pick_device

N_HEADS = 13


class Critic(nn.Module):
    def __init__(self, obs_dim: int, hidden: int = 64, n_heads: int = N_HEADS):
        super().__init__()
        self.obs_dim, self.n_heads = obs_dim, n_heads
        self.net = nn.Sequential(nn.Linear(obs_dim + n_heads, hidden), nn.Tanh(), nn.Linear(hidden, hidden),
                                 nn.Tanh(), nn.Linear(hidden, 1))

    def forward(self, obs: torch.Tensor, head: torch.Tensor) -> torch.Tensor:
        oh = nn.functional.one_hot(head.long().clamp(0, self.n_heads - 1), self.n_heads).to(obs.dtype)
        return self.net(torch.cat([obs.clamp(-10, 10), oh], -1)).squeeze(-1)


@dataclass
class ValueConfig:
    lr: float = 3e-4
    weight_decay: float = 1e-4
    batch_size: int = 512
    max_epochs: int = 50
    patience: int = 5
    w_win: float = 1.0
    w_margin: float = 0.5
    device: str = 'auto'
    seed: int = 1


def unique_obs_rows(shard) -> np.ndarray:
    m = shard.meta
    keys = np.stack([m['match_index'].astype(np.int64), m['side'].astype(np.int64), m['champion'].astype(np.int64),
                     m['round'].astype(np.int64)], 1)
    valid = shard.inputs['obs_valid'].astype(bool)
    _, idx = np.unique(keys[valid], axis=0, return_index=True)
    return np.flatnonzero(valid)[np.sort(idx)]


def _value_tensors(shard, dev):
    idx = unique_obs_rows(shard)
    t = lambda a: torch.as_tensor(np.asarray(a)[idx], device=dev)
    return t(shard.inputs['obs']).float(), t(shard.targets['outcome']).float(), t(shard.targets['margin']).float()


def value_loss(model, obs, outcome, margin, cfg: ValueConfig):
    v = model.values(model.encode(obs))
    lw = nn.functional.binary_cross_entropy_with_logits(v['win_logit'], outcome)
    lm = nn.functional.mse_loss(v['margin'], margin)
    return cfg.w_win * lw + cfg.w_margin * lm, dict(win_bce=float(lw.detach()), margin_mse=float(lm.detach()))


def train_value(model, train_shard, val_shard, cfg: ValueConfig, *, authorized: bool, time_limit_minutes: float | None,
                deadline: Deadline | None = None) -> dict:
    minutes = require_authorization(authorized, time_limit_minutes, 'train-value')
    deadline = deadline or Deadline.from_minutes(minutes)
    assert_disjoint_partitions(train_shard.manifest, val_shard.manifest)
    dev = pick_device(cfg.device)
    torch.manual_seed(cfg.seed)
    model.to(dev)
    xo, yo, mo = _value_tensors(train_shard, dev)
    xv, yv, mv = _value_tensors(val_shard, dev)
    if len(xo) == 0 or len(xv) == 0:
        raise ValueError('train-value needs observation rows in both partitions')
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    stop = EarlyStopper(cfg.patience)
    best = copy.deepcopy(model.state_dict())
    history = []
    for epoch in range(cfg.max_epochs):
        if deadline.expired():
            break
        model.train()
        for idx in torch.randperm(len(xo), device=dev).split(cfg.batch_size):
            loss, _ = value_loss(model, xo[idx], yo[idx], mo[idx], cfg)
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
        model.eval()
        with torch.no_grad():
            vl, parts = value_loss(model, xv, yv, mv, cfg)
            acc = float(((model.values(model.encode(xv))['win_logit'] > 0).float() == (yv > 0.5).float()).float().mean())
        history.append(dict(epoch=epoch, val_loss=float(vl), val_win_acc=acc, **parts))
        if stop.step(float(vl), epoch):
            best = copy.deepcopy(model.state_dict())
        if stop.stop:
            break
    model.load_state_dict(best)
    return dict(history=history, early_stopping=stop.state_dict(), train_rows=len(xo), val_rows=len(xv),
                caveat='validation loss/accuracy are not gameplay evidence; promotion requires engine gates')


# --------------------------------------------------------------------------------------------- draft (observational)
N_CHAMPIONS = 12


def draft_features(picks_own: list[int], picks_opp: list[int], first_pick_own: bool) -> np.ndarray:
    x = np.zeros(2 * N_CHAMPIONS + 4, np.float32)
    for c in picks_own:
        x[c] += 1
    for c in picks_opp:
        x[N_CHAMPIONS + c] += 1
    size = len(picks_own)
    if 3 <= size <= 5:
        x[2 * N_CHAMPIONS + size - 3] = 1
    x[-1] = float(first_pick_own)
    return x


def draft_rows(records: list[dict]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Both perspectives of each accepted archive record (scope gameplay_1_0_3 or draft_observational)."""
    xs, ys, ids = [], [], []
    for r in records:
        if r.get('label_scope') not in ('gameplay_1_0_3', 'draft_observational'):
            continue
        for side, other in (('teamA', 'teamB'), ('teamB', 'teamA')):
            xs.append(draft_features(r['picks'][side], r['picks'][other], r.get('first_pick') == side))
            ys.append(float(r['outcome'] == side))
            ids.append(r['match_id'])
    return np.stack(xs) if xs else np.zeros((0, 2 * N_CHAMPIONS + 4), np.float32), np.asarray(ys, np.float32), ids


class DraftOutcomeModel(nn.Module):
    def __init__(self, hidden: int = 32):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(2 * N_CHAMPIONS + 4, hidden), nn.Tanh(), nn.Linear(hidden, 1))

    def forward(self, x):
        return self.net(x).squeeze(-1)


def train_draft_outcome(records: list[dict], assignment: dict, cfg: ValueConfig, *, authorized: bool,
                        time_limit_minutes: float | None, model: nn.Module | None = None) -> dict:
    """Observational, confounded. Uses only 'train' rows for fitting and 'validation' for early stopping."""
    minutes = require_authorization(authorized, time_limit_minutes, 'train-value --draft')
    deadline = Deadline.from_minutes(minutes)
    x, y, ids = draft_rows(records)
    part = np.array([assignment.get(i, 'unassigned') for i in ids])
    tr, va = part == 'train', part == 'validation'
    if tr.sum() == 0 or va.sum() == 0:
        raise ValueError('draft outcome model needs train and validation rows')
    dev = pick_device(cfg.device)
    torch.manual_seed(cfg.seed)
    model = (model or DraftOutcomeModel()).to(dev)
    X, Y = torch.as_tensor(x, device=dev), torch.as_tensor(y, device=dev)
    tri, vai = torch.as_tensor(np.flatnonzero(tr), device=dev), torch.as_tensor(np.flatnonzero(va), device=dev)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    stop, best, hist = EarlyStopper(cfg.patience), copy.deepcopy(model.state_dict()), []
    for epoch in range(cfg.max_epochs):
        if deadline.expired():
            break
        for idx in tri[torch.randperm(len(tri), device=dev)].split(cfg.batch_size):
            loss = nn.functional.binary_cross_entropy_with_logits(model(X[idx]), Y[idx])
            opt.zero_grad(); loss.backward(); opt.step()
        with torch.no_grad():
            vl = float(nn.functional.binary_cross_entropy_with_logits(model(X[vai]), Y[vai]))
        hist.append(dict(epoch=epoch, val_bce=vl))
        if stop.step(vl, epoch):
            best = copy.deepcopy(model.state_dict())
        if stop.stop:
            break
    model.load_state_dict(best)
    return dict(history=hist, early_stopping=stop.state_dict(), train_rows=int(tr.sum()), val_rows=int(va.sum()),
                label_scope='draft_observational', confounded=True,
                caveat='winning drafts are observational and confounded by team strength; not causal evidence')
