id: L004
title: Held-out check - is the per-map fit (x3mf) overfit, and do near-miss lines win on unseen opponents?
supersedes: the L002/L003 withdrawal (msg 0044). This is a NEW job; it does not rerun any K* work.
commit: build/z-plan head (rebase build/z-plan-g3 on it; experiments off by default, default build 5704d7ba41ac)
bot: x3
run: gate, pool, held-out opponents: SETS=pool OPPS="v81hl v86h-s2 x1" WORKERS=14
  bash tools/x1_gate.sh x3 TAG-g3 "SWITCHES"
lines (TAG: SWITCHES), in this order:
  mf:      --set X1_MAPFIT=1
  noop:    --set X1_MAPFIT=1 --set X1_NOOP=1
  bag80:   --set X1_MAPFIT=1 --set X1_BAGRISK=80
  rb:      --set X1_MAPFIT=1 --set X1_RACEBANK=1
  mfsec:   --set X1_MAPFIT=1 --set X1_G3_SECURE=1
  hrwt:    --set X1_MAPFIT=1 --set A2_HIDEREC=1 --set X1_WALKTAIL=3
known held-out numbers (PC, x3 with no switches, 5704d7ba41ac): v81hl 130, v86h-s2 100, x1 133 = 363 / 516.
  The PC is running mf too (x1g-ho-mf-pc); yours must match it game for game - post a mismatch at once.
priority: 0. If a bot folder (bots/v81hl, bots/v86h-s2, bots/x1) is missing, write g3/msgs and use what exists.
done when: g3/results/L004.md after each line: wins per opponent, total vs x3 (363) and vs mf, gained / lost
  per cell, z, fuel-outs, build sha. Then go idle and poll for L005.
