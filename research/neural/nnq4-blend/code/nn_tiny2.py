"""E124: a small model of the blend's decision (v92's pick stays unless another camp scores > 2 logits higher): cheap enough to run on every farm turn at real fuel.
Camp encoder (camp fields + "this is v92's pick") -> E units; context (global + self, optional enemies) -> C units; score = <camp, q(context)> + v(camp) + alpha * flag; "far" from the context.
Soft targets: the 16x64 student's target head + 2 on v92's pick. Held out by map. Rows: nn_ens_rec.py (all disagreements + 1 in 8 of the rest, weighted back).
usage (project root): python -P agent2/lab/nn_tiny2.py ROWS.npz STUDENT.pt OUT.pt [--e 8] [--c 8] [--enemies 0] [--epochs 12] [--ow 4] [--rows N]"""
import math, os, sys, time, zlib
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nn_model import BLK, NTYPE, Prep, TYPEF, load, split_blocks, student  # noqa: E402

A = sys.argv[1:]
ROWS, SPT, OUT = A[0], A[1], A[2]
arg = lambda k, d: type(d)(A[A.index(k) + 1]) if k in A else d
E, C, ENEM, EP, OW, NROWS, BS, ALPHA = arg("--e", 8), arg("--c", 8), arg("--enemies", 0), arg("--epochs", 12), arg("--ow", 4.0), arg("--rows", 2000000), 2048, 2.0
dev = "cuda"
COFF, CN, CW = BLK["c"]
d = np.load(ROWS)
X = torch.as_tensor(d["X"][:NROWS]).to(dev)
V = torch.as_tensor(d["v92g"][:NROWS]).to(dev)
NG = torch.as_tensor(d["ng"][:NROWS]).to(dev)
game = d["game"][:NROWS]
keys = d["keys"]
held = np.array([zlib.crc32(k.encode()) % 10 == 0 for k in keys])[game]
tr, te = np.where(~held)[0], np.where(held)[0]
print(f"rows {len(X)} (train {len(tr)}, held-out {len(te)}, official share {float(np.mean(d['off'][game])):.2f})", flush=True)


class Tiny(nn.Module):
    def __init__(self, prep):
        super().__init__()
        self.prep = prep
        dims = {k: len(prep.keep[k]) + (NTYPE[k] if k in TYPEF else 0) for k in BLK}
        self.enc = nn.Linear(dims["c"] + 1, E)
        self.ctx = nn.Linear(dims["g"] + dims["s"], C)
        if ENEM:
            self.ee = nn.Linear(dims["e"], C)
            self.ctx2 = nn.Linear(C * 3, C)
        self.q = nn.Linear(C, E)
        self.v = nn.Linear(E, 1)
        self.far = nn.Linear(C + 1, 1)
        self.alpha = nn.Parameter(torch.tensor(ALPHA))

    def forward(self, x, flag, ff):
        B = split_blocks(x)
        P = self.prep(B)
        ctx = F.relu(self.ctx(torch.cat([P["g"][:, 0], P["s"][:, 0]], -1)))
        if ENEM:
            m = (B["e"][..., 0] != 0).unsqueeze(-1).float()
            ee = F.relu(self.ee(P["e"]))
            pooled = [(ee * m).sum(1) / m.sum(1).clamp_min(1.0), (ee - 1e4 * (1 - m)).max(1).values * (m.sum(1) > 0).float()]
            ctx = F.relu(self.ctx2(torch.cat([ctx] + pooled, -1)))
        e = F.relu(self.enc(torch.cat([P["c"], flag.unsqueeze(-1)], -1)))
        s = (e * self.q(ctx).unsqueeze(1)).sum(-1) / math.sqrt(E) + self.v(e).squeeze(-1) + self.alpha * flag
        far = self.far(torch.cat([ctx, ff.unsqueeze(-1)], -1)) + self.alpha * ff.unsqueeze(-1)
        pres = B["c"][..., 0] != 0
        return torch.cat([s.masked_fill(~pres, -1e9), far], 1)


def flags(x, v):
    """flag per camp slot: this camp group is v92's pick; ff: v92's pick is outside the slots."""
    g = x[:, COFF + 1::CW][:, :CN].long()
    pres = x[:, COFF::CW][:, :CN] != 0
    fl = ((g == v.unsqueeze(1)) & pres).float()
    return fl, 1.0 - fl.max(1).values


S = load(student(Prep()), SPT, dev).to(dev).eval()
fl_all, ff_all = flags(X, V)
with torch.no_grad():
    T = torch.cat([S(X[s:s + 8192])["target"] for s in range(0, len(X), 8192)])
    Tb = T.clone()
    Tb[:, :CN] += ALPHA * fl_all
    Tb[:, CN] += ALPHA * ff_all
tv = torch.where(ff_all > 0, torch.full_like(ff_all, CN).long(), fl_all.argmax(1))  # v92's slot
top = T.argmax(1)
choice = Tb.argmax(1)
dis = NG != V
over = choice != tv
W = torch.where(dis, torch.tensor(1.0, device=dev), torch.tensor(8.0, device=dev))
print(f"weighted: network top differs from v92 {100 * (W * dis.float()).sum().item() / W.sum().item():.1f}% of rows, blend overrides v92 {100 * (W * over.float()).sum().item() / W.sum().item():.2f}%", flush=True)
W2 = W * (1.0 + (OW - 1.0) * over.float())
net = Tiny(S.prep).to(dev)
print("parameters", sum(p.numel() for n, p in net.named_parameters() if not n.startswith("prep")), flush=True)
opt = torch.optim.Adam([p for n, p in net.named_parameters() if not n.startswith("prep")], lr=2e-3)
steps = EP * (len(tr) // BS)
sch = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=3e-3, total_steps=steps)


def report(tag):
    net.eval()
    with torch.no_grad():
        idx = torch.as_tensor(te, device=dev)
        o = torch.cat([net(X[idx[s:s + 8192]], fl_all[idx[s:s + 8192]], ff_all[idx[s:s + 8192]]) for s in range(0, len(idx), 8192)])
        ch, ov, w, vs = choice[idx], over[idx], W[idx], tv[idx]
        pk = o.argmax(1)
        same = (pk == ch).float()
        po = pk != vs
        rec = same[ov].mean().item() if ov.any() else 0.0
        prec = (w * same * po.float()).sum().item() / max(1e-6, (w * po.float()).sum().item())
        false = (w * po.float() * (~ov).float()).sum().item() / max(1e-6, (w * (~ov).float()).sum().item())
        ag = (w * same).sum().item() / w.sum().item()
    net.train()
    print(f"{tag}: agreement {100 * ag:.2f}% | blend's overrides found {100 * rec:.1f}% | of the model's overrides {100 * prec:.1f}% are the blend's | overrides where the blend keeps v92 {100 * false:.2f}% | alpha {net.alpha.item():.2f}", flush=True)


t0 = time.time()
for ep in range(EP):
    perm = np.random.permutation(tr)
    tot = 0.0
    for s0 in range(0, len(perm) - BS + 1, BS):
        idx = torch.as_tensor(perm[s0:s0 + BS], device=dev)
        o = net(X[idx], fl_all[idx], ff_all[idx])
        kl = F.kl_div(F.log_softmax(o, -1).clamp_min(-30), F.softmax(Tb[idx], -1), reduction="none").sum(-1)
        loss = (kl * W2[idx]).sum() / W2[idx].sum()
        opt.zero_grad(); loss.backward(); opt.step(); sch.step()
        tot += loss.item()
    if ep == EP - 1 or ep % 3 == 2:
        report(f"epoch {ep + 1} ({time.time() - t0:.0f}s, KL {tot / max(1, len(perm) // BS):.4f})")
torch.save({k: v for k, v in net.state_dict().items()}, OUT)
print("saved", OUT, flush=True)
