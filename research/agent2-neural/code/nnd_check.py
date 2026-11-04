"""E123: on one game of an A2_NN_DBG build, compare the logits the bot printed with PyTorch's on the same features. The heads: behaviour (8), target (11).
usage (project root): [NN_STUDENT=ExT] python -P agent2/lab/nnd_check.py BOT WEIGHTS.pt teacher|student OPP MAP(file in v4/maps, no extension)"""
import base64, os, shutil, subprocess, sys, zipfile
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from nn_model import Prep, load, student, teacher  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
V4 = os.path.join(ROOT, "v4")
BOT, PT, KIND, OPP, MAP = sys.argv[1:6]
tag = f"bench_out/nndk_{BOT}"
shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
os.makedirs(os.path.join(V4, tag))
f = f"{tag}/g"
man = os.path.join(V4, f".m_nndk_{BOT}.txt")
open(man, "w").write(f"bots/{BOT} bots/{OPP} maps/{MAP}.map26a {f}.repl26a --statistics {f}.json --json\n")
subprocess.run([os.path.join(V4, "cambc.exe"), "run-batch", man, "--jobs", "1", "--json", "--color", "never", "--release", "--fuel-quantum", "20000000", "--log-limit", "67108864"],
               cwd=V4, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
txt = zipfile.ZipFile(os.path.join(V4, tag, "g.repl26a")).read("team-a.stdout").replace(b"\0", b"").decode("utf-8", "replace")
rows = []
for l in txt.splitlines():
    if l.startswith("NND "):
        q = l.split()
        rows.append((int(q[1]), int(q[2]), np.frombuffer(base64.b64decode(q[5]), np.int16), np.array([float(v) for v in q[6:]], np.float32)))
print(len(rows), "rows")
net = load((teacher if KIND == "teacher" else student)(Prep()), PT).eval()
X = torch.as_tensor(np.stack([r[2] for r in rows]))
with torch.no_grad():
    o = net(X)
P = torch.cat([o["behaviour"], o["target"]], 1).numpy()
C = np.stack([r[3] for r in rows])
d = np.abs(P - C)
d[(C < -1e8) | (P < -1e8)] = 0
print(f"bot vs PyTorch logits: mean abs {d.mean():.5f}, median of row max {np.median(d.max(1)):.5f}, p90 {np.quantile(d.max(1), 0.9):.5f}, max {d.max():.4f}")
print(f"behaviour part: mean {d[:, :8].mean():.5f} max {d[:, :8].max():.4f}; target part: mean {d[:, 8:].mean():.5f} max {d[:, 8:].max():.4f}")
same = (P[:, 8:].argmax(1) == C[:, 8:].argmax(1)).mean()
print(f"same target argmax {100 * same:.1f}%")
w = np.argsort(-d.max(1))[:3]
for i in w:
    print(f" worst round {rows[i][0]} slot {rows[i][1]}: largest differences at output {np.argsort(-d[i])[:4].tolist()}: bot {C[i][np.argsort(-d[i])[:4]].round(3).tolist()} pytorch {P[i][np.argsort(-d[i])[:4]].round(3).tolist()}")
# intermediate values (A2_NN_DBGX builds): which block first differs?
nx = [np.array([float(v) for v in l.split()[1:]], np.float32) for l in txt.splitlines() if l.startswith("NNX")]
nh = [np.array([float(v) for v in l.split()[1:]], np.float32) for l in txt.splitlines() if l.startswith("NNH")]
if nx:
    from nn_model import BLK, split_blocks  # noqa: E402
    m = len(nx)
    Xs = X[:m]
    with torch.no_grad():
        B = split_blocks(Xs)
        Pp = net.prep(B)
        emb = {k: net.enc[k](Pp[k]) for k in BLK}
        parts, names = [emb["g"][:, 0], emb["s"][:, 0]], ["g", "s"]
        for k in ("a", "e", "c", "l"):
            mk = (B[k][..., 0] != 0).unsqueeze(-1).float()
            parts += [(emb[k] * mk).sum(1) / mk.sum(1).clamp_min(1.0), (emb[k] - 1e4 * (1 - mk)).max(1).values * (mk.sum(1) > 0).float()]
            names += [k + " mean", k + " max"]
        ed = net.enc_dim
        xp = torch.cat(parts, -1).numpy()
    xc = np.stack(nx)
    print("pooled input, mean abs difference per block:", {n: round(float(np.abs(xp[:, j * ed:(j + 1) * ed] - xc[:, j * ed:(j + 1) * ed]).mean()), 5) for j, n in enumerate(names)})
    for k in ("a", "e", "c", "l", "g", "s"):
        ok = net.enc[k]
    with torch.no_grad():
        h = net.trunk[1](net.trunk[0](torch.as_tensor(xc)))
        h1 = net.trunk[3](net.trunk[2](h))
    hc = np.stack(nh)
    T = h.shape[1]
    print("trunk layer 0 from the bot's pooled input: mean abs", float(np.abs(h.numpy() - hc[:, :T]).mean()), "; layer 1:", float(np.abs(h1.numpy() - hc[:, T:]).mean()))
shutil.rmtree(os.path.join(V4, tag), ignore_errors=True)
