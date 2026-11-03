"""Neural bot model (agent2/plans/neural_bot_2026-11-03.md): entity encoders per type -> masked mean+max pooling ->
trunk -> heads (behaviour, target pointer, step, attack pointer, cast, cast target pointer, cast timing, utility, shop).
Teacher: encoders 2 x 64, trunk 2 x 128. Student: encoder 1 x 16, trunk 2 x 64. Feature layout: nnrec.cpp (500 int16).
Identifier fields (handles, group ids, altar codes) and v92-internal state (target_group, heading_home) are dropped."""
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

NT = 13  # champion type ids 0..12
# block offsets / counts / widths in the 500-vector
BLK = {"g": (0, 1, 16), "s": (16, 1, 44), "a": (60, 5, 12), "e": (120, 8, 16), "c": (248, 10, 22), "l": (468, 4, 8)}
DROP = {"g": [13], "s": [29, 31], "a": [10], "e": [14], "c": [1], "l": [7]}  # identifiers / v92-internal
TYPEF = {"s": 0, "a": 1, "e": 1}  # field holding a champion type (one-hot instead of numeric)
HEADS = ["behaviour", "target", "step", "attack", "cast", "cast_tgt", "cast_pre", "utility", "shop"]
NCLS = {"behaviour": 8, "step": 9, "cast": 3, "cast_pre": 2, "utility": 6, "shop": 88}


def split_blocks(X):
    """int16 [N, 500] -> dict of float tensors [N, n, w] (raw values; identifiers kept for masks only)."""
    out = {}
    for k, (o, n, w) in BLK.items():
        out[k] = X[:, o:o + n * w].reshape(-1, n, w)
    return out


class Prep(nn.Module):
    """Feature transform: signed log for magnitudes, one-hot champion types, identifiers dropped. Per-field mean / std
    from the training set are buffers (exported to the bot)."""

    def __init__(self, stats=None):
        super().__init__()
        self.keep = {k: [i for i in range(w) if i not in DROP[k] and i != TYPEF.get(k, -1)] for k, (o, n, w) in BLK.items()}
        for k in BLK:
            nk = len(self.keep[k])
            mu, sd = (stats[k] if stats else (np.zeros(nk), np.ones(nk)))
            self.register_buffer(f"mu_{k}", torch.tensor(mu, dtype=torch.float32))
            self.register_buffer(f"sd_{k}", torch.tensor(sd, dtype=torch.float32))

    def raw(self, B, k):
        x = B[k][..., self.keep[k]].float()
        return torch.sign(x) * torch.log1p(x.abs())

    def forward(self, B):
        out = {}
        for k in BLK:
            x = (self.raw(B, k) - getattr(self, f"mu_{k}")) / getattr(self, f"sd_{k}")
            if k in TYPEF:
                t = B[k][..., TYPEF[k]].long().clamp(0, NT - 1)
                x = torch.cat([x, F.one_hot(t, NT).float()], -1)
            out[k] = x
        return out

    @staticmethod
    def fit_stats(Xs):
        B = split_blocks(torch.as_tensor(Xs))
        p = Prep()
        st = {}
        for k in BLK:
            x = p.raw(B, k)
            if k in ("a", "e", "c", "l"):
                m = B[k][..., 0] != 0
                x = x[m]
            else:
                x = x.reshape(-1, x.shape[-1])
            st[k] = (x.mean(0).numpy(), x.std(0).clamp_min(1e-3).numpy())
        return st


def mlp(i, h, layers):
    mods, d = [], i
    for _ in range(layers):
        mods += [nn.Linear(d, h), nn.ReLU()]
        d = h
    return nn.Sequential(*mods)


class Net(nn.Module):
    def __init__(self, prep, enc=64, enc_layers=2, trunk=128, trunk_layers=2):
        super().__init__()
        self.prep = prep
        dims = {k: len(prep.keep[k]) + (NT if k in TYPEF else 0) for k in BLK}
        self.enc = nn.ModuleDict({k: mlp(dims[k], enc, enc_layers) for k in BLK})
        pooled = enc * 2 + enc * 2 * 4  # global + self (single), allies / enemies / camps / altars (mean + max)
        self.trunk = mlp(pooled, trunk, trunk_layers)
        self.q = nn.ModuleDict({h: nn.Linear(trunk, enc) for h in ("target", "attack", "cast_tgt")})
        self.k = nn.ModuleDict({h: nn.Linear(enc, enc) for h in ("target", "attack", "cast_tgt")})
        self.extra = nn.ParameterDict({"target": nn.Parameter(torch.zeros(1, enc)), "attack": nn.Parameter(torch.zeros(1, enc)),
                                       "cast_tgt": nn.Parameter(torch.zeros(9, enc))})  # far / none / 8 directions + own tile
        self.lin = nn.ModuleDict({h: nn.Linear(trunk, n) for h, n in NCLS.items()})
        self.enc_dim = enc

    def forward(self, X):
        B = split_blocks(X)
        P = self.prep(B)
        emb = {k: self.enc[k](P[k]) for k in BLK}
        present = {k: (B[k][..., 0] != 0) for k in ("a", "e", "c", "l")}
        parts = [emb["g"][:, 0], emb["s"][:, 0]]
        for k in ("a", "e", "c", "l"):
            m = present[k].unsqueeze(-1).float()
            mean = (emb[k] * m).sum(1) / m.sum(1).clamp_min(1.0)
            mx = (emb[k] - 1e4 * (1 - m)).max(1).values * (m.sum(1) > 0).float()
            parts += [mean, mx]
        z = self.trunk(torch.cat(parts, -1))
        out = {h: self.lin[h](z) for h in NCLS}
        n = X.shape[0]

        def pointer(h, ents, masks):
            keys = torch.cat([self.k[h](e) for e in ents] + [self.k[h](self.extra[h]).unsqueeze(0).expand(n, -1, -1)], 1)
            mask = torch.cat(masks + [torch.ones(n, self.extra[h].shape[0], dtype=torch.bool, device=X.device)], 1)
            s = (keys @ self.q[h](z).unsqueeze(-1)).squeeze(-1) / self.enc_dim ** 0.5
            return s.masked_fill(~mask, -1e9)

        ones = torch.ones(n, 1, dtype=torch.bool, device=X.device)
        out["target"] = pointer("target", [emb["c"]], [present["c"]])                       # 10 camps + far
        out["attack"] = pointer("attack", [emb["e"], emb["c"]], [present["e"], present["c"]])  # 8 + 10 + none
        out["cast_tgt"] = pointer("cast_tgt", [emb["s"], emb["a"], emb["e"], emb["c"]],
                                  [ones, present["a"], present["e"], present["c"]])         # 1 + 5 + 8 + 10 + 9
        return out


def teacher(prep):
    return Net(prep, 64, 2, 128, 2)


def student(prep):
    return Net(prep, 16, 1, 64, 2)


def losses(out, Y, weights=None):
    tot, per = 0.0, {}
    for j, h in enumerate(HEADS):
        y = Y[:, j].long()
        m = y >= 0
        if m.sum() == 0:
            continue
        l = F.cross_entropy(out[h][m], y[m])
        per[h] = l.item()
        tot = tot + (weights or {}).get(h, 1.0) * l
    return tot, per
