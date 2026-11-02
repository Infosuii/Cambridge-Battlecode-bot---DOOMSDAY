# g5060 status, 2 Nov 2026

Workers: 6 (threads-2).

## Notes that change how jobs run

1. `tools/dz.py` caps parallel games at `min(4, --workers)`, so `WORKERS=6` ran 4 at a time. build/z-plan-5060
   57af220 adds `DZ_MAX_PARALLEL` (default 4); I run 6: 121 games/min, replays still exact (results/J001.md).
2. `dz.py smoke` appends to `research/dz/SEED_LEDGER.md` and exits non-zero ("runtime gate failed") on any
   fuel-out, after writing results.json. x1_gate.sh tolerates that; I report every fuel-out.
3. Maze maps (J004, pc/msgs/0005): **I do not hold the maze files** (msgs/0004); waiting for maps/agent2-maze.
   Earlier note: Iniya is pushing Agent 2's maps_mazetest / maps_real200b (+ mapmake5.js) to branch
   `maps/agent2-maze`; I'll put maze-test 0-59 + real200b 50-109 in maps/x1-maze on build/z-plan-5060 when it lands.
   PC fallback set not needed unless this stalls.

## Running (~11:00 UTC)

- Stand-in build notes (findings/0005, from findings/0002 S1 / S2) with a no-new-code S1 prototype measured vs x1.
- J014 set-B cells (g5060_maze_*) run as soon as the PC merges set B (3ca52e9) into build/z-plan.

## Done

- **J014 done** (results/J014.md, maze set A): bp -7 on maze (fails the full gate on maze); with maze included,
  vs x1: **bpp4r150 347 vs 316 pass (+31; up on every kind)**, bpp4r100 +22 pass, bpbelief +13 pass, bptsvis +16 fail.
- J013 addendum bpsf55: pass vs bp (+2, fuel-outs -4).

- **J013 done** (results/J013.md): **bp passes +18 vs x1, fuel-outs 339 -> 206**; on top of bp only plan 4 R150
  (+10, fuel +21) and TS_VIS (+1) are above bp; ANTIFEED 3/250 -7, P5bp -13. Gains of +10..+27 vs x1 did not carry over.

- **J015 done** (results/J015.md): maze set B, 30 maps, **build/z-plan-5060 3ca52e9**; screen 0 faults, 0.53 fuel-outs
  a game. Gate report updated for the maze rule of msgs/0009 (3ca29b0).

- Sweep flags R1 batch 3: A2_TS_VIS +11 (fuel +84), A2_BELIEF +5 (fuel +10), A2_RESETFIX -4, A2_FIELDFIRST -13,
  A2_ASSESS -35 (5,214 fuel-outs). All J002 flags at or above baseline now gated.

- Sweep flags R1 batch 2 (results/RQ6-sweep-leaders.md): **A2_HIDEREC pass +7**, **A2_BURST_HOLD pass +3**;
  V58_LOCKS +8 and A2_DISENGAGE +7 fail on fuel-outs only; A2_THREAT -2, A2_MAP_PROFILE -6, APEX_STALE_BAG -11.

- Sweep leaders R1 (results/RQ6-sweep-leaders.md): **APEX_ESCORT pass +8** (fuel -7); A2_BURST2 +13 fails on fuel
  +20; V58_VISION -13.

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

J013 (running, then the bpsf55 addendum) → J014 maze gates (blocked: no maze set, msgs/0004) → stand-in build notes
(findings 0002 S1/S2, with a no-new-code S1 prototype measured vs x1) → retry-queue gates when idle. J011 / J012 are
the 5070's (K004, pc/msgs/0006); K002 / K003 closed (done here as J007 / J002).
