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

## Running (22:25 UTC)

- **J022** gate with the fixed x1_mapfit.h (run tag x3mf2; the first table never fired, msgs/0006): pool vs v92 / v86h /
  x1bru, ~10 min. Fit: 13 of 16 maps get rows (e.g. 03membrane 0.163 -> 1.404, 03fan 0.194 -> 1.029, 03showdown
  0.178 -> 0.749 fit / game); 3 keep v92 (00happy-halloween, 03colosseum, 03riverbed).
- Then J023, J019 screens, J021 runs.

## Done

- **J024** (results/J024.md): counter table **171 / 172 vs v92** (exact replay) after fixing the table keys
  (tools/x3_counter.py --fp, build/z-plan-5060 0f2c65ba); costs -4 vs v86h, -8 vs x1bru (v92-specific).

- **J018** (results/J018.md): on x3, BUSHPRE -48 (z -2.77, all on the pool), SECURE +3 (not shown), WALKTAIL -5, all -45.
  x3 vs x1: pool 77%, styled 38%, maze 45%.

- **K010 Part A** (results/K010.md): vs v92, x1 21 / 140 ladder but 62 / 100 styled, 65 / 118 maze; x1c1 57 / 59 / 55;
  v86h 49 / 50 / 58. x1 vs v86h 194 / 358. v92 looks ladder-map-specific.

- **J017 + K010 Part B** (analysis/J017.md, blind): of 116 losses, 47% conversion (collected, not banked: 36 losses
  had >= 1000 net collected), 28% feeding (few-camp maps), 22% slow economy; 77 of 80 opponent-map groups are uniform.

- Maps on git: build/z-plan-5060 5b8ceddd now carries all 59 maze maps (set A copied from build/z-plan + set B) and set
  B's 10 leftover candidates in maps/x1-maze-g5060-extra (reference only, not gated).

- **Rule 15** (results/RQ15-rule15.md, msgs/0005): bp -18, p4 -23, bpp4r150 -22 vs x1 against v86h + v81hl (z ~ -1.6);
  pooled with x2 / x2-s2, bpp4r150 z +0.44: no line shown better than x1 yet.

- **I-60-03 / findings 0006**: gate noise floor (no-op builds -8..+3, |z| < 1) and a paired sign test for every
  line: no gain so far reaches z >= 2 except SECURE (4-0); BP + plan 4 R150 z = 1.99. Report tool prints z (c754366f).

- **I-60-01** (results/I-60-01.md): walking-distance fields faster (FIELDQ 4/6/20) on P4: -14 / -23 / -43; retry
  pending (R3). Draft-time version failed R0 by design. I-60-02 (first-turn fuel-outs on 6 maps): finding, parked.

- **J016 done** (results/J016.md): on p4 only X1_SECURE passes (+2, 34 games changed); HIDEREC +4 fails on fuel;
  others -2..-42. p4 + all passes = p4secure 417.

- J014 set-B cells (results/J014.md): bp +3 on set B (-7 on A); with A+B pooled (716 games) vs x1: bp +14 pass,
  **bpp4r150 +39 pass**, **bpp4r100 +36 pass**, bpbelief +14 pass, bp2050 +13 pass, bptsvis +13 fail (maze -2.5 pts).

- findings/0005: stand-in build notes; S1a / S1b / S2a no-new-code prototypes measured (x1 wins 74 / 78 / 103 of 140;
  none out-farms x1); proposal S3 action-replay opponent (the audit harness), S1 / S2 real versions.

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
