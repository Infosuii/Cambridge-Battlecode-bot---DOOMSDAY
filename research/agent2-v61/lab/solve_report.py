"""Report on offline-solved fight states (solve_lab.js output): how often the simulator's fight/run verdict agrees with
the engine's, what disagreement costs, and a least-squares correction engD ~ simD + features (the distillation target).

usage: python -I solve_report.py agent2/lab/solve_*.jsonl [--margin 2.0]
"""
import json
import sys
from pathlib import Path

import numpy as np


def main():
    args = sys.argv[1:]
    margin = float(args[args.index("--margin") + 1]) if "--margin" in args else 2.0
    files = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] != "--margin")]
    rows = []
    for f in files:
        for line in Path(f).read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))
    n = len(rows)
    sim_d = np.array([r["simF"] - r["simR"] for r in rows])
    eng_d = np.array([r["engF"] - r["engR"] for r in rows])
    verdict = lambda d: np.where(d > margin, 1, np.where(d < -margin, -1, 0))
    vs, ve = verdict(sim_d), verdict(eng_d)
    print(f"states {n}; engine fight {np.mean(ve == 1):.2f} run {np.mean(ve == -1):.2f} tie {np.mean(ve == 0):.2f}")
    print(f"sim    fight {np.mean(vs == 1):.2f} run {np.mean(vs == -1):.2f} tie {np.mean(vs == 0):.2f}")
    print(f"corr(simD, engD) {np.corrcoef(sim_d, eng_d)[0, 1]:.3f}")
    decided = (vs != 0) & (ve != 0)
    print(f"both decided {decided.sum()}: agree {np.mean(vs[decided] == ve[decided]):.3f}")
    # Regret of the simulator's verdict (in value units): taking fight/run as it says vs the engine's better plan.
    take = np.where(vs == 1, 1, np.where(vs == -1, -1, 0))
    regret = np.where(take == 1, np.maximum(0, -eng_d), np.where(take == -1, np.maximum(0, eng_d), 0))
    print(f"mean regret per state {regret.mean():.2f}; states with regret > 5: {(regret > 5).sum()}")
    for name, sel in [("sim fight, engine run", (vs == 1) & (ve == -1)), ("sim run, engine fight", (vs == -1) & (ve == 1)),
                      ("sim tie, engine fight", (vs == 0) & (ve == 1)), ("sim tie, engine run", (vs == 0) & (ve == -1))]:
        print(f"  {name}: {sel.sum()}")
    # Correction: engD ~ a simD + b + c hpf + d nEnemies + e nAllies + f near + g ranged.
    feats = ["simD", "1", "hpf", "nEnemies", "nAllies", "near", "ranged"]
    X = np.array([[sd, 1.0, r["hpf"], r["nEnemies"], r["nAllies"], r["near"], 1.0 if r["range"] > 1 else 0.0] for sd, r in zip(sim_d, rows)])
    # Two halves: fit on one, check the other (a correction that does not hold out is noise).
    idx = np.arange(n)
    for fit_half in (0, 1):
        tr, te = idx % 2 == fit_half, idx % 2 != fit_half
        coef, *_ = np.linalg.lstsq(X[tr], eng_d[tr], rcond=None)
        pred = X[te] @ coef
        vc = verdict(pred)
        reg_c = np.where(vc == 1, np.maximum(0, -eng_d[te]), np.where(vc == -1, np.maximum(0, eng_d[te]), 0))
        print(f"fit half {fit_half}: " + " ".join(f"{k}={c:+.3f}" for k, c in zip(feats, coef)) +
              f" | held-out regret {reg_c.mean():.2f} vs sim {regret[te].mean():.2f}, corr {np.corrcoef(pred, eng_d[te])[0, 1]:.3f}")


if __name__ == "__main__":
    main()
