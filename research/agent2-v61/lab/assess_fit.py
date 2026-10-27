"""Learned fight-or-run assessment from engine counterfactuals (fightcf_lab.js): each state was played three ways
(the bot's own verdict, forced fight, forced run). Fits two small models on the start state:
  value: margin50(fight) - margin50(run)    (team gem margin 50 rounds later; the game objective)
  death: P(champion dead 3 rounds later | fight), and | run
and compares, on held-out states, the realised value of: always fight, always run, the bot's own verdict, the
model's choice and the hindsight best. Writes assess_model.h (inputs: 42 features + option) when asked.

usage: python assess_fit.py fightcf.jsonl [out_header]
"""
import json
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else ".")
from behave_fit import features  # noqa: E402


def feat(r):
    st = r["start"]
    units = [u for u in st["units"] if "x" in u]
    rec = {"units": units, "actor": r["champ"], "round": r["startRound"]}
    f, mn = features(rec)
    if f is None:
        return None
    me = mn[0]
    camp_n = camp_str = 0.0
    for c in st.get("camps", []):
        if c["str"] > 0 and max(abs(c["x"] - me["x"]), abs(c["y"] - me["y"])) <= 4:
            camp_n += 1
            camp_str += c["str"] / 100.0
    return np.concatenate([f, np.array([camp_n, camp_str], np.float32)])


def margin(o, key):
    g = o[key]
    return None if g is None else g[0] - g[1]


def mlp(X, y, kind, epochs=60, hidden=24, seed=1):
    rng = np.random.default_rng(seed)
    W1 = rng.normal(0, 0.3, (X.shape[1], hidden)); b1 = np.zeros(hidden)
    W2 = rng.normal(0, 0.3, (hidden, 1)); b2 = np.zeros(1)
    ps = [W1, b1, W2, b2]; m = [np.zeros_like(p) for p in ps]; v = [np.zeros_like(p) for p in ps]; t = 0
    for _ in range(epochs):
        idx = rng.permutation(len(X))
        for s in range(0, len(X), 128):
            b = idx[s:s + 128]
            h = np.tanh(X[b] @ W1 + b1); z = (h @ W2 + b2)[:, 0]
            if kind == "bin":
                p = 1 / (1 + np.exp(-z)); g = (p - y[b]) / len(b)
            else:
                g = 2 * (z - y[b]) / len(b)
            gW2 = h.T @ g[:, None]; gb2 = g.sum(keepdims=True)
            gh = g[:, None] @ W2.T * (1 - h * h); gW1 = X[b].T @ gh; gb1 = gh.sum(0)
            t += 1
            for i, (p_, g_) in enumerate(zip(ps, [gW1, gb1, gW2, gb2])):
                g_ = g_ + 1e-3 * p_  # weight decay
                m[i] = 0.9 * m[i] + 0.1 * g_; v[i] = 0.999 * v[i] + 0.001 * g_ * g_
                p_ -= 2e-3 * (m[i] / (1 - 0.9 ** t)) / (np.sqrt(v[i] / (1 - 0.999 ** t)) + 1e-8)
    def f(Xq):
        z = (np.tanh(Xq @ W1 + b1) @ W2 + b2)[:, 0]
        return 1 / (1 + np.exp(-z)) if kind == "bin" else z
    return f, ps


def auc(score, y):
    o = np.argsort(score); y = y[o]; pos = y.sum(); neg = len(y) - pos
    if pos == 0 or neg == 0:
        return float("nan")
    ranks = np.arange(1, len(y) + 1)
    return (ranks[y == 1].sum() - pos * (pos + 1) / 2) / (pos * neg)


def main():
    rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    data = []
    for r in rows:
        x = feat(r)
        mf, mr, mb = margin(r["fight"], "g50"), margin(r["run"], "g50"), margin(r["base"], "g50")
        if x is None or mf is None or mr is None or mb is None:
            continue
        data.append((x, mf, mr, mb, r["verdict"], 0 if r["fight"]["meAlive"] else 1, 0 if r["run"]["meAlive"] else 1, 0 if r["base"]["meAlive"] else 1))
    X = np.stack([d[0] for d in data]).astype(np.float64)
    MF, MR, MB = (np.array([d[i] for d in data], float) for i in (1, 2, 3))
    V = np.array([d[4] for d in data]); DF, DR, DB = (np.array([d[i] for d in data], float) for i in (5, 6, 7))
    n = len(data)
    te = np.arange(n) % 4 == 0; tr = ~te
    mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-6
    Xn = (X - mu) / sd
    D = MF - MR
    print(f"{n} states with 50-round outcomes ({tr.sum()} train / {te.sum()} held out)")
    print(f"  forced fight vs forced run: same margin in {np.mean(D == 0):.0%}; fight better {np.mean(D > 0):.0%}, run better {np.mean(D < 0):.0%}; mean {D.mean():+.1f} ± {D.std() / np.sqrt(n):.1f}")
    print(f"  bot's own verdict: fight {np.mean(V == 1):.0%}, run {np.mean(V == -1):.0%}, neither {np.mean(V == 0):.0%}")
    print(f"  deaths within 3 rounds: own choice {DB.mean():.1%}, forced fight {DF.mean():.1%}, forced run {DR.mean():.1%}")
    # Value model: D = margin difference (clipped against chaos).
    Dc = np.clip(D, -200, 200)
    fv, pv = mlp(Xn[tr], Dc[tr], "reg")
    pred = fv(Xn)
    corr = np.corrcoef(pred[te], D[te])[0, 1]
    for margin_ in (0, 10, 25):
        choose = np.where(pred > margin_, MF, np.where(pred < -margin_, MR, MB))
        print(f"  model choice (|pred| > {margin_:2d}, else the bot's own): held-out mean margin {choose[te].mean():+7.1f}")
    best = np.maximum(MF, MR)
    for name, val in [("always fight", MF), ("always run", MR), ("bot's own verdict", MB), ("hindsight best", best)]:
        print(f"  {name:28s}: held-out mean margin {val[te].mean():+7.1f}")
    print(f"  value model: held-out correlation with the real difference {corr:+.3f}")
    # Death models.
    fdf, _ = mlp(Xn[tr], DF[tr], "bin"); fdr, _ = mlp(Xn[tr], DR[tr], "bin")
    print(f"  death within 3 rounds, held-out AUC: if fighting {auc(fdf(Xn[te]), DF[te]):.3f}, if running {auc(fdr(Xn[te]), DR[te]):.3f}")
    if len(sys.argv) > 2:
        W1, b1, W2, b2 = pv
        fmt = lambda a: ", ".join(f"{x:.6e}f" for x in np.ravel(a))
        with open(sys.argv[2], "w") as fh:
            fh.write("// Learned fight-or-run value (agent2/lab/assess_fit.py on fightcf_lab.js engine counterfactuals):\n")
            fh.write("// predicted team gem margin 50 rounds later, forced fight minus forced run. Inputs: behave_fit features + camps.\n")
            fh.write(f"#pragma once\nnamespace assess_model {{\ninline constexpr int kIn = {X.shape[1]}, kHidden = {W1.shape[1]};\n")
            fh.write(f"inline constexpr float kMu[kIn] = {{{fmt(mu)}}};\ninline constexpr float kSd[kIn] = {{{fmt(sd)}}};\n")
            fh.write(f"inline constexpr float kW1[kIn][kHidden] = {{{', '.join('{' + fmt(r) + '}' for r in W1)}}};\n")
            fh.write(f"inline constexpr float kB1[kHidden] = {{{fmt(b1)}}};\ninline constexpr float kW2[kHidden] = {{{fmt(W2)}}};\ninline constexpr float kB2 = {b2[0]:.6e}f;\n")
            fh.write("} // namespace assess_model\n")
        print("wrote", sys.argv[2])


if __name__ == "__main__":
    main()
