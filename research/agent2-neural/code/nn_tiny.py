"""E121 fuel fit: how much of the teacher's camp choice and bank decision can a tiny, always-fresh model copy?
Target: score each camp group from its own features and a small context vector (global + self features); the student's
trunk is what costs the fuel, so none here. Bank: a small model on the same context. Models are trained on recorded states
(an nn_labels.py file; rows are states, labels unused) to match the teacher, then scored on held-out maps. Reported: argmax
agreement on all rows and on the rows that matter (the teacher's choice is not the current target), against the
distilled student as the reference. Multiply-adds per decision are printed for each model (fuel is about 4-6 per MAC).
usage: python -P agent2/lab/nn_tiny.py TEACHER.pt LABELS.npz [STUDENT.pt] [--rows 1000000] [--epochs 6]"""
import os, sys, zlib
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nn_model import Prep, load, student, teacher  # noqa: E402

A = sys.argv[1:]
arg = lambda k, d: type(d)(A[A.index(k) + 1]) if k in A else d
ROWS, EP, BS = arg("--rows", 1000000), arg("--epochs", 6), 4096
pos = [a for i, a in enumerate(A) if not a.startswith("--") and (i == 0 or not A[i - 1].startswith("--"))]
TPT, LAB = pos[0], pos[1]
SPT = pos[2] if len(pos) > 2 else None
dev = "cuda"
kG, kS, kC, kCF, COFF = 16, 44, 10, 22, 248  # layout 2 (nnrec.cpp)
FLAG = 21  # camp field: "our current target"

d = np.load(LAB, mmap_mode="r")
rng = np.random.default_rng(0)
idx = np.sort(rng.choice(len(d["game"]), min(ROWS, len(d["game"])), replace=False))
X = np.asarray(d["X"][idx])
game, keys = np.asarray(d["game"])[idx], d["keys"]
held = np.array([zlib.crc32(k.encode()) % 10 == 0 for k in keys])[game]
tr, te = np.where(~held)[0], np.where(held)[0]
Xt = torch.as_tensor(X).to(dev)
T = load(teacher(Prep()), TPT, dev).to(dev).eval()


@torch.no_grad()
def teacher_out(net):
    tg, bh = [], []
    for s in range(0, len(Xt), 16384):
        o = net(Xt[s:s + 16384])
        tg.append(o["target"].cpu()), bh.append(o["behaviour"].cpu())
    return torch.cat(tg).to(dev), torch.cat(bh).to(dev)


Tt, Tb = teacher_out(T)
Tt = torch.nan_to_num(Tt.float(), neginf=-1e4).clamp(min=-1e4)
t_arg = Tt.argmax(-1)
b_lab = (Tb.argmax(-1) == 1).float()
present = Xt[:, COFF::kCF][:, :kC] == 1
cur = Xt[:, COFF + FLAG::kCF][:, :kC] == 1
cur_slot = torch.where(cur.any(-1), cur.float().argmax(-1), torch.full((len(Xt),), -1, device=dev))
matter = t_arg != cur_slot
print(f"rows {len(X)}, held-out {len(te)}; on held-out rows the teacher moves away from its current target on "
      f"{100 * matter[te].float().mean():.1f}% and says bank on {100 * b_lab[te].mean():.1f}%", flush=True)


def slog(x):
    x = x.float()
    return torch.sign(x) * torch.log1p(x.abs())


ctx_raw = slog(Xt[:, :kG + kS])
camp_raw = slog(Xt[:, COFF:COFF + kC * kCF].reshape(-1, kC, kCF))
tr_t = torch.as_tensor(tr, device=dev)
te_t = torch.as_tensor(te, device=dev)
cm, cs = ctx_raw[tr_t].mean(0), ctx_raw[tr_t].std(0).clamp(min=1e-3)
mask = present[tr_t].unsqueeze(-1).float()
pm = (camp_raw[tr_t] * mask).sum((0, 1)) / mask.sum()
ps = (((camp_raw[tr_t] - pm) ** 2 * mask).sum((0, 1)) / mask.sum()).sqrt().clamp(min=1e-3)
CTX = (ctx_raw - cm) / cs
CAMP = ((camp_raw - pm) / ps) * present.unsqueeze(-1).float()
del ctx_raw, camp_raw


class Target(nn.Module):
    """c = linear(context); camp score: bilinear (hidden 0: x'Bc + a'x) or one hidden layer on (x, c); none slot from c."""

    def __init__(self, cdim, hidden):
        super().__init__()
        self.ctx, self.hidden = nn.Linear(kG + kS, cdim), hidden
        if hidden:
            self.net = nn.Sequential(nn.Linear(kCF + cdim, hidden), nn.ReLU(), nn.Linear(hidden, 1))
        else:
            self.B = nn.Parameter(torch.zeros(kCF, cdim))
            self.a = nn.Parameter(torch.zeros(kCF))
        self.none = nn.Linear(cdim, 1)

    def forward(self, cx, camp, pres):
        c = self.ctx(cx)
        if self.hidden:
            s = self.net(torch.cat([camp, c.unsqueeze(1).expand(-1, kC, -1)], -1)).squeeze(-1)
        else:
            s = (camp @ self.B * c.unsqueeze(1)).sum(-1) + camp @ self.a
        s = s.masked_fill(~pres, -1e4)
        return torch.cat([s, self.none(c)], -1)

    def macs(self):
        n = (kG + kS) * self.ctx.out_features + self.ctx.out_features
        return n + (kC * ((kCF + self.ctx.out_features) * self.hidden + self.hidden) if self.hidden else kCF * self.ctx.out_features + kC * 2 * kCF)


def fit(m, loss_fn):
    m = m.to(dev)
    opt = torch.optim.Adam(m.parameters(), lr=3e-3)
    steps = EP * (len(tr) // BS)
    sch = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=5e-3, total_steps=steps)
    for _ in range(EP):
        perm = tr_t[torch.randperm(len(tr_t), device=dev)]
        for s in range(0, len(perm) - BS + 1, BS):
            loss = loss_fn(m, perm[s:s + BS])
            opt.zero_grad(), loss.backward(), opt.step(), sch.step()
    return m.eval()


def tgt_loss(m, b):
    return F.kl_div(F.log_softmax(m(CTX[b], CAMP[b], present[b]), -1), F.softmax(Tt[b], -1), reduction="batchmean")


def report(name, pred, macs):
    a = (pred[te_t] == t_arg[te_t]).float()
    print(f"target {name:18s} MACs {macs:6d} | agreement all {100 * a.mean():.1f}%, moves {100 * a[matter[te_t]].mean():.1f}%", flush=True)


@torch.no_grad()
def predict(m):
    return torch.cat([m(CTX[s:s + 16384], CAMP[s:s + 16384], present[s:s + 16384]).argmax(-1) for s in range(0, len(X), 16384)])


if SPT:
    S = load(student(T.prep), SPT, dev).to(dev).eval()
    St, Sb = teacher_out(S)
    report("student (ref)", torch.nan_to_num(St.float(), neginf=-1e4).argmax(-1), 28000)
    s_b = (Sb.argmax(-1) == 1).float()
    print(f"bank   student (ref)      | agreement all {100 * (s_b[te_t] == b_lab[te_t]).float().mean():.1f}%, teacher-bank rows "
          f"{100 * s_b[te_t][b_lab[te_t] == 1].mean():.1f}%", flush=True)
report("always current", torch.where(cur_slot >= 0, cur_slot, torch.full_like(cur_slot, kC)), 0)
for cd, hid in ((4, 0), (8, 0), (16, 0), (4, 8), (8, 16), (16, 32)):
    m = fit(Target(cd, hid), tgt_loss)
    report(f"ctx {cd} hidden {hid}", predict(m), m.macs())

for hid in (0, 8, 16):
    m = nn.Linear(kG + kS, 1) if not hid else nn.Sequential(nn.Linear(kG + kS, hid), nn.ReLU(), nn.Linear(hid, 1))
    m = fit(m, lambda mm, b: F.binary_cross_entropy_with_logits(mm(CTX[b]).squeeze(-1), b_lab[b]))
    with torch.no_grad():
        p = torch.cat([(m(CTX[s:s + 16384]).squeeze(-1) > 0).float() for s in range(0, len(X), 16384)])
    macs = (kG + kS) if not hid else (kG + kS) * hid + hid
    print(f"bank   hidden {hid:2d}          MACs {macs:6d} | agreement all {100 * (p[te_t] == b_lab[te_t]).float().mean():.1f}%, "
          f"teacher-bank rows {100 * p[te_t][b_lab[te_t] == 1].mean():.1f}%", flush=True)
