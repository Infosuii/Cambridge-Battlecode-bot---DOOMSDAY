id: L005
title: Which part of x3inv beats us? (after L004)
commit: build/z-plan 94c35fe or later (bots/x3inv, x3inv-t, x3inv-a, x3inv-i)
bot: x3
run: SETS=pool WORKERS=14 bash tools/x1_gate.sh x3 L005-g3 "--set X1_MAPFIT=1" with OPPS="x3inv x3inv-t x3inv-a x3inv-i"
  x3inv   = x3mf + HOME_TERR 1.0 + HOME_AGGR 1.0 + V58_ITEM_PLAN 0 (PC: x3mf scores 102/172 vs it)
  x3inv-t = x3mf + HOME_TERR 1.0 only (invades); x3inv-a = HOME_AGGR 1.0 only; x3inv-i = V58_ITEM_PLAN 0 only
  The x3inv run must match the PC's 102 game for game (x1g-inv-mf-pc-pool-x3inv-01); post a mismatch at once.
then: python research/x3/local_pattern.py on each run (opp camp clears on our side, gold at round 600, deaths).
priority: 1 (after L004).
done when: g3/results/L005.md: wins per opponent, local_pattern lines, and per map the cells x3mf loses to each part
  but not to x3mf itself (the v92/x3 mirror), then poll for L006.
