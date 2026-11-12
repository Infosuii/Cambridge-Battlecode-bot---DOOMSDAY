"""Map features -> lineup choice. For each lineup, a ridge regression predicts its mean win rate against the opponent
field from map features (map_features.js); the selector takes the lineup with the highest prediction. Scored by
k-fold cross-validation over maps: the actual win rate of the chosen lineups on held-out maps, against the best single
lineup and the per-map oracle. Writes the fitted coefficients (all maps) as a C++ header for the bot's draft.

usage: python lineup_fit.py out.h table1.json:features1.json [table2.json:features2.json ...]
"""
import json
import sys

import numpy as np

OPPS = ["meta", "L21", "L24", "melee"]


def feats(x):
    t = x["types"]
    n = max(1, sum(t.values()))
    frac = [t.get(str(k), 0) / n for k in range(6)]  # wolf, elk, gem cluster, gold cluster, monolith, golem
    return [np.log(x["area"]), x["picks"] == 3, x["picks"] == 4, x["picks"] == 5, np.log1p(x["groups"]), np.log1p(x["gems"]),
            np.log1p(x["gold"]), x["density"], np.log(x["room"]), x["bush"], x["blocked"], x["spread"], x["maxShare"],
            np.log(x["aspect"]), *frac, t.get("4", 0) > 0, t.get("5", 0) > 0]


NAMES = ["log_area", "picks3", "picks4", "picks5", "log_groups", "log_gems", "log_gold", "density", "log_room", "bush",
         "blocked", "spread", "max_share", "log_aspect", "f_wolf", "f_elk", "f_gem", "f_gold", "f_monolith", "f_golem",
         "has_monolith", "has_golem"]


def main():
    out = sys.argv[1]
    X, Y, src = [], [], []
    lineups = None
    for pair in sys.argv[2:]:
        tp, fp = pair.split(":")
        tab, fe = json.load(open(tp)), json.load(open(fp))
        lineups = lineups or list(tab["lineups"])
        for m, v in tab["maps"].items():
            key = m.replace(".map26a", "")
            if key not in fe:
                continue
            X.append(feats(fe[key]))
            Y.append([np.mean([v["W"][u][o] for o in OPPS]) for u in lineups])
            src.append(tp)
    X, Y = np.array(X, float), np.array(Y, float)
    n, L = Y.shape
    print(f"{n} maps, {L} lineups, {X.shape[1]} features")
    mu, sd = X.mean(0), X.std(0) + 1e-6
    Xn = np.c_[np.ones(n), (X - mu) / sd]

    def fit(idx, lam):
        A = Xn[idx]
        R = lam * np.eye(A.shape[1]); R[0, 0] = 0
        return np.linalg.solve(A.T @ A + R, A.T @ Y[idx])

    rng = np.random.default_rng(1)
    folds = rng.permutation(n) % 5
    for lam in (1, 5, 20, 50):
        chosen = np.zeros(n)
        for k in range(5):
            tr, te = folds != k, folds == k
            B = fit(np.where(tr)[0], lam)
            pred = Xn[te] @ B
            chosen[te] = Y[te][np.arange(te.sum()), pred.argmax(1)]
        best_fixed = Y.mean(0).argmax()
        print(f"lambda {lam:3}: held-out chosen {100 * chosen.mean():.1f}% | best single lineup {lineups[best_fixed]} "
              f"{100 * Y[:, best_fixed].mean():.1f}% | per-map oracle {100 * Y.max(1).mean():.1f}%")
        for s in sorted(set(src)):
            msk = np.array([x == s for x in src])
            print(f"      {s.split('/')[-1]:24} chosen {100 * chosen[msk].mean():.1f}% vs {lineups[best_fixed]} {100 * Y[msk, best_fixed].mean():.1f}%")
    lam = float(sys.argv[sys.argv.index("--lam") + 1]) if "--lam" in sys.argv else 20
    B = fit(np.arange(n), lam)
    with open(out, "w") as fh:
        fh.write(f"// Lineup selector (agent2/lab/lineup_fit.py, ridge {lam}, {n} maps): predicted win rate per lineup from map\n")
        fh.write("// features; the draft takes the highest. Feature order: " + ", ".join(NAMES) + ".\n#pragma once\nnamespace lineup_model {\n")
        fh.write(f"inline constexpr int kF = {X.shape[1]}, kL = {L};\n")
        fh.write("inline constexpr float kMu[kF] = {" + ", ".join(f"{v:.6g}f" for v in mu) + "};\n")
        fh.write("inline constexpr float kSd[kF] = {" + ", ".join(f"{v:.6g}f" for v in sd) + "};\n")
        fh.write("inline constexpr float kB[kF + 1][kL] = {" + ", ".join("{" + ", ".join(f"{v:.6g}f" for v in row) + "}" for row in B) + "};\n")
        fh.write("// Lineups in order: " + ", ".join(lineups) + "\n}\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
