"""Macro choice model from what-if data (exit_lab.js): per option, a ridge regression predicts its gain over keeping the
bot's choice from the 20 decision-point features (fitted on points where the option triggered). The rule takes the
option with the highest predicted gain if it clears a margin, else keeps. Scored by 5-fold cross-validation grouped by
map: the actual gain of the chosen options on held-out maps (keep = 0), against each option applied everywhere.

usage: python macro_fit.py data.jsonl [out.h]
"""
import json
import sys

import numpy as np

OPTS = ["forbid", "bank", "hold", "regroup", "home"]


def main():
    rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    X = np.array([r["feats"] for r in rows], float)
    G = np.array([[r["gain"].get(o, 0.0) if r["applied"].get(o) else np.nan for o in OPTS] for r in rows])
    maps = np.array([r["map"] for r in rows])
    n = len(rows)
    print(f"{n} decision points, {len(set(maps))} maps")
    for j, o in enumerate(OPTS):
        g = G[~np.isnan(G[:, j]), j]
        print(f"  always {o:8} applied {len(g):4}  mean gain {g.mean():+7.1f} +- {g.std() / np.sqrt(max(1, len(g))):5.1f}")
    mu, sd = X.mean(0), X.std(0) + 1e-6
    sd[-1] = 1.0  # bias column
    Xn = (X - mu) / sd
    Xn[:, -1] = 1.0

    def fit(idx, lam):
        B = np.zeros((X.shape[1], len(OPTS)))
        for j in range(len(OPTS)):
            ii = [i for i in idx if not np.isnan(G[i, j])]
            if len(ii) < 20:
                B[-1, j] = -1e9
                continue
            A, y = Xn[ii], G[ii, j]
            R = lam * np.eye(A.shape[1]); R[-1, -1] = 0
            B[:, j] = np.linalg.solve(A.T @ A + R, A.T @ y)
        return B

    umaps = sorted(set(maps))
    rng = np.random.default_rng(5)
    fold_of = {m: k for m, k in zip(umaps, rng.permutation(len(umaps)) % 5)}
    folds = np.array([fold_of[m] for m in maps])
    best = None
    for lam in (10, 50, 200, 1000):
        for tau in (0, 10, 25, 50):
            got, chosen = np.zeros(n), np.zeros(n, int) - 1
            for k in range(5):
                tr, te = np.where(folds != k)[0], np.where(folds == k)[0]
                B = fit(tr, lam)
                P = Xn[te] @ B
                for row, i in enumerate(te):
                    avail = [j for j in range(len(OPTS)) if not np.isnan(G[i, j])]
                    if not avail:
                        continue
                    j = max(avail, key=lambda c: P[row, c])
                    if P[row, j] > tau:
                        got[i], chosen[i] = G[i, j], j
            se = got.std() / np.sqrt(n)
            share = (chosen >= 0).mean()
            print(f"lambda {lam:5} margin {tau:3}: held-out gain per decision {got.mean():+6.1f} +- {se:4.1f} (acts on {100 * share:.0f}%"
                  f"; {', '.join(f'{OPTS[j]} {(chosen == j).mean() * 100:.0f}%' for j in range(len(OPTS)) if (chosen == j).any())})")
            if best is None or got.mean() > best[0]:
                best = (got.mean(), lam, tau, se)
    print(f"best: lambda {best[1]}, margin {best[2]}: {best[0]:+.1f} +- {best[3]:.1f} gems per decision vs always keep (0)")
    if len(sys.argv) > 2:
        B = fit(np.arange(n), best[1])
        with open(sys.argv[2], "w") as fh:
            fh.write(f"// Macro chooser (agent2/lab/macro_fit.py, ridge {best[1]}, {n} what-if points): predicted gain per option over keeping\n")
            fh.write(f"// the bot's choice; act on the best option above the margin {best[2]}. Options: " + ", ".join(OPTS) + ".\n#pragma once\nnamespace macro_model {\n")
            fh.write(f"inline constexpr int kF = {X.shape[1]}, kO = {len(OPTS)};\ninline constexpr float kMargin = {best[2]}f;\n")
            fh.write("inline constexpr float kMu[kF] = {" + ", ".join(f"{v:.6g}f" for v in mu) + "};\n")
            fh.write("inline constexpr float kSd[kF] = {" + ", ".join(f"{v:.6g}f" for v in sd) + "};\n")
            fh.write("inline constexpr float kB[kF][kO] = {" + ", ".join("{" + ", ".join(f"{v:.6g}f" for v in row) + "}" for row in B) + "};\n}\n")
        print("wrote", sys.argv[2])


if __name__ == "__main__":
    main()
