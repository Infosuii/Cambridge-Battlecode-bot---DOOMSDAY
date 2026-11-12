id: J025
title: URGENT (Rishik: next bot within the hour) - stacks on the per-map fit
commit: c153c59 on build/z-plan (bots/x3; X1_MAPFIT=1 builds c3da892053a7 = your x3mf2, so J022's gate is the base:
  pool vs v92 / v86h / x1bru = 96 / 115 / 130, 341 / 516)
bot: x3
run: gate, pool only first: OPPS="v92 v86h x1bru" SETS=pool
switches (one line each; all with --set X1_MAPFIT=1):
  mfp6: --set X1_MAPFIT=1 --set X1_PLAN=1 --set X1_PLAN_ROUND=0 --set X1_PLAN_ID=6     (J024 k6 was +16 vs v92)
  mfp8: --set X1_MAPFIT=1 --set X1_PLAN=1 --set X1_PLAN_ROUND=0 --set X1_PLAN_ID=8     (k8 +10)
  mfp2l: --set X1_MAPFIT=1 --set X1_PLAN=1 --set X1_PLAN_ROUND=300 --set X1_PLAN_ID=2  (k13 +5)
priority: 0 (before J023; pause it)
done when: g5060/results/J025.md after each line: wins per opponent vs mf (96 / 115 / 130), gained / lost, z,
  fuel-outs, deaths/game. The best line that passes (total >= 347, z >= 1.3, no opponent > 2 worse): also run
  styled + maze vs v92 and x1bru, and post it. g3 runs the fight-style stacks (L003) at the same time.
