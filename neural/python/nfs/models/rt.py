"""Exact Python twins of the C++ runtime primitives in bot/src/nn_rt.h (agent B).

* ``act_np`` / ``act_torch``: rational tanh ``rtanh`` with the same f32 operation order as ``nnrt::act``.
* ``SplitMix64`` / ``mix64`` / ``decision_stream``: bit-identical PRNG.
* ``fnv1a64`` / ``fnv1a32``: checksums over little-endian bytes.
"""
from __future__ import annotations

import numpy as np

MASK64 = (1 << 64) - 1
GOLDEN = 0x9E3779B97F4A7C15
F32 = np.float32
_C27, _C9, _C3, _C1 = F32(27.0), F32(9.0), F32(3.0), F32(1.0)


def act_np(x):
    """rtanh on float32 arrays/scalars, bit-identical to nnrt::act (clamp, rational, clamp)."""
    x = np.asarray(x, dtype=np.float32)
    with np.errstate(invalid='ignore', over='ignore'):
        x = np.where(x < -_C3, -_C3, x).astype(np.float32)
        x = np.where(x > _C3, _C3, x).astype(np.float32)
        t = (x * x).astype(np.float32)
        y = ((x * (_C27 + t)).astype(np.float32) / (_C27 + (_C9 * t).astype(np.float32)).astype(np.float32))
        y = y.astype(np.float32)
        y = np.where(y < -_C1, -_C1, y).astype(np.float32)
        y = np.where(y > _C1, _C1, y).astype(np.float32)
    return y


def act_torch(x):
    """rtanh for torch tensors (same f32 ops elementwise; differentiable; derivative 0 outside |x| > 3)."""
    import torch
    x = torch.clamp(x, -3.0, 3.0)
    t = x * x
    y = (x * (27.0 + t)) / (27.0 + 9.0 * t)
    return torch.clamp(y, -1.0, 1.0)


def bounded_np(r, R):
    R = F32(R)
    return (R * act_np((np.asarray(r, np.float32) / R).astype(np.float32))).astype(np.float32)


def mix64(z: int) -> int:
    z = (z + GOLDEN) & MASK64
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
    return z ^ (z >> 31)


class SplitMix64:
    def __init__(self, s: int):
        self.s = s & MASK64

    def next(self) -> int:
        self.s = (self.s + GOLDEN) & MASK64
        z = self.s
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
        return z ^ (z >> 31)

    def uniform(self) -> np.float32:
        return F32(self.next() >> 40) * F32(1.0 / 16777216.0)

    def uniform_pm1(self, n: int) -> np.ndarray:
        """n values u*2-1 in f32, as the C++ selftest fixtures generate them."""
        out = np.empty(n, np.float32)
        for i in range(n):
            out[i] = F32(self.uniform() * F32(2.0)) - F32(1.0)
        return out


def decision_stream(seed: int, round_: int, champion: int, head: int, call: int) -> SplitMix64:
    s = mix64(seed & 0xFFFFFFFF)
    for v in (round_, champion, head, call):
        s = mix64(s ^ (v & 0xFFFFFFFF))
    return SplitMix64(s)


FNV64_OFFSET, FNV64_PRIME = 0xCBF29CE484222325, 0x100000001B3
FNV32_OFFSET, FNV32_PRIME = 0x811C9DC5, 0x01000193


def fnv1a64(data: bytes, h: int = FNV64_OFFSET) -> int:
    for b in data:
        h = ((h ^ b) * FNV64_PRIME) & MASK64
    return h


def fnv1a64_f32(values) -> int:
    """fnv1a64 over the little-endian float32 bytes of `values` (as nnrt::fnv1a64_f32)."""
    a = np.ascontiguousarray(np.asarray(values, dtype='<f4'))
    return fnv1a64(a.tobytes())


def fnv1a32(data: bytes) -> int:
    h = FNV32_OFFSET
    for b in data:
        h = ((h ^ b) * FNV32_PRIME) & 0xFFFFFFFF
    return h
