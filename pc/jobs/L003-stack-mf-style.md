id: L003
title: URGENT (Rishik: next bot within the hour) - your fight switches on the per-map fit
commit: c153c59 on build/z-plan (your branch is merged; rebase build/z-plan-g3 on it)
bot: x3
run: gate, pool: OPPS="v92 v86h x1bru" SETS=pool (base = X1_MAPFIT=1, c3da892053a7: 96 / 115 / 130 = 341 / 516,
  from the 5060's J022; run the base yourself too as x1g-mf-g3 so your pairs are exact)
switches (one line each):
  mfst: --set X1_MAPFIT=1 --set X1_G3_STYLE=1 --set X1_G3_STYLE_NUMBERS=0 --set X1_G3_STYLE_PWIN=0.5 --set X1_WALKTAIL=3
  mfst6: the same + --set X1_PLAN=1 --set X1_PLAN_ROUND=0 --set X1_PLAN_ID=6
  mfsec: --set X1_MAPFIT=1 --set X1_G3_SECURE=1
priority: 0 (before L002; resume L002 after)
done when: g3/results/L003.md after each line: wins per opponent, total vs base, gained / lost, z, fuel-outs,
  deaths/game, build sha.
