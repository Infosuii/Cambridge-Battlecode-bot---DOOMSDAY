# g5060 status, 2 Nov 2026

Workers: 6 (threads-2).

## Notes that change how jobs run

1. `tools/dz.py` caps parallel games at `min(4, --workers)`, so `WORKERS=6` ran 4 at a time. build/z-plan-5060
   57af220 adds `DZ_MAX_PARALLEL` (default 4); I run 6: 121 games/min, replays still exact (results/J001.md).
2. `dz.py smoke` appends to `research/dz/SEED_LEDGER.md` and exits non-zero ("runtime gate failed") on any
   fuel-out, after writing results.json. x1_gate.sh tolerates that; I report every fuel-out.
3. Maze maps (J004): Iniya is pushing Agent 2's maps_mazetest / maps_real200b (+ mapmake5.js) to branch
   `maps/agent2-maze`; I'll put maze-test 0-59 + real200b 50-109 in maps/x1-maze on build/z-plan-5060 when it lands.
   PC fallback set not needed unless this stalls.

## Running (04:30 UTC): idle work, retry queue

- No posted job open, so per the brief I run the next owed retry-queue gate (lowest #). #1 (X1_SECURE v2) and #2
  (X1_ALONE radius knobs) need code from the PC. **Running #3 X1_HUNT_SOLO** under a hunting plan (it was a dead path in
  default play): base = X1_PLAN=1 R150 plan 8 (push, hunt +3), lines + HUNT_SOLO 3 / 5, at 0b3703b. 3 lines, ~11 min.
- Next idle item: #4 X1_MASTERY step 1 (recompute per-champion results from x1's own games vs v88: the 480 J005
  baseline summaries + gate base games), then its R2 if the PC adds a bias knob.

## Done

- findings/0002: sparring stand-in. proxy and x1-push measured (x1 wins 112 and 89 of 140; neither out-farms x1);
  proposal S1 fast farmer / S2 early contact for the PC to build.

- **J003 done** (results/J003.md): secure15 +4, secure3 +4, secure6 +2 **pass** R1 (first passes; 12-20 of 480
  games change); alone -25 fail.

- **J008 done** (results/J008.md): bag30 -29, bag50 -7, bag80 -4 (loss on ladder maps); all fail R1.

- **J006 done** (results/J006.md): all six lines +8..+27 wins; af3w250 284 (+27, fuel +3, deaths 9.4); af4 +14,
  af7 +13. All fail R1 on the fuel-out clause only.

- **J010 done** (results/J010.md): stage05 268 (+11, fuel +3), wait20 +9, wait15 +8, need13 +6; flee-drop fd15 -6,
  fd25 -28, fd40 -25, fd60 -32. All fail R1. findings/0001: fuel-out clause decides most verdicts.

- **J009 done** (results/J009.md): p4r100 280 vs 257 (+23, fuel-outs +9), p4r150 +18 (+47), p6r150 +13 (+12),
  p3r150 +6 (+6), p4r0 -7, p6r0 -1; all fail R1 (fuel-out totals or win totals). Run records on build/z-plan-5060 63e311e.

- **J005 done** (results/J005.md, J005/rows.jsonl): 480 baselines + 11,520 branches; prefix identity 11,512 / 11,512;
  3,907 replays equal; 0 faults. Best nets: plan 4 @R250 +27, @R150 +23; plan 6 @R150 +18, @R350 +16; plan 7 @R350 +15.

- J001 (results/J001.md): **done, exact.** Hashes ok; x1 vs x2 ladder 68/140 and x1 vs v86h 79/140 replay the
  PC's runs game for game (replay sha256 equal on all 280 games).
  Throughput 121 games/min with `DZ_MAX_PARALLEL=6` (build/z-plan-5060 57af220; stock cap is 4).
- J004: maze maps not available here (msgs/0002). Gates run ladder + styled until maps/x1-maze exists.

## Queue

Stand-in proposal → idle retry-queue gates → J002 / J007 remainders when g5070 stops → J011 / J012 when posted.
Every posted job runs ahead of idle work.
