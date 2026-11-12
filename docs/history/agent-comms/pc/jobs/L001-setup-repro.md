id: L001
title: setup check + one exact reproduction
commit: 4118520 on build/z-plan (bots/x3; default build 5704d7ba41ac = v92)
bot: x3
run: gate
switches: none
opponents: v86h
maps: pool
priority: 1
done when: g3/results/L001.md: build sha, wins (must be 108/172), and a per-game compare with
  g5060/results/J018/x1g-x3-pool-v86h-01.json (map, side, outcome, banked: all 172 must match), games/min with your
  DZ_MAX_PARALLEL; g3/STATUS.md filled in (machine, CPU threads, RAM).

Command: `SETS=pool OPPS=v86h WORKERS=$N bash tools/x1_gate.sh x3 repro-g3`
(run x1g-repro-g3-pool-v86h-01). A mismatch means the machine is not usable for gates yet: report it and stop.
