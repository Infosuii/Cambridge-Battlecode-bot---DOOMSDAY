"""Spatial move model (option 2): terrain + unit positions around the champion + the option + exact physics features,
a small network ranking each scenario's options (engine labels from micro_lab.js; terrain from grid_dump.js).

usage: python spatial_fit.py micro.jsonl grids.jsonl
"""
import json
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else ".")
from micro_phys import simulate  # noqa: E402


def opt_vec(start, acts, grid):
    me = start[0]
    team = me["team"]
    t = np.array(grid, np.float32)
    terr = np.concatenate([(t == 1), (t == 2)]).astype(np.float32)  # 162
    units = np.zeros((2, 81), np.float32)
    for u in start[1:]:
        if not u["alive"]:
            continue
        dx, dy = u["x"] - me["x"], u["y"] - me["y"]
        if abs(dx) <= 4 and abs(dy) <= 4:
            units[0 if u["team"] != team else 1, (dy + 4) * 9 + (dx + 4)] = u["hp"] / max(1, u["maxhp"])
    a = acts.split() if acts and acts != "pass" else []
    o = np.zeros(20, np.float32)
    mv = next((int(x[4:]) for x in a if x.startswith("move")), 8)
    o[mv] = 1  # 0..8 (8 = stay)
    o[9] = sum(x.startswith("attack") for x in a)
    c = next((x for x in a if x.startswith("cast")), None)
    if c:
        s, tgt = c[4:].split(":")
        o[10 + int(s)] = 1
        o[12] = tgt == "self"; o[13] = tgt.startswith("enemy"); o[14] = tgt.startswith("ground"); o[15] = tgt.startswith("ally")
        mi = next((i for i, x in enumerate(a) if x.startswith("move")), 99)
        o[16] = a.index(c) < mi
    o[17] = 1 if (a and a[0].startswith("attack") and any(x.startswith("move") for x in a)) else 0
    o[18] = me["hp"] / max(1, me["maxhp"])
    o[19] = 1 if me["range"] > 1 else 0
    phys = simulate(start, acts)
    if phys is None:
        return None
    typ = np.zeros(12, np.float32)
    if 0 <= me["type"] < 12:
        typ[me["type"]] = 1
    return np.concatenate([terr, units.ravel(), o, phys.astype(np.float32), typ])


def main():
    recs = [r for r in (json.loads(l) for l in open(sys.argv[1]) if l.strip()) if "options" in r and "start" in r]
    grids = [json.loads(l) for l in open(sys.argv[2]) if l.strip()]
    S = []
    for r, g in zip(recs, grids):
        X, V = [], []
        for opt in r["options"]:
            v = opt_vec(r["start"], opt["acts"], g["grid"])
            if v is not None:
                X.append(v); V.append(opt["v"])
        if len(X) >= 2:
            S.append((np.stack(X), np.array(V), r["own"]["v"]))
    n = len(S)
    te = np.arange(n) % 4 == 0
    Xtr = np.concatenate([s[0] for s, t in zip(S, te) if not t]); Ytr = np.concatenate([np.clip(s[1] - s[1].mean(), -40, 40) for s, t in zip(S, te) if not t])
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-3
    Xn = (Xtr - mu) / sd
    D, Hd = Xn.shape[1], 64
    rng = np.random.default_rng(5)
    W1 = rng.normal(0, 0.1, (D, Hd)); b1 = np.zeros(Hd); W2 = rng.normal(0, 0.1, Hd)
    ps = [W1, b1, W2]; m = [np.zeros_like(p) for p in ps]; v = [np.zeros_like(p) for p in ps]; t = 0
    for ep in range(30):
        idx = rng.permutation(len(Xn))
        for s in range(0, len(idx), 256):
            b = idx[s:s + 256]
            h = np.maximum(0, Xn[b] @ W1 + b1); z = h @ W2
            g = 2 * (z - Ytr[b]) / len(b)
            gW2 = h.T @ g; gh = np.outer(g, W2) * (h > 0); gW1 = Xn[b].T @ gh; gb1 = gh.sum(0)
            t += 1
            for i, (p_, g_) in enumerate(zip(ps, [gW1, gb1, gW2])):
                g_ = g_ + 3e-3 * p_
                m[i] = 0.9 * m[i] + 0.1 * g_; v[i] = 0.999 * v[i] + 0.001 * g_ * g_
                p_ -= 1e-3 * (m[i] / (1 - 0.9 ** t)) / (np.sqrt(v[i] / (1 - 0.999 ** t)) + 1e-8)
    score = lambda X: np.maximum(0, (X - mu) / sd @ W1 + b1) @ W2
    sh_m, sh_o, hm, ho = [], [], 0, 0
    for s, t_ in zip(S, te):
        if not t_:
            continue
        X, V, own = s
        best = V.max(); pick = V[np.argmax(score(X))]
        sh_m.append(best - pick); sh_o.append(best - own); hm += best - pick < 0.5; ho += best - own < 0.5
    nt = int(te.sum())
    print(f"{n} scenarios ({nt} held out), {D} inputs per option")
    print(f"  spatial model: within 0.5 of best {hm / nt:.0%}, shortfall mean {np.mean(sh_m):.2f}, median {np.median(sh_m):.2f}")
    print(f"  bot's own:     within 0.5 of best {ho / nt:.0%}, shortfall mean {np.mean(sh_o):.2f}, median {np.median(sh_o):.2f}")


if __name__ == "__main__":
    main()
