"""Neural bot step 2/3: teacher by imitation of v92 (nn_labels.py output), then the student distilled from the teacher.
Split by map (10% of map keys held out). Reports per-head held-out accuracy, and on the informative rows (attack /
cast rows where v92 acted; step rows where it moved).
usage: python -P nn_train.py LABELS.npz OUTDIR [--epochs 6] [--student-epochs 6] [--batch 2048]"""
import json, os, sys, time, zlib
import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nn_model import HEADS, Prep, losses, student, teacher  # noqa: E402

A = sys.argv[1:]
LAB, OUT = A[0], A[1]
arg = lambda k, d: type(d)(A[A.index(k) + 1]) if k in A else d
EP, SEP, BS = arg("--epochs", 6), arg("--student-epochs", 6), arg("--batch", 2048)
os.makedirs(OUT, exist_ok=True)
dev = "cuda" if torch.cuda.is_available() else "cpu"
d = np.load(LAB)
X, Y, game, keys = d["X"], d["Y"], d["game"], d["keys"]
held = np.array([zlib.crc32(k.encode()) % 10 == 0 for k in keys])[game]
tr, te = np.where(~held)[0], np.where(held)[0]
print(f"{dev}: rows {len(X)}, train {len(tr)}, held-out {len(te)} ({held[game].sum() if False else len(set(game[te]))} games)", flush=True)
prep = Prep(Prep.fit_stats(X[tr[np.random.default_rng(0).choice(len(tr), min(len(tr), 300000), replace=False)]]))
Xt, Yt = torch.as_tensor(X), torch.as_tensor(Y)
if dev == "cuda" and X.nbytes < 4.5e9:
    # whole dataset in GPU memory (RTX 5060, 8 GB): batches are gathered on the GPU, no host copies per step
    Xt, Yt = Xt.to(dev), Yt.to(dev)
    print(f"dataset on GPU: {X.nbytes / 1e9:.2f} GB", flush=True)
gi = lambda idx: torch.as_tensor(idx, device=Xt.device)


def evaluate(net):
    net.eval()
    hit = {h: [0, 0] for h in HEADS}
    inf = {"step-moved": [0, 0], "attack-acted": [0, 0], "cast-acted": [0, 0], "target": [0, 0]}
    with torch.no_grad():
        for s in range(0, len(te), 8192):
            idx = te[s:s + 8192]
            out = net(Xt[gi(idx)].to(dev))
            y = Yt[gi(idx)].to(dev).long()
            for j, h in enumerate(HEADS):
                m = y[:, j] >= 0
                p = out[h].argmax(-1)
                hit[h][0] += (p[m] == y[m, j]).sum().item(); hit[h][1] += m.sum().item()
            for name, j, cond in (("step-moved", 2, y[:, 2] != 8), ("attack-acted", 3, y[:, 3] != 18), ("cast-acted", 4, y[:, 4] != 0)):
                p = out[HEADS[j]].argmax(-1)
                inf[name][0] += (p[cond] == y[cond, j]).sum().item(); inf[name][1] += cond.sum().item()
    net.train()
    return {h: a / max(1, b) for h, (a, b) in hit.items()}, {h: a / max(1, b) for h, (a, b) in inf.items() if b}


def fit(net, epochs, distil_from=None, tag=""):
    net.to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    steps = epochs * (len(tr) // BS)
    sch = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=2e-3, total_steps=steps)
    rng = np.random.default_rng(1)
    t0 = time.time()
    for ep in range(epochs):
        perm = rng.permutation(tr)
        tot = 0.0
        for s in range(0, len(perm) - BS + 1, BS):
            idx = perm[s:s + BS]
            xb, yb = Xt[gi(idx)].to(dev), Yt[gi(idx)].to(dev)
            out = net(xb)
            loss, _ = losses(out, yb)
            if distil_from is not None:
                with torch.no_grad():
                    tout = distil_from(xb)
                kl = 0.0
                for h in HEADS:
                    kl = kl + F.kl_div(F.log_softmax(out[h], -1), F.softmax(tout[h], -1), reduction="batchmean")
                loss = 0.5 * loss + kl
            opt.zero_grad(); loss.backward(); opt.step(); sch.step()
            tot += loss.item()
        acc, inf = evaluate(net)
        print(f"{tag} epoch {ep + 1}: loss {tot / max(1, len(perm) // BS):.4f}, {time.time() - t0:.0f}s | held-out " +
              ", ".join(f"{h} {a:.3f}" for h, a in acc.items()) + " | " + ", ".join(f"{h} {a:.3f}" for h, a in inf.items()), flush=True)
    return net


T = fit(teacher(prep), EP, tag="teacher")
torch.save(T.state_dict(), os.path.join(OUT, "teacher.pt"))
T.eval()
S = fit(student(prep), SEP, distil_from=T, tag="student")
torch.save(S.state_dict(), os.path.join(OUT, "student.pt"))
print("parameters: teacher", sum(p.numel() for p in T.parameters()), "student", sum(p.numel() for p in S.parameters()))
