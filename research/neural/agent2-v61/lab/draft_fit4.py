"""Fine-tune the draft net (draft_net.h: 53 -> 64 tanh -> 1 logit, P(win)) on self-play lab games (draft_data4.js).

Rows mirror draft.cpp ml_draft_pick at each of a team's picks: 16 map features, our picks including this one (16+c),
their picks from completed draft rounds (28+c), team size one-hot (40..42), picking first (43, always 1: the engine
shows only completed rounds), progress j/size (44); plan inputs 45..52 stay 0. Label: that team's result.
Training starts from the shipped weights with an L2 pull toward them (keeps what the ladder data taught); maps are
split into train / validation groups so the check never sees a training map.

usage: python draft_fit4.py data.jsonl feats.json draft_net.h out_draft_net.h [l2=1e-3] [epochs=300] [lr=0.01]
"""
import json
import re
import sys

import numpy as np

data_f, feat_f, net_f, out_f = sys.argv[1:5]
L2 = float(sys.argv[5]) if len(sys.argv) > 5 else 1e-3
EPOCHS = int(sys.argv[6]) if len(sys.argv) > 6 else 300
LR = float(sys.argv[7]) if len(sys.argv) > 7 else 0.01
KIN, KH = 53, 64


def load_net(p):
    t = open(p, encoding="utf-8").read()
    arr = lambda name: np.array([float(x.rstrip("f")) for x in re.search(name + r"\[\d+\] = \{([^}]*)\}", t).group(1).split(",") if x.strip()], dtype=np.float64)
    W1 = arr("W1").reshape(KIN, KH)
    b1, w2 = arr("b1"), arr("w2")
    b2 = float(re.search(r"b2 = ([-0-9.e]+)f", t).group(1))
    return W1, b1, w2, b2, t


feats = json.load(open(feat_f))
X, Y, G = [], [], []
maps = {}
for line in open(data_f):
    g = json.loads(line)
    if g.get("error") or not g.get("seq"):
        continue
    f = feats[g["map"]]
    picks = [[c for t, c in g["seq"] if t == side] for side in (0, 1)]
    sz = len(picks[0])
    if sz < 3 or sz != len(picks[1]):
        continue
    for side in (0, 1):
        us, them = g["gems"][side], g["gems"][1 - side]
        y = 1.0 if us > them else 0.5 if us == them else 0.0
        for j in range(1, sz + 1):
            x = np.zeros(KIN)
            x[:16] = f[side]
            for c in picks[side][:j]:
                x[16 + c] = 1.0
            for c in picks[1 - side][: j - 1]:
                x[28 + c] = 1.0
            x[40 + min(max(sz, 3), 5) - 3] = 1.0
            x[43] = 1.0
            x[44] = j / sz
            X.append(x), Y.append(y), G.append(maps.setdefault(g["map"], len(maps)))
X, Y, G = np.array(X), np.array(Y), np.array(G)
rng = np.random.default_rng(0)
val_maps = set(rng.choice(len(maps), size=max(1, len(maps) // 5), replace=False).tolist())
va = np.array([g in val_maps for g in G])
print(f"rows {len(X)} from {len(maps)} maps; validation maps {len(val_maps)} ({va.sum()} rows)")

W1o, b1o, w2o, b2o, text = load_net(net_f)


def forward(P, X):
    W1, b1, w2, b2 = P
    h = np.tanh(X @ W1 + b1)
    return h, h @ w2 + b2


def loss(P, X, Y):
    _, z = forward(P, X)
    p = 1 / (1 + np.exp(-z))
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-np.mean(Y * np.log(p) + (1 - Y) * np.log(1 - p))), float(np.mean((p > 0.5) == (Y > 0.5)))


P0 = [W1o.copy(), b1o.copy(), w2o.copy(), b2o]
print("shipped net   train %.4f / %.3f   val %.4f / %.3f" % (*loss(P0, X[~va], Y[~va]), *loss(P0, X[va], Y[va])))
print("constant 0.5  val %.4f" % np.log(2))

P = [W1o.copy(), b1o.copy(), w2o.copy(), b2o]
m = [np.zeros_like(W1o), np.zeros_like(b1o), np.zeros_like(w2o), 0.0]
v = [np.zeros_like(W1o), np.zeros_like(b1o), np.zeros_like(w2o), 0.0]
Xt, Yt = X[~va], Y[~va]
best = (1e9, None)
for ep in range(1, EPOCHS + 1):
    h, z = forward(P, Xt)
    p = 1 / (1 + np.exp(-z))
    dz = (p - Yt) / len(Xt)
    gw2, gb2 = h.T @ dz, dz.sum()
    dh = np.outer(dz, P[2]) * (1 - h * h)
    gW1, gb1 = Xt.T @ dh, dh.sum(0)
    grads = [gW1 + L2 * (P[0] - W1o), gb1 + L2 * (P[1] - b1o), gw2 + L2 * (P[2] - w2o), gb2]
    for i in range(4):
        m[i] = 0.9 * m[i] + 0.1 * grads[i]
        v[i] = 0.999 * v[i] + 0.001 * grads[i] * grads[i]
        P[i] = P[i] - LR * (m[i] / (1 - 0.9 ** ep)) / (np.sqrt(v[i] / (1 - 0.999 ** ep)) + 1e-8)
    if ep % 25 == 0 or ep == EPOCHS:
        lv = loss(P, X[va], Y[va])
        print("epoch %d  train %.4f / %.3f  val %.4f / %.3f" % (ep, *loss(P, Xt, Yt), *lv))
        if lv[0] < best[0]:
            best = (lv[0], [a.copy() if isinstance(a, np.ndarray) else a for a in P], ep)
print("best validation %.4f at epoch %d" % (best[0], best[2]))
W1, b1, w2, b2 = best[1]


def fmt(a):
    return ",".join("%.9gf" % x for x in np.ravel(a))


t = re.sub(r"W1\[\d+\] = \{[^}]*\}", "W1[%d] = {%s}" % (W1.size, fmt(W1)), text)
t = re.sub(r"b1\[\d+\] = \{[^}]*\}", "b1[%d] = {%s}" % (b1.size, fmt(b1)), t)
t = re.sub(r"w2\[\d+\] = \{[^}]*\}", "w2[%d] = {%s}" % (w2.size, fmt(w2)), t)
t = re.sub(r"b2 = [-0-9.e]+f", "b2 = %.9gf" % b2, t)
t = t.replace("// Fine-tuned on recent ranked games by tools/train.py.",
              "// Fine-tuned on recent ranked games by tools/train.py, then on engine 2.0.0 self-play lab games (agent2/lab/draft_fit4.py).", 1)
open(out_f, "w", encoding="utf-8", newline="\n").write(t)
print("wrote", out_f)
