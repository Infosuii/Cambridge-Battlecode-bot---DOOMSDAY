"""Neural bot fuel fit: distil an RL teacher into the small student (encoder 1 x 16, trunk 2 x 64) for the shipped bot.
The student matches the teacher's distributions (KL, temperature 1) on the heads the bot reads - behaviour (bank gate),
target, option - plus the teacher's attack / cast heads at a lower weight, on recorded states (an nn_labels.py file;
rows are states, labels unused). Held-out by map: agreement of the student's argmax with the teacher's per head.
usage: python -P nn_distill.py TEACHER.pt LABELS.npz OUT_STUDENT.pt [--rows 1500000] [--epochs 8] [--move-weight W]
--move-weight W (E121): rows where the teacher moves off its current target, and rows where it banks, count W times."""
import os, sys, time, zlib
import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nn_model import Prep, load, student, teacher  # noqa: E402

A = sys.argv[1:]
TPT, LAB, OUT = A[0], A[1], A[2]
arg = lambda k, d: type(d)(A[A.index(k) + 1]) if k in A else d
ROWS, EP, BS = arg("--rows", 1500000), arg("--epochs", 8), 2048
MW = arg("--move-weight", 1.0)
COFF, KCF, FLAG = 248, 22, 21  # layout 2: camp block offset, fields per camp, "our current target" field
W = {"behaviour": 1.0, "target": 1.0, "option": 1.0, "attack": 0.3, "cast": 0.3, "cast_tgt": 0.3}
dev = "cuda"
d = np.load(LAB, mmap_mode="r")
n_all = len(d["game"])
rng = np.random.default_rng(0)
idx = np.sort(rng.choice(n_all, min(ROWS, n_all), replace=False))
X = np.asarray(d["X"][idx]); game = np.asarray(d["game"])[idx]; keys = d["keys"]
held = np.array([zlib.crc32(k.encode()) % 10 == 0 for k in keys])[game]
tr, te = np.where(~held)[0], np.where(held)[0]
Xt = torch.as_tensor(X).to(dev)
T = load(teacher(Prep()), TPT, dev).to(dev).eval()
prep = T.prep
S = student(prep).to(dev)
print(f"rows {len(X)} (train {len(tr)}, held-out {len(te)}), student parameters {sum(p.numel() for p in S.parameters())}", flush=True)
opt = torch.optim.Adam(S.parameters(), lr=2e-3)
steps = EP * (len(tr) // BS)
sch = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=3e-3, total_steps=steps)


def moves(xb, to):
    """Rows where the teacher's target is not the current target."""
    c = xb[:, COFF + FLAG::KCF][:, :10] == 1
    cur = torch.where(c.any(-1), c.float().argmax(-1), torch.full((len(xb),), -1, device=dev))
    return to["target"].argmax(-1) != cur


def agree():
    S.eval()
    hit = {h: [0, 0] for h in W}
    hit["moves"], hit["bank"] = [0, 0], [0, 0]
    with torch.no_grad():
        for s0 in range(0, len(te), 8192):
            xb = Xt[torch.as_tensor(te[s0:s0 + 8192], device=dev)]
            to, so = T(xb), S(xb)
            for h in W:
                hit[h][0] += (to[h].argmax(-1) == so[h].argmax(-1)).sum().item(); hit[h][1] += len(xb)
            m, b = moves(xb, to), to["behaviour"].argmax(-1) == 1
            hit["moves"][0] += (to["target"].argmax(-1) == so["target"].argmax(-1))[m].sum().item(); hit["moves"][1] += m.sum().item()
            hit["bank"][0] += (so["behaviour"].argmax(-1) == 1)[b].sum().item(); hit["bank"][1] += b.sum().item()
    S.train()
    return {h: a / max(1, b) for h, (a, b) in hit.items()}


t0 = time.time()
for ep in range(EP):
    perm = rng.permutation(tr)
    tot = 0.0
    for s0 in range(0, len(perm) - BS + 1, BS):
        xb = Xt[torch.as_tensor(perm[s0:s0 + BS], device=dev)]
        with torch.no_grad():
            to = T(xb)
        so = S(xb)
        rw = {"target": 1 + (MW - 1) * moves(xb, to).float(), "behaviour": 1 + (MW - 1) * (to["behaviour"].argmax(-1) == 1).float()}
        loss = sum(w * (F.kl_div(F.log_softmax(so[h], -1), F.softmax(to[h], -1), reduction="none").sum(-1) * rw.get(h, 1.0)).mean()
                   for h, w in W.items())
        opt.zero_grad(); loss.backward(); opt.step(); sch.step()
        tot += loss.item()
    a = agree()
    print(f"epoch {ep + 1}: KL {tot / max(1, len(perm) // BS):.4f}, {time.time() - t0:.0f}s | student = teacher argmax on held-out maps: " +
          ", ".join(f"{h} {v:.3f}" for h, v in a.items()), flush=True)
torch.save(S.state_dict(), OUT)
print("saved", OUT)
