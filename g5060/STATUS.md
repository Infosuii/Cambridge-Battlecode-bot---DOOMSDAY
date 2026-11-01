# g5060 status, 2 Nov 2026

Workers: 6 (threads-2).

## Notes that change how jobs run

1. `tools/dz.py` caps parallel games at `min(4, --workers)` (ThreadPoolExecutor in `experiment()`), so
   `WORKERS=6` actually runs 4 games at a time. J001 measures the stock tool as-is (exact reproduction); after
   that I'll test a 6-way cap on build/z-plan-5060 (runner only, no game changes) and report the speed-up.
2. `dz.py smoke` appends to `research/dz/SEED_LEDGER.md` and exits non-zero ("runtime gate failed") on any
   fuel-out, after writing results.json. x1_gate.sh tolerates that; I report every fuel-out.
3. Maze maps (J004): not available (msgs/0002).

## Running

- J005 branch farm: reading lab/box tools/lab/branch_farm.py + branch_prefix.py, adapting to X1_PLAN on
  build/z-plan-5060. ETA for the farm itself after setup: ~11.5k games at ~120/min ≈ 1.5-2 h (ladder + styled).

## Done

- J001 (results/J001.md): hashes ok; x1 vs x2 ladder 68/140; x1 vs v86h ladder replays the PC's run exactly,
  game for game. Game-for-game check vs x2 waits on the PC pushing x1e-cw-ladder-x2-01 (msgs/0001).
  Throughput 121 games/min with `DZ_MAX_PARALLEL=6` (build/z-plan-5060 57af220; stock cap is 4).
- J004: maze maps not available here (msgs/0002). Gates run ladder + styled until maps/x1-maze exists.

## Queue

J005 (now) → J002 (when pc/STATUS says the PC stopped sweep 1d) → J003 retry round 1 → retry-queue gates when idle.
