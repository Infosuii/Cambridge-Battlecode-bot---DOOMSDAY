"""Shared training utilities: deadlines, early stopping, grouped-partition guards, seeding."""
from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass

import numpy as np
import torch


class Deadline:
    """Absolute wall-clock deadline (epoch seconds). Never extended by resume."""

    def __init__(self, deadline_epoch: float):
        self.deadline = float(deadline_epoch)

    @classmethod
    def from_minutes(cls, minutes: float) -> 'Deadline':
        return cls(time.time() + 60.0 * float(minutes))

    def remaining(self) -> float:
        return self.deadline - time.time()

    def expired(self, margin: float = 0.0) -> bool:
        return self.remaining() <= margin


@dataclass
class EarlyStopper:
    patience: int = 5
    min_delta: float = 1e-4
    best: float = math.inf
    best_epoch: int = -1
    bad: int = 0

    def step(self, value: float, epoch: int) -> bool:
        """Returns True when this is a new best; check `.stop` afterwards."""
        if value < self.best - self.min_delta:
            self.best, self.best_epoch, self.bad = value, epoch, 0
            return True
        self.bad += 1
        return False

    @property
    def stop(self) -> bool:
        return self.bad >= self.patience

    def state_dict(self) -> dict:
        return dict(patience=self.patience, min_delta=self.min_delta, best=self.best, best_epoch=self.best_epoch,
                    bad=self.bad)


def assert_disjoint_partitions(train_manifest: dict, val_manifest: dict) -> None:
    """Grouped validation guard: no match identity may appear in two partitions; final_eval is never trained on."""
    for m, name in ((train_manifest, 'train'), (val_manifest, 'validation')):
        if m.get('partition') == 'final_eval':
            raise ValueError(f'{name} input is a final_eval partition; final evaluation data is never used for fitting')
    a, b = set(train_manifest.get('matches', [])), set(val_manifest.get('matches', []))
    both = a & b
    if both:
        raise ValueError(f'{len(both)} matches appear in both train and validation (grouping violated)')


def seed_all(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def device(name: str | None = None) -> torch.device:
    if name in (None, 'auto'):
        return torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    return torch.device(name)
