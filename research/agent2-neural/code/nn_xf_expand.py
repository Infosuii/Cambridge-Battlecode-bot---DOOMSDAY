"""E123: student for layout 2 (500 features) -> the same student on layout 4 (A2_NN_XF, 556 features), new inputs at zero weight, so behaviour starts unchanged.
Checks that the logits do not depend on the new fields. usage (project root): [NN_STUDENT=ExT] python -P agent2/lab/nn_xf_expand.py IN.pt OUT.pt"""
import os, subprocess, sys
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
IN, OUT = sys.argv[1:3]
if os.environ.get("NN_LAYOUT") != "4":
    os.environ["NN_LAYOUT"] = "4"
    sys.exit(subprocess.run([sys.executable, "-P", os.path.abspath(__file__), IN, OUT], env=os.environ).returncode)
from nn_model import BLK, NFEAT, Prep, student  # noqa: E402

sd = torch.load(IN, map_location="cpu")
OLD = {"g": 16, "c": 22}  # layout 2 widths
new = {k: BLK[k][2] - w for k, w in OLD.items()}
for k, m in new.items():
    sd[f"prep.mu_{k}"] = torch.cat([sd[f"prep.mu_{k}"], torch.zeros(m)])
    sd[f"prep.sd_{k}"] = torch.cat([sd[f"prep.sd_{k}"], torch.ones(m)])
    w = sd[f"enc.{k}.0.weight"]
    sd[f"enc.{k}.0.weight"] = torch.cat([w, torch.zeros(w.shape[0], m)], 1)
net = student(Prep())
missing, unexpected = net.load_state_dict(sd, strict=False)
assert not missing and not unexpected, (missing, unexpected)
torch.save(net.state_dict(), OUT)
net.eval()
X = torch.randint(0, 400, (64, NFEAT), dtype=torch.int16)
X2 = X.clone()
for k, m in new.items():
    o, n, w = BLK[k]
    for e in range(n):
        X[:, o + e * w + w - m:o + e * w + w] = 0
        X2[:, o + e * w + w - m:o + e * w + w] = torch.randint(1, 200, (64, m), dtype=torch.int16)
with torch.no_grad():
    a, b = net(X), net(X2)
d = max((a[h] - b[h]).abs().max().item() for h in ("target", "behaviour", "option"))
print(f"wrote {OUT}: new inputs {new}; largest logit change from the new fields at zero weight: {d:.6f}")
assert d < 1e-5
