# Vendored unchanged from JOHNDOE's johndoe/rl-learner-e3-1104 @ e6807c95 tools/rl_learner_1104/target_head_reference/head.py
"""Reference learner math; not an integrated or fuel-profiled Battlecode actor."""
import math
import torch
from torch import nn

class TargetHead(nn.Module):
    def __init__(self):
        super().__init__()
        self.context = nn.Linear(160, 64)
        self.query = nn.Linear(64, 16)
        self.key = nn.Linear(16, 16)
        self.features = nn.Linear(4, 16)
        self.far = nn.Linear(64, 1)
        self.gate = nn.Linear(64, 1)
        nn.init.zeros_(self.query.weight)
        nn.init.zeros_(self.query.bias)
        nn.init.zeros_(self.far.weight)
        nn.init.zeros_(self.far.bias)
        nn.init.zeros_(self.gate.weight)
        nn.init.constant_(self.gate.bias, math.log(.02/.98))

    def forward(self, context, camps, features, native_logits, valid, mapping, reference, physical_count):
        # Slots: K camp rows followed by one far/fallback row. Mapping is metadata,
        # never a learned input. Every physical reference must have valid support.
        batch, slots = valid.shape
        if slots != camps.shape[1] + 1 or not valid.any(-1).all():
            raise ValueError('invalid slot support')
        if mapping.shape != valid.shape or (mapping[valid] < 0).any() or (mapping[valid] >= physical_count).any():
            raise ValueError('invalid physical mapping')
        h = self.context(context).relu()
        q = self.query(h)
        keys = self.key(camps) + self.features(features)
        residual = (keys * q[:, None]).sum(-1) / 4
        scores = native_logits + torch.cat((residual, self.far(h)), -1)
        slot_q = scores.masked_fill(~valid, -torch.inf).softmax(-1)
        physical_q = slot_q.new_zeros(batch, physical_count)
        physical_q.scatter_add_(1, mapping.clamp(0, physical_count-1), slot_q)
        ref = torch.nn.functional.one_hot(reference, physical_count).to(slot_q)
        if not ((valid & (mapping == reference[:, None])).any(-1)).all():
            raise ValueError('reference missing from valid support')
        alpha = self.gate(h).sigmoid()
        policy = alpha * physical_q + (1-alpha) * ref
        return policy, alpha, slot_q
