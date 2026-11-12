id: K001
for: g5070
title: setup and one exact reproduction (10 min)
steps:
  1. docs/x1_5070/HANDOVER.md setup (clone, cambc, comms init, local cherry-pick of 57af220 + DZ_MAX_PARALLEL).
  2. python tools/dz.py smoke --name x1e-cw-ladder-x2-g5070 --pool --opponent x2 --candidate-bot x1 --workers <threads-2>
     Expected: 68/140 wins; every game's outcome/banked/rounds equal to research/dz/runs/x1e-cw-ladder-x2-01/results.json.
  3. Note games/minute.
done when: g5070/STATUS.md: machine, threads, games/min, reproduction exact or which games differ (if games
differ, post g5070/msgs/0001 and still run K002: results stay comparable within your own machine's base).
