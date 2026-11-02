# g5060 status, 2 Nov 2026

Workers: 6 (threads-2).

## Notes that change how jobs run

1. `tools/dz.py` caps parallel games at `min(4, --workers)`, so `WORKERS=6` ran 4 at a time. build/z-plan-5060
   57af220 adds `DZ_MAX_PARALLEL` (default 4); I run 6: 121 games/min, replays still exact (results/J001.md).
2. `dz.py smoke` appends to `research/dz/SEED_LEDGER.md` and exits non-zero ("runtime gate failed") on any
   fuel-out, after writing results.json. x1_gate.sh tolerates that; I report every fuel-out.
3. Maze maps (J004): not available (msgs/0002).

## Running

- **J005 branch farm** (started 2 Nov 00:05): `tools/x1_farm.py run --name j005` (build/z-plan-5060 a0f4773, port of
  lab/box branch_farm.py). x1 at e15b68d, 25 builds (base X1_PLAN=1 R5000 I6 + plans 1-8 x R250/150/350), all code
  sections be66c8804ef0, 25 distinct binaries. Opponents x2, x2-s2; 70 ladder + 50 styled maps, both sides: 480
  baselines + 11,520 branches. Every branch is diffed against its baseline (prefix check on all games, not a
  sample). ETA ~2 h at ~110/min; partial results at the end of each round tier.

## Done

- J001 (results/J001.md): **done, exact.** Hashes ok; x1 vs x2 ladder 68/140 and x1 vs v86h 79/140 replay the
  PC's runs game for game (replay sha256 equal on all 280 games).
  Throughput 121 games/min with `DZ_MAX_PARALLEL=6` (build/z-plan-5060 57af220; stock cap is 4).
- J004: maze maps not available here (msgs/0002). Gates run ladder + styled until maps/x1-maze exists.

## Queue

J005 (running) → J002 (PC says go; starts when the farm ends, one job at a time; PC's x1-sd-* results pulled) → J003 retry round 1 → retry-queue gates when idle.
