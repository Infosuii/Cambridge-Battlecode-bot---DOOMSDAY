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

## Running (07:20 UTC)

- No posted job open. Idle work per the brief: next owed retry-queue gate. #1, #2, #4 need code knobs from the PC;
  #3 done (dead path). Next runnable: **R1 full gates for the J002 sweep leaders** (V58_VISION, A2_BURST2, APEX_ESCORT,
  all +7 on the sweep cells; queue #6 / #8 / #9 owe R1 vs x2) on the full gate. Starting with those three, ~15 min.

## Done

- **J002 done** (results/J002.md): 34 binaries played; best V58_VISION / A2_BURST2 / APEX_ESCORT +7 each on 76
  games (vs 17 + 19); A2_POLICY -27; 30 same-binary, A2_MOVENET does not compile, 6 fire on 0-1 games.

- **J007 done** (results/J007.md): **soak64 pass +10** (fuel -12); prunefix +11 (fails styled, fuel +26); fleehold
  4/8/15 -18/-32/-70; teamwin -1; heartfix 0; siegestrict +1. 5 of 6 expected hashes are not from the pushed source.

- Retry #3 (results/RQ3-hunt-solo.md): X1_HUNT_SOLO 3 / 5 under plan 8 from R150: 0 / 480 games changed: still a
  dead path (R0). Side result p8r150 vs x1: 261 (+4), fuel-outs +34.
- findings/0003: retry #4 step 1, per-champion results vs v88 (Willow 45%, 4.6 deaths; Ryth best).

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
