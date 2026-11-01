# 0001: J001 reference run not pushed

`research/dz/runs/x1e-cw-ladder-x2-01/results.json` (x1 vs x2, ladder, the 68/140 baseline) is not on build/z-plan or
any other branch; neither is `x1e-cw-unseen-x2-01` (the sweep 1d baseline per tools/x1_sweep1d.sh). Please push both
results.json + provenance.json (no evidence.zip needed).

Not blocking: my x1 vs x2 ladder run gives 68/140, and x1 vs v86h ladder replays `x1e-cw-ladder-v86h-01` exactly
(140/140 games, replay hashes identical), so the machines agree. Carrying on with J004.
