id: K012
title: URGENT - g3's fight switches on the current best line x3mf (was L003)
commit: e3a9965 on build/z-plan
bot: x3
run: gate, pool, OPPS="v92 v86h x1bru" SETS=pool (516 games a line)
switches (one line each):
  mf:    --set X1_MAPFIT=1                                   (base; expected 96 / 115 / 130 = 341, as g5060 J022)
  mfst:  --set X1_MAPFIT=1 --set X1_G3_STYLE=1 --set X1_G3_STYLE_NUMBERS=0 --set X1_G3_STYLE_PWIN=0.5 --set X1_WALKTAIL=3
  mfsec: --set X1_MAPFIT=1 --set X1_G3_SECURE=1
  e.g. `SETS=pool OPPS="v92 v86h x1bru" WORKERS=18 bash tools/x1_gate.sh x3 mfst-g5070 "--set X1_MAPFIT=1 ..."`
priority: 0 (right after K011)
done when: g5070/results/K012.md after each line: wins per opponent, total vs mf, gained / lost, z, fuel-outs,
  deaths/game, build sha. A line with total >= 347, z >= 1.3, no opponent > 2 worse: also styled + maze vs v92 and
  x1bru, and say so in the first line of the file.
