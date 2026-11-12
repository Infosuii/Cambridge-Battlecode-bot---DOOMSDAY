id: K011
title: refresh on the x3 base + one exact reproduction
commit: e3a9965 on build/z-plan (bots/x3; default build 5704d7ba41ac = v92)
bot: x3
run: gate
opponents: v86h
maps: pool
priority: 1
done when: g5070/results/K011.md: build sha 5704d7ba41ac, wins (must be 108/172), per-game compare with
  g5060/results/J018/x1g-x3-pool-v86h-01.json (map, side, outcome, banked: all 172 must match), games/min;
  g5070/STATUS.md updated (machine, threads, what runs next).
Command: `SETS=pool OPPS=v86h WORKERS=18 bash tools/x1_gate.sh x3 repro-g5070`. A mismatch: report and stop.
