# g5060 status, 2 Nov 2026 (session start)

Workers: 6 (threads-2).

## Notes that change how jobs run

1. `tools/dz.py` caps parallel games at `min(4, --workers)` (ThreadPoolExecutor in `experiment()`), so
   `WORKERS=6` actually runs 4 games at a time. J001 measures the stock tool as-is (exact reproduction); after
   that I'll test a 6-way cap on build/z-plan-5060 (runner only, no game changes) and report the speed-up.
2. `dz.py smoke` appends to `research/dz/SEED_LEDGER.md` and exits non-zero ("runtime gate failed") on any
   fuel-out, after writing results.json. x1_gate.sh tolerates that; I report every fuel-out.
3. Maze maps (J004): Agent 2's handover puts them in their local workspace (`v4/maps_maze`, `v4/maps_mazetest`)
   and not in any branch. Not on this disk. Searching further; message to follow if I can't find them.

## Running

- J001 step 3: `x1e-cw-ladder-x2-g5060` (x1 vs x2, 70 ladder maps x 2 sides), started.

## Done

- Clone, `build/z-plan` checked out, `build/z-plan-5060` created and pushed; comms initialised.
- J001 step 2 hashes (built via tools/dz.py `build()` from a copy of each `bots/<bot>/src`):

| bot | sha256 (12) | expected | |
|---|---|---|---|
| x1 | 1746f2bb7fa3 | 1746f2bb7fa3 | ok |
| x2 | a9f1bbc43ef7 | a9f1bbc43ef7 | ok |
| x2-s2 | 5d21ba5ebbf7 | (not given) | recorded |
| v86h | 0fae1c17ee73 | 0fae1c17ee73 | ok |
| v86h-s2 | a0d2aabd702a | a0d2aabd702a | ok |

## Queue

J001 (running) → J004 (maze maps) → J002 (sweep 1d, when pc/STATUS says the PC stopped its copy) → J005 branch
farm / J003 retry round 1 by priority.
