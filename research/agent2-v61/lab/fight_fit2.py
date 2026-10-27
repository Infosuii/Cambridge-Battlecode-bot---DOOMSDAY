"""E69 multi-horizon fight / flee / regroup analysis on fight_cf4.js rows with outcomes at 10 / 25 / 50 / 100 rounds.
For each training horizon h, a network (fight_fit.train) predicts the change of each forced action against the bot's
own verdict in team gem margin after h rounds; on held-out maps (5 folds grouped by map) the policy "best predicted
action when it beats our own by > tau" is scored by the real 100-round and 50-round changes and the final result.
With an output path, writes fight_net.h trained on horizon H_OUT.
usage: python fight_fit2.py rows.jsonl [out_header] [H_OUT=25]"""
import json
import sys

import numpy as np

rows = [json.loads(l) for l in open(sys.argv[1])]
rows = [r for r in rows if all(r.get("hz", {}).get(a) and all(str(h) in r["hz"][a] for h in (10, 25, 50)) for a in ("own", "fight", "run", "regroup"))]
out = sys.argv[2] if len(sys.argv) > 2 else None
H_OUT = int(sys.argv[3]) if len(sys.argv) > 3 else 25
ACTS = ["fight", "run", "regroup"]
X = np.array([r["f"] for r in rows])


def target(h):
    if h == 100:
        return np.array([[r["d"][a] - r["d"]["own"] for a in ACTS] for r in rows], float)
    return np.array([[r["hz"][a][str(h)]["d"] - r["hz"]["own"][str(h)]["d"] for a in ACTS] for r in rows], float)


T = {h: target(h) for h in (10, 25, 50, 100)}
W = np.array([[r["win"][a] - r["win"]["own"] for a in ACTS] for r in rows], float)
maps = sorted({r["map"] for r in rows})
fold = np.array([maps.index(r["map"]) % 5 for r in rows])
print(f"rows {len(rows)} on {len(maps)} maps")
for h, Y in T.items():
    print(f"  h{h:3d}: mean change vs own " + ", ".join(f"{a} {Y[:, i].mean():+.2f}" for i, a in enumerate(ACTS)) +
          f" | oracle {np.maximum(0, Y.max(1)).mean():.1f} per decision")

# train / predict: the same small network as fight_fit.py
HID, EPOCHS = 32, 400


def train(Xt, Yt, seed=0):
    rng = np.random.default_rng(seed)
    mu, sd = Xt.mean(0), Xt.std(0) + 1e-6
    Z = (Xt - mu) / sd
    P = [rng.normal(0, 0.3, (Z.shape[1], HID)), np.zeros(HID), rng.normal(0, 0.1, (HID, Yt.shape[1])), np.zeros(Yt.shape[1])]
    m = [np.zeros_like(p) for p in P]; v = [np.zeros_like(p) for p in P]
    ys = Yt.std() + 1e-6
    Y = np.clip(Yt / ys, -5, 5)
    for ep in range(1, EPOCHS + 1):
        hh = np.tanh(Z @ P[0] + P[1]); y = hh @ P[2] + P[3]
        g = (y - Y) / len(Z)
        grads = [Z.T @ ((g @ P[2].T) * (1 - hh * hh)) + 1e-3 * P[0], ((g @ P[2].T) * (1 - hh * hh)).sum(0), hh.T @ g + 1e-3 * P[2], g.sum(0)]
        for i, gr in enumerate(grads):
            m[i] = 0.9 * m[i] + 0.1 * gr; v[i] = 0.999 * v[i] + 0.001 * gr * gr
            P[i] -= 0.01 * (m[i] / (1 - 0.9 ** ep)) / (np.sqrt(v[i] / (1 - 0.999 ** ep)) + 1e-8)
    return mu, sd, P, ys


def predict(model, Xq):
    mu, sd, P, ys = model
    return (np.tanh(((Xq - mu) / sd) @ P[0] + P[1]) @ P[2] + P[3]) * ys


idx = np.arange(len(rows))
for h, Y in T.items():
    pred = np.zeros_like(Y)
    for k in range(5):
        tr, te = fold != k, fold == k
        pred[te] = predict(train(X[tr], Y[tr], seed=k), X[te])
    corr = [np.corrcoef(pred[:, i], Y[:, i])[0, 1] for i in range(3)]
    print(f"train on h{h}: held-out corr " + ", ".join(f"{a} {c:+.3f}" for a, c in zip(ACTS, corr)))
    for tau in (0, 10, 25):
        best = pred.argmax(1)
        act = pred.max(1) > tau
        res = {hh: np.where(act, T[hh][idx, best], 0.0) for hh in (50, 100)}
        wr = np.where(act, W[idx, best], 0.0)
        print(f"    tau {tau:2d}: acts {100 * act.mean():4.1f}% | real 100-round gain {res[100].mean():+.2f} +- {res[100].std() / np.sqrt(len(idx)):.2f}, "
              f"50-round {res[50].mean():+.2f}, win share {wr.mean():+.4f}; actions " + ", ".join(f"{a} {int((act & (best == i)).sum())}" for i, a in enumerate(ACTS)))
if out:
    mu, sd, P, ys = train(X, T[H_OUT], seed=9)
    f = lambda a: ",".join("%.6gf" % x for x in np.ravel(a))
    txt = (f"// Fight / flee / regroup model (agent2/lab/fight_fit2.py, E69): {len(rows)} counterfactual contacts, trained on the\n"
           f"// {H_OUT}-round team gem change of forced fight / run / regroup versus the bot's own verdict.\n#pragma once\nnamespace fight_net {{\n"
           f"inline constexpr int kIn = {X.shape[1]}, kHid = {HID}, kOut = 3;\n"
           f"inline constexpr float kMu[kIn] = {{{f(mu)}}};\ninline constexpr float kSd[kIn] = {{{f(sd)}}};\n"
           f"inline constexpr float W1[kIn * kHid] = {{{f(P[0])}}};\ninline constexpr float b1[kHid] = {{{f(P[1])}}};\n"
           f"inline constexpr float W2[kHid * kOut] = {{{f(P[2])}}};\ninline constexpr float b2[kOut] = {{{f(P[3])}}};\n"
           f"inline constexpr float kScale = {ys:.6g}f;\n}} // namespace fight_net\n")
    open(out, "w", newline="\n").write(txt)
    print("wrote", out)
