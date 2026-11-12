"""E124: what do the blend's overrides of v92 look like? Field by field: the camp the network moves to against the camp v92 picked, on rows where the blend overrides, by map set; also round, slot and how far v92's pick is from the current target.
A rule found here could go into v92's own scoring at no fuel. usage (project root): python -P agent2/lab/nn_ens_why.py ROWS.npz STUDENT.pt"""
import os, sys
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nn_model import BLK, Prep, load, student  # noqa: E402

ROWS, SPT = sys.argv[1:3]
dev = "cuda"
COFF, CN, CW = BLK["c"]
d = np.load(ROWS)
X = torch.as_tensor(d["X"]).to(dev)
V = torch.as_tensor(d["v92g"]).to(dev)
meta, game, off = d["meta"], d["game"], d["off"][d["game"]]
S = load(student(Prep()), SPT, dev).to(dev).eval()
with torch.no_grad():
    T = torch.cat([S(X[s:s + 8192])["target"] for s in range(0, len(X), 8192)])
g = X[:, COFF + 1::CW][:, :CN].long()
pres = X[:, COFF::CW][:, :CN] != 0
fl = ((g == V.unsqueeze(1)) & pres).float()
ff = 1.0 - fl.max(1).values
Tb = T.clone()
Tb[:, :CN] += 2.0 * fl
Tb[:, CN] += 2.0 * ff
tv = torch.where(ff > 0, torch.full_like(ff, CN).long(), fl.argmax(1))
ch = Tb.argmax(1)
over = (ch != tv) & (ch < CN) & (tv < CN)
print(f"rows {len(X)}, overrides with both camps in view {over.sum().item()}; choice is 'far' {(ch == CN).sum().item()}; v92's pick out of view {(tv == CN).sum().item()}")
NAMES = ["present", "group", "dx", "dy", "cheb d", "gems", "gold", "state", "respawn in", "hp left", "max hp", "strength x10", "harmless", "rounds since enemy", "claims", "allies near", "walk d", "side margin", "altar d", "spawn d", "allies closer", "current target"]
idx = over.nonzero().squeeze(1)
cam = X[idx][:, COFF:COFF + CN * CW].reshape(-1, CN, CW).float()
a = cam[torch.arange(len(idx)), ch[idx]].cpu().numpy()
b = cam[torch.arange(len(idx)), tv[idx]].cpu().numpy()
ofl = off[idx.cpu().numpy()]
for name, m in (("official", ofl), ("generated", ~ofl)):
    print(f"\n{name}: {int(m.sum())} overrides. Field: network's camp vs v92's camp, mean (share where network's is higher / lower)")
    for i, n in enumerate(NAMES):
        if i in (0, 1):
            continue
        x, y = a[m, i], b[m, i]
        print(f"  {n:20s} {x.mean():9.2f} vs {y.mean():9.2f}   higher {100 * (x > y).mean():4.0f}%  lower {100 * (x < y).mean():4.0f}%")
r = meta[idx.cpu().numpy(), 0]
print("\nrounds of overrides, by 250:", np.histogram(r, bins=[0, 250, 500, 750, 1000, 1250, 1500, 2000, 4000])[0].tolist())
allr = meta[:, 0]
print("all rows, by 250:          ", np.histogram(allr, bins=[0, 250, 500, 750, 1000, 1250, 1500, 2000, 4000])[0].tolist())
gap = (Tb[idx, ch[idx]] - Tb[idx, tv[idx]]).cpu().numpy()
print("margin of the override over v92's pick after the bonus: median", float(np.median(gap)), "p90", float(np.quantile(gap, 0.9)))
print("override moves off the current target:", float((b[:, 21] == 1).mean()), "; to it:", float((a[:, 21] == 1).mean()))
