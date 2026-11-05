# RL160 (JOHNDOE engine-3 RL, header dc57ac51) + CLFS vs exact v109 — 2026-11-05

- Control: exact v109 (source ZIP c013c216, header 6661d16a, CLFS=1), WASM f3d919e9.
- Candidate: the same source, nn_weights.h = dc57ac51 restored with tournament_engine3_01/restore_weights.py
  (input/output SHA-256 verified), WASM 47857f37. No other change.
- Engine 3.0.0 (cambc 5.0.0, build 96ce858f), release, 100k fuel. Paired by cell; family-cluster bootstrap 95%.
- RL1024 is a separate checkpoint and was not tested here. Confirmation maps untouched.

| maps | opponent | RL160+CLFS | v109 | delta [95% CI] | own fuel-outs |
|---|---|---|---|---|---|
| training (50 / 40 families) | v92 | 54/100 | 46/100 | +0.08 [-0.05, +0.19] | 830 vs 781 |
| training | native Agent 2 | 53/100 | 48/100 | +0.05 [-0.07, +0.16] | 907 vs 907 |
| training | both | 107/200 | 94/200 | +0.065 [-0.02, +0.14] | |
| development (15 / 13 families) | v92 | 18/30 | 15/30 | +0.10 [-0.04, +0.23] | 106 vs 120 |
| development | native Agent 2 | 12/30 | 14/30 | -0.07 [-0.22, +0.08] | 83 vs 103 |
| development | both | 30/60 | 29/60 | +0.017 [-0.08, +0.12] | 189 vs 223 |

Reports: runs/rl_env_1104/eval/e3-cand-clfs-train-01, e3-cand-clfs-dev-01. Status: strongest engine-3 candidate so far,
not significant alone; awaiting the joint confirmation screen before any ladder change (JOHNDOE #150).
