"""Fight / flee / regroup model (E69) from fight_cf4.js rows: a small network predicts, from the 24 fight features at a
contact turn, how much each forced action changes the team gem margin over the next 100 rounds compared with the
bot's own verdict (targets d_fight - d_own, d_run - d_own, d_regroup - d_own). Evaluated by 5-fold cross-validation
grouped by map: the policy "take the best predicted action if it beats the bot's own by more than tau" is scored by
the real outcome of the chosen action on held-out maps. Writes fight_net.h (weights + feature scaling) for A2_FIGHTNET.
usage: python fight_fit.py rows.jsonl [out_header] [hidden=32] [epochs=400]"""
import json
import sys

import numpy as np

rows = [json.loads(l) for l in open(sys.argv[1])]
out = sys.argv[2] if len(sys.argv) > 2 else None
HID = int(sys.argv[3]) if len(sys.argv) > 3 else 32
EPOCHS = int(sys.argv[4]) if len(sys.argv) > 4 else 400
ACTS = ["fight", "run", "regroup"]
X = np.array([r["f"] for r in rows], dtype=np.float64)
D = np.array([[r["d"][a] - r["d"]["own"] for a in ACTS] for r in rows], dtype=np.float64)
Wn = np.array([[r["win"][a] - r["win"]["own"] for a in ACTS] for r in rows], dtype=np.float64)
maps = sorted({r["map"] for r in rows})
gid = np.array([maps.index(r["map"]) for r in rows])
print(f"rows {len(rows)}, maps {len(maps)}")
print("mean change vs own (gems / 100 rounds):", {a: round(float(D[:, i].mean()), 2) for i, a in enumerate(ACTS)})
print("share where action beats own by > 20 gems:", {a: round(float((D[:, i] > 20).mean()), 3) for i, a in enumerate(ACTS)},
      " worse by > 20:", {a: round(float((D[:, i] < -20).mean()), 3) for i, a in enumerate(ACTS)})
print("final-result change vs own (win share):", {a: round(float(Wn[:, i].mean()), 4) for i, a in enumerate(ACTS)})
print("oracle (best of own / actions) gain per decision:", round(float(np.maximum(0, D.max(1)).mean()), 2))


def train(Xt, Yt, seed=0):
    rng = np.random.default_rng(seed)
    mu, sd = Xt.mean(0), Xt.std(0) + 1e-6
    Z = (Xt - mu) / sd
    W1 = rng.normal(0, 0.3, (Z.shape[1], HID)); b1 = np.zeros(HID)
    W2 = rng.normal(0, 0.1, (HID, Yt.shape[1])); b2 = np.zeros(Yt.shape[1])
    P = [W1, b1, W2, b2]
    m = [np.zeros_like(p) for p in P]; v = [np.zeros_like(p) for p in P]
    ys = Yt.std() + 1e-6
    Y = np.clip(Yt / ys, -5, 5)  # robust: heavy tails
    for ep in range(1, EPOCHS + 1):
        h = np.tanh(Z @ P[0] + P[1]); y = h @ P[2] + P[3]
        g = (y - Y) / len(Z)
        gW2 = h.T @ g + 1e-3 * P[2]; gb2 = g.sum(0)
        dh = (g @ P[2].T) * (1 - h * h)
        gW1 = Z.T @ dh + 1e-3 * P[0]; gb1 = dh.sum(0)
        for i, gr in enumerate([gW1, gb1, gW2, gb2]):
            m[i] = 0.9 * m[i] + 0.1 * gr; v[i] = 0.999 * v[i] + 0.001 * gr * gr
            P[i] -= 0.01 * (m[i] / (1 - 0.9 ** ep)) / (np.sqrt(v[i] / (1 - 0.999 ** ep)) + 1e-8)
    return mu, sd, P, ys


def predict(model, Xq):
    mu, sd, P, ys = model
    return (np.tanh(((Xq - mu) / sd) @ P[0] + P[1]) @ P[2] + P[3]) * ys


folds = 5
rng = np.random.default_rng(1)
perm = rng.permutation(len(maps))
fold_of_map = {m: i % folds for i, m in enumerate(perm)}
fold = np.array([fold_of_map[g] for g in gid])
pred = np.zeros_like(D)
for k in range(folds):
    tr, te = fold != k, fold == k
    pred[te] = predict(train(X[tr], D[tr], seed=k), X[te])
for i, a in enumerate(ACTS):
    c = np.corrcoef(pred[:, i], D[:, i])[0, 1]
    print(f"held-out correlation, predicted vs real change ({a}): {c:.3f}")
print("policy on held-out maps (gain per decision vs the bot's own, real outcomes):")
for tau in (0, 5, 10, 20, 40):
    best = pred.argmax(1)
    act = pred.max(1) > tau
    gain = np.where(act, D[np.arange(len(D)), best], 0.0)
    wgain = np.where(act, Wn[np.arange(len(D)), best], 0.0)
    se = gain.std() / np.sqrt(len(gain))
    print(f"  tau {tau:3d}: acts on {100 * act.mean():5.1f}% of contacts, gem gain {gain.mean():+.2f} +- {se:.2f}, "
          f"win-share change {wgain.mean():+.4f}; by action " +
          ", ".join(f"{a} {int((act & (best == i)).sum())}" for i, a in enumerate(ACTS)))
if out:
    model = train(X, D, seed=9)
    mu, sd, P, ys = model
    f = lambda a: ",".join("%.6gf" % x for x in np.ravel(a))
    txt = (f"// Fight / flee / regroup model (agent2/lab/fight_fit.py, E69): {len(rows)} counterfactual contacts from "
           "fight_cf4.js.\n// Inputs: bot.cpp fight_features (24); outputs: predicted change in the team gem margin over 100 "
           "rounds\n// for forced fight, run and regroup versus the bot's own verdict.\n#pragma once\nnamespace fight_net {\n"
           f"inline constexpr int kIn = {X.shape[1]}, kHid = {HID}, kOut = 3;\n"
           f"inline constexpr float kMu[kIn] = {{{f(mu)}}};\ninline constexpr float kSd[kIn] = {{{f(sd)}}};\n"
           f"inline constexpr float W1[kIn * kHid] = {{{f(P[0])}}};\ninline constexpr float b1[kHid] = {{{f(P[1])}}};\n"
           f"inline constexpr float W2[kHid * kOut] = {{{f(P[2])}}};\ninline constexpr float b2[kOut] = {{{f(P[3])}}};\n"
           f"inline constexpr float kScale = {ys:.6g}f;\n}} // namespace fight_net\n")
    open(out, "w", newline="\n").write(txt)
    print("wrote", out)
