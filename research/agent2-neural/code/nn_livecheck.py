"""E123: does the deployed scoring (A2_NN_LIVE: incremental camp encoder + staged summary) reproduce PyTorch? Plays a few games with the rollout build and compares the logged log-probability
of each row with the trainer's recomputation, and the full logits' argmax. usage (project root): [NN_ENS=a] python -P agent2/lab/nn_livecheck.py WEIGHTS.pt [GAMES]"""
import os, random, shutil, subprocess, sys, zipfile
import numpy as np
import torch
import torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PT = sys.argv[1]
GAMES = int(sys.argv[2]) if len(sys.argv) > 2 else 16
WD = os.path.join(os.environ.get("TEMP", "."), "nn_livecheck")
sys.argv = ["nn_rl4", WD, PT, "0"]
import nn_rl4 as R  # noqa: E402
from nn_model import Prep, load, student  # noqa: E402

R.FLAGS.append("A2_NN_LAZY=1") if os.environ.get("NN_LAZY") == "1" else None
dev = R.dev
net = load(student(Prep()), PT, dev).to(dev).eval()
wh = os.path.join(WD, "w.h")
subprocess.run([sys.executable, "-P", os.path.join(R.LAB, "nn_export.py"), PT, "student", wh], check=True, capture_output=True)
shutil.rmtree(os.path.join(R.V4, "bots", "nnqc"), ignore_errors=True)
R.build("nnqc", wh, rl=True)
rng = random.Random(5)
maps = [("maps", m) for m in R.maplist("maps")]
tag = os.path.join("bench_out", "nnq", "lc")
shutil.rmtree(os.path.join(R.V4, tag), ignore_errors=True)
os.makedirs(os.path.join(R.V4, tag))
lines = []
games = []
for k in range(GAMES):
    s, m = rng.choice(maps)
    side = rng.choice("AB")
    a, b = ("nnqc", "v92") if side == "A" else ("v92", "nnqc")
    f = f"{tag}/g{k}".replace("\\", "/")
    lines.append(f"bots/{a} bots/{b} {s}/{m} {f}.repl26a --statistics {f}.json --json")
    games.append(side)
R.play(lines, tag, debug=True)
rows = []
for k, side in enumerate(games):
    try:
        txt = zipfile.ZipFile(os.path.join(R.V4, tag, f"g{k}.repl26a")).read(f"team-{side.lower()}.stdout").replace(b"\0", b"").decode("utf-8", "replace")
    except Exception as e:
        print("game", k, "unreadable", e)
        continue
    rows += R.parse_rows(txt)
print(len(rows), "rows")
X = torch.as_tensor(np.stack([r["x"] for r in rows])).to(dev)
XZ = torch.as_tensor(np.stack([r["xz"] for r in rows])).to(dev)
TA = torch.as_tensor([r["ta"] for r in rows]).to(dev)
BS = torch.as_tensor([r["bs"] for r in rows]).to(dev)
TLP = torch.as_tensor([r["tlp"] for r in rows], dtype=torch.float32).to(dev)
with torch.no_grad():
    lg = R.blend(torch.cat([R.live_logits(net, XZ[s:s + 8192], X[s:s + 8192]) for s in range(0, len(X), 8192)]), BS)
    lp = F.log_softmax(lg / R.TEMP, -1).gather(1, TA[:, None]).squeeze(1)
d = (lp - TLP).abs()
print(f"logged vs recomputed log-probability: median {d.median().item():.4f}, p90 {d.quantile(0.9).item():.4f}, p99 {d.quantile(0.99).item():.4f}, max {d.max().item():.3f}")
shutil.rmtree(os.path.join(R.V4, tag), ignore_errors=True)
