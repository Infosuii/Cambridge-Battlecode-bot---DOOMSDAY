"""Bit-exact numpy twin of the C++ forward pass (bot/src/nn_rt.h + nn_model.h), operating on the exported f32 blob.

Every operation is a float32 IEEE op in the C++ order (sequential input accumulation with zero-skip, rtanh,
masked mean/max in row order), so logits/values/encodings match the Wasm/native build bit-for-bit.
log-softmax uses float32 exp/log from numpy, which may differ from libm by an ulp (tests allow 1e-6).
Also reproduces the C++ selftest fixtures (``selftest_lines``).
"""
from __future__ import annotations

import numpy as np

from . import layout
from .rt import SplitMix64, act_np, bounded_np, fnv1a64_f32

F32 = np.float32
NEG_INF = F32(-np.inf)


class Blob:
    """Named views into the flat blob following ``layout(cfg)``."""

    def __init__(self, cfg: dict, blob: np.ndarray):
        self.cfg = cfg
        self.blob = np.asarray(blob, dtype=np.float32)
        self.p, off = {}, 0
        for name, shape in layout(cfg):
            n = int(np.prod(shape))
            self.p[name] = self.blob[off:off + n].reshape(shape)
            off += n
        if off != self.blob.size:
            raise ValueError(f'blob has {self.blob.size} floats, layout needs {off}')
        self.heads = {h['name']: h for h in cfg['heads']}


def dense_acc(x, W, y):
    """y += x @ W in C++ order: for each non-zero x[i] in order, y = y + x[i] * W[i] (f32)."""
    y = np.array(y, dtype=np.float32, copy=True)
    for i in range(W.shape[0]):
        xi = F32(x[i])
        if xi == 0:
            continue
        y = (y + (xi * W[i]).astype(np.float32)).astype(np.float32)
    return y


def dense(x, W, b):
    return dense_acc(x, W, np.array(b, dtype=np.float32))


def dot(x, w, b):
    s = F32(b)
    for i in range(len(w)):
        s = F32(s + F32(F32(x[i]) * F32(w[i])))
    return s


def pool_mean_max(rows, mask):
    E = rows.shape[1] if rows.ndim == 2 else 0
    mean = np.zeros(E, np.float32)
    mx = np.zeros(E, np.float32)
    n = 0
    for r in range(rows.shape[0]):
        if not mask[r]:
            continue
        if n == 0:
            mean = rows[r].astype(np.float32).copy()
            mx = rows[r].astype(np.float32).copy()
        else:
            mean = (mean + rows[r]).astype(np.float32)
            mx = np.where(rows[r] > mx, rows[r], mx).astype(np.float32)
        n += 1
    if n > 1:
        mean = (mean / F32(n)).astype(np.float32)
    return mean, mx


def encode(B: Blob, x) -> np.ndarray:
    o = B.cfg['obs']
    S, Ra, Da, Re, De = o['self_global_dim'], o['ally_rows'], o['ally_dim'], o['enemy_rows'], o['enemy_dim']
    x = np.asarray(x, np.float32)
    i = 0
    sg = x[i:i + S]; i += S
    ally = x[i:i + Ra * Da].reshape(Ra, Da); i += Ra * Da
    am = x[i:i + Ra] > F32(0.5); i += Ra
    enemy = x[i:i + Re * De].reshape(Re, De); i += Re * De
    em = x[i:i + Re] > F32(0.5)
    p = B.p
    g = act_np(dense(sg, p['enc.g1_w'], p['enc.g1_b']))
    E = B.cfg['encoder']['entity_hidden']

    def block(rows, mask, w, b):
        emb = np.zeros((rows.shape[0], E), np.float32)
        for r in range(rows.shape[0]):
            if mask[r]:
                emb[r] = act_np(dense(rows[r], w, b))
        return pool_mean_max(emb, mask)

    a_mean, a_max = block(ally, am, p['enc.a1_w'], p['enc.a1_b'])
    e_mean, e_max = block(enemy, em, p['enc.e1_w'], p['enc.e1_b'])
    cat = np.concatenate([g, a_mean, a_max, e_mean, e_max]).astype(np.float32)
    return act_np(dense(cat, p['enc.c1_w'], p['enc.c1_b']))


def head_pre(B: Blob, name, h, context=0):
    hc, p = B.heads[name], B.p
    q = f'heads.{name}.'
    u = p[q + 'b1'].astype(np.float32).copy()
    if hc['uses_ctx']:
        u = dense_acc(h, p[q + 'wh'], u)
    if hc['n_ctx']:
        u = (u + p[q + 'emb'][context]).astype(np.float32)
    return u


def head_residual(B: Blob, name, u, f):
    p = B.p
    q = f'heads.{name}.'
    z = act_np(dense_acc(f, p[q + 'wf'], u))
    return dot(z, p[q + 'w2'][:, 0], p[q + 'b2'][0])


def candidate_logits(B: Blob, name, h, feat, legal, prior, context=0):
    hc = B.heads[name]
    feat = np.asarray(feat, np.float32).reshape(len(legal), hc['F'])
    u = head_pre(B, name, h, context)
    out = np.full(len(legal), NEG_INF, np.float32)
    for k in range(len(legal)):
        if legal[k]:
            r = head_residual(B, name, u, feat[k])
            out[k] = F32(F32(prior[k]) + bounded_np(r, hc['R']))
    return out


def value_out(B: Blob, name, h):
    u = act_np(head_pre(B, name, h, 0))
    q = f'heads.{name}.'
    return dense(u, B.p[q + 'w2'], B.p[q + 'b2'])


def leaf_out(B: Blob, h, f, context=0):
    hc = B.heads['ts_leaf']
    u = head_pre(B, 'ts_leaf', h, context)
    return bounded_np(head_residual(B, 'ts_leaf', u, np.asarray(f, np.float32)), hc['R'])


def masked_argmax(v, legal) -> int:
    best, bv = -1, None
    for k in range(len(v)):
        if not legal[k]:
            continue
        if best < 0 or v[k] > bv:
            best, bv = k, v[k]
    return best


def masked_log_softmax(l, legal):
    a = masked_argmax(l, legal)
    if a < 0:
        return None, None
    m = F32(l[a])
    e = np.array([np.exp(F32(l[k] - m)) if legal[k] else F32(0) for k in range(len(l))], np.float32)
    s = F32(0)
    for v in e:
        s = F32(s + v)
    ls = np.log(s)
    lp = np.array([F32(F32(l[k] - m) - ls) if legal[k] else NEG_INF for k in range(len(l))], np.float32)
    return lp, e


def masked_sample(l, legal, u):
    """Inverse-CDF sample exactly as nnrt::masked_sample; returns (index, logp)."""
    lp, e = masked_log_softmax(l, legal)
    if lp is None:
        return -1, None
    s = F32(0)
    for v in e:
        s = F32(s + v)
    target = F32(F32(u) * s)
    c, last, pick = F32(0), -1, -1
    for k in range(len(l)):
        if not legal[k]:
            continue
        last = k
        c = F32(c + e[k])
        if target < c:
            pick = k
            break
    if pick < 0:
        pick = last
    return pick, lp[pick]


# ---------------------------------------------------------------------- selftest fixtures (nn_head.cpp selftest())
SELFTEST_SEED = 0x5E1F7E57


def selftest_obs(cfg: dict) -> np.ndarray:
    o = cfg['obs']
    S, Ra, Da, Re, De = o['self_global_dim'], o['ally_rows'], o['ally_dim'], o['enemy_rows'], o['enemy_dim']
    x = SplitMix64(SELFTEST_SEED).uniform_pm1(o['obs_dim'])
    a0 = S
    am0 = a0 + Ra * Da
    e0 = am0 + Ra
    em0 = e0 + Re * De
    for r in range(Ra):
        ok = r % 3 != 1
        x[am0 + r] = 1.0 if ok else 0.0
        if not ok:
            x[a0 + r * Da:a0 + (r + 1) * Da] = 0
    for r in range(Re):
        ok = r % 2 == 0
        x[em0 + r] = 1.0 if ok else 0.0
        if not ok:
            x[e0 + r * De:e0 + (r + 1) * De] = 0
    return x


def selftest_lines(cfg: dict, blob: np.ndarray, model_name: str) -> list[str]:
    """Expected 'NNST ...' lines (hash lines only) for a model, as printed by the C++ selftest."""
    B = Blob(cfg, blob)
    h = encode(B, selftest_obs(cfg))
    lines = [f'NNST {model_name} enc -1 {fnv1a64_f32(h):016x} 0']
    K = 16
    for hc in cfg['heads']:
        hi = hc['id']
        rng = SplitMix64(SELFTEST_SEED + 0x100 * (hi + 1))
        hh = h if hc['uses_ctx'] else None
        if hc['kind'] == 'candidate':
            feat = rng.uniform_pm1(K * hc['F'])
            legal = [k % 5 != 3 for k in range(K)]
            prior = np.array([0.0 if k == 0 else F32(-0.125) * F32(k) for k in range(K)], np.float32)
            lg = candidate_logits(B, hc['name'], hh, feat, legal, prior, 0)
            lines.append(f'NNST {model_name} head {hi} {fnv1a64_f32(lg):016x} {masked_argmax(lg, legal)}')
        elif hc['kind'] == 'value':
            y = value_out(B, hc['name'], hh)
            lines.append(f'NNST {model_name} value {hi} {fnv1a64_f32(y):016x} {hc["n_out"]}')
        else:
            f = rng.uniform_pm1(hc['F'])
            y = np.array([leaf_out(B, hh, f, 0)], np.float32)
            lines.append(f'NNST {model_name} leaf {hi} {fnv1a64_f32(y):016x} 1')
    return lines
