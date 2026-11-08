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
import os as _os
LAYOUT = int(_os.environ.get("NN_LAYOUT", "2"))  # 2: 500 features; 3: 828 (24 camp groups, allies' claimed targets)
if LAYOUT == 3:
    BLK = {"g": (0, 1, 16), "s": (16, 1, 44), "a": (60, 5, 16), "e": (140, 8, 16), "c": (268, 24, 22), "l": (796, 4, 8)}
elif LAYOUT == 4:  # E123 (A2_NN_XF): 6 more global fields (exact deaths and respawn countdown), 5 more camp fields (draft-turn analysis)
    BLK = {"g": (0, 1, 22), "s": (22, 1, 44), "a": (66, 5, 12), "e": (126, 8, 16), "c": (254, 10, 27), "l": (524, 4, 8)}
else:
    BLK = {"g": (0, 1, 16), "s": (16, 1, 44), "a": (60, 5, 12), "e": (120, 8, 16), "c": (248, 10, 22), "l": (468, 4, 8)}
NFEAT = max(o + n * w for o, n, w in BLK.values())
DROP = {"g": [13], "s": [29, 31], "a": [10], "e": [14], "c": [1], "l": [7]}  # identifiers / v92-internal
TYPEF = {"s": 0, "a": 1, "e": 1}  # field holding a category (one-hot instead of numeric): champion type ...
NTYPE = {"s": NT, "a": NT, "e": NT}  # ... with this many classes
NMAPS = 71  # version 3: global field 13 = ladder map id (1-70 = v92's ladfit maps, 0 = not a ladder map)
if LAYOUT == 3:
    DROP["g"] = []
    TYPEF["g"], NTYPE["g"] = 13, NMAPS
HEADS = ["behaviour", "target", "step", "attack", "cast", "cast_tgt", "cast_pre", "utility", "shop"]
NCLS = {"behaviour": 8, "step": 9, "cast": 3, "cast_pre": 2, "utility": 6, "shop": 88,
        "option": 5}  # option: RL-only residual head (0 none = v92 + the imitation heads, 1 hunt, 2 home, 3 regroup, 4 bank now)
OPT_NONE_BIAS = 7.0  # a fresh option head says "none" (bias 7, zero weights; ~0.4% forced options per turn): the start = the best bot


def init_option(net):
    """Zero the option head except a strong "none" bias (used whenever a checkpoint has no trained option head)."""
    with torch.no_grad():
        net.lin["option"].weight.zero_()
        net.lin["option"].bias.zero_()
        net.lin["option"].bias[0] = OPT_NONE_BIAS


def load(net, path, device="cpu"):
    """Load a checkpoint; checkpoints from before the option head get the fresh "none" option head."""
    sd = torch.load(path, map_location=device, weights_only=True)
    missing, unexpected = net.load_state_dict(sd, strict=False)
    assert not unexpected and all(k.startswith("lin.option") for k in missing), (missing, unexpected)
    if missing:
        init_option(net)
    return net


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
        self.deploy_q11 = _os.environ.get('NN_DEPLOY_PREP') == '1'
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
                t = B[k][..., TYPEF[k]].long().clamp(0, NTYPE[k] - 1)
                x = torch.cat([x, F.one_hot(t, NTYPE[k]).float()], -1)
            if self.deploy_q11:
                x = torch.trunc(x.clamp(-16000/2048,16000/2048)*2048)/2048
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
        dims = {k: len(prep.keep[k]) + (NTYPE[k] if k in TYPEF else 0) for k in BLK}
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
    # NN_STUDENT=ENCxTRUNK (E123): larger students for the same one-layer encoder / two-layer trunk shape (default 16x64)
    e, t = (int(v) for v in _os.environ.get("NN_STUDENT", "16x64").split("x"))
    return Net(prep, e, 1, t, 2)


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
