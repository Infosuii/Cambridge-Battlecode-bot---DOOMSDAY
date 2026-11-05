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

## Broader opponent pool (e3-rl160-pool-01, training maps, 800 games)

Same frozen artifacts (v109 f3d919e9, RL160+CLFS 47857f37). 50 training maps x A/B, cambc 5.0.0 / engine 3.0.0, release.

| opponent | v109 | RL160+CLFS | fuel-outs v109 / RL160 |
|---|---|---|---|
| x3inv | 50/100 | 54/100 | 920 / 922 |
| dz | 99/100 | 99/100 | 890 / 883 |
| v86h | 50/100 | 55/100 | 834 / 842 |
| jd-g5070-1104 | 46/100 | 54/100 | 781 / 830 |
| ALL | 245/400 | 262/400 | 3425 / 3477 |

Paired RL160 - v109: **+0.0425 [-0.003, +0.090]** (40 families). The gain shows up against every non-saturated lineage (+4, +5, +8 per 100), and fuel is flat (+1.5%). These are still training maps; the held-out 04 panel from JOHNDOE #151 is the deciding test.

## Held-out 04 panel confirmation (JOHNDOE #151; e3-rl160-heldout04-01, 592 games)

37 frozen 04 maps (SHA-256 pinned in manifests/heldout04_jd151.json, one family per stem), both sides, release, cambc 5.0.0 / engine 3.0.0. Exact v109 f3d919e9 vs RL160+CLFS 47857f37.

| opponent | v109 | RL160+CLFS | fuel-outs v109 / RL160 |
|---|---|---|---|
| v92 | 35/74 | 29/74 | 827 / 832 |
| native Agent 2 | 36/74 | 41/74 | 1274 / 1305 |
| exact v109 (direct) | 37/74 (mirror) | 37/74 | 995 / 973 |
| x3 economy (botx3_11 @ 2bd70a93, SDK rebuild) | 46/74 | 45/74 | 1056 / 1114 |
| ALL | 154/296 | 152/296 | 4152 / 4224 |

Paired RL160 - v109: **-0.007 [-0.061, +0.047]** (37 families). The direct result is level (37/74), and against v92 there is a regression (-6/74). The newer Agent 2 reference (nnfinal_carry_persize_engine4.zip) was not available on this PC.

**Verdict: does not meet the #151 advance bar.** The gain is not broad, the direct result is not favorable, and v92 regresses. The training-map edge (+0.065 / +0.0425) did not carry over to held-out maps, so it looks map-fitted. RL160 stays off the ladder and v109 stays live.
