"""E124: the blend's overrides are mostly "stay on the current target" (v92 wants to switch, the network says stay). Among rows where v92's pick differs from the current target and the current target is in view:
when does the blend stay? Small decision trees on readable fields of the current target and of v92's pick, weighted back to all turns, held out by map. usage (project root): python -P agent2/lab/nn_ens_rule.py ROWS.npz STUDENT.pt"""
import os, sys, zlib
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nn_model import BLK, Prep, load, student  # noqa: E402
from sklearn.tree import DecisionTreeClassifier, export_text  # noqa: E402

ROWS, SPT = sys.argv[1:3]
dev = "cuda"
COFF, CN, CW = BLK["c"]
SOFF = BLK["s"][0]
d = np.load(ROWS)
X = torch.as_tensor(d["X"]).to(dev)
V = torch.as_tensor(d["v92g"]).to(dev)
NG = torch.as_tensor(d["ng"]).to(dev)
meta, game, keys = d["meta"], d["game"], d["keys"]
off = d["off"][game]
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
cur_flag = X[:, COFF + 21::CW][:, :CN] == 1
has_cur = cur_flag.any(1)
cur = cur_flag.float().argmax(1)
wt = torch.where(NG != V, torch.tensor(1.0, device=dev), torch.tensor(8.0, device=dev))
# rows: v92 wants to switch away from a current target in view, both camps in view
m = has_cur & (ff == 0) & (tv != cur)
idx = m.nonzero().squeeze(1)
stay = (ch[idx] == cur[idx]).cpu().numpy()
w = wt[idx].cpu().numpy()
print(f"rows {len(X)}; weighted turns {wt.sum().item():.0f}; v92 wants to switch on {100 * wt[idx].sum().item() / wt.sum().item():.1f}% of them; the blend stays on {100 * (w * stay).sum() / w.sum():.1f}% of those")
print(f"  official {100 * (w * stay)[off[idx.cpu().numpy()]].sum() / w[off[idx.cpu().numpy()]].sum():.1f}%, generated {100 * (w * stay)[~off[idx.cpu().numpy()]].sum() / w[~off[idx.cpu().numpy()]].sum():.1f}%")
NAMES = ["cheb", "gems", "gold", "state", "respawn", "hpleft", "maxhp", "str", "harmless", "enemyage", "claims", "alliesnear", "walk", "margin", "altar", "spawn", "closer"]
FI = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
cam = X[idx][:, COFF:COFF + CN * CW].reshape(-1, CN, CW).float()
A = cam[torch.arange(len(idx)), cur[idx]][:, FI].cpu().numpy()
B = cam[torch.arange(len(idx)), tv[idx]][:, FI].cpu().numpy()
sf = X[idx][:, SOFF:SOFF + 44].float().cpu().numpy()
SN = {1: "hp", 2: "maxhp", 6: "bag", 7: "gold", 32: "since_target", 33: "changes50", 39: "since_bank", 40: "since_contact"}
SEL = list(SN)
glob = X[idx][:, 0:16].float().cpu().numpy()
F = np.concatenate([A, B, A - B, sf[:, SEL], glob[:, [0, 1, 2, 15]]], 1)
fn = [f"cur_{n}" for n in NAMES] + [f"v92_{n}" for n in NAMES] + [f"diff_{n}" for n in NAMES] + [f"self_{SN[i]}" for i in SEL] + ["round", "our_score", "their_score", "near_enemy"]
held = np.array([zlib.crc32(k.encode()) % 5 == 0 for k in keys])[game[idx.cpu().numpy()]]
for depth in (1, 2, 3, 4, 6):
    t = DecisionTreeClassifier(max_depth=depth, min_weight_fraction_leaf=0.01, class_weight=None)
    t.fit(F[~held], stay[~held], sample_weight=w[~held])
    p = t.predict(F[held])
    acc = (w[held] * (p == stay[held])).sum() / w[held].sum()
    rec = (w[held] * (p & stay[held])).sum() / max(1e-6, (w[held] * stay[held]).sum())
    pre = (w[held] * (p & stay[held])).sum() / max(1e-6, (w[held] * p).sum())
    print(f"depth {depth}: held-out accuracy {100 * acc:.1f}%, stay recall {100 * rec:.1f}%, precision {100 * pre:.1f}%")
    if depth in (2, 3, 4):
        print(export_text(t, feature_names=fn, max_depth=depth, show_weights=False)[:2400])
base = max((w[held] * stay[held]).sum(), (w[held] * (~stay[held])).sum()) / w[held].sum()
print(f"always the commoner answer: {100 * base:.1f}%")
t = DecisionTreeClassifier(max_depth=6, min_weight_fraction_leaf=0.005)
t.fit(F[~held], stay[~held], sample_weight=w[~held])
imp = sorted(zip(t.feature_importances_, fn), reverse=True)[:14]
print("importance:", [(n, round(float(v), 3)) for v, n in imp])
# how long does a run of "v92 wants to switch" last, and how often does the same champion keep the current target until it ends?
EOF_NOTE = None
