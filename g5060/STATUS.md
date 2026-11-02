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

## Running (03:56 UTC)

- **J003** retry round 1 (0b3703b, latest build/z-plan): secure15 / secure3 / secure6 / alone, 4 lines -> ~04:12.
- Then: stand-in proposal (findings), then retry-queue gates by lowest # (RETRY_QUEUE.md) while idle.

## Done

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

J005 (running, ETA ~02:00) → **J009** whole-game plan gates (846e8ce, has X1_PLAN) → **J006** antifeed (846e8ce)
→ **J008** bag-risk (2636803) → J003 retry round 1 → stand-in proposal → J002/J007 remainders from g5070.
All gates run in one worktree `C:\x1run-846e8ce`, moved to each job's commit; the base gate (x1g-base-*, x1
1746f2bb7fa3, x2 + x2-s2, ladder + styled) runs once before J009 and is the base for all of them (x2 cells also
checked against the PC's x1e-cw-*-x2). Verdicts: tools/x1_gate_report.py (wins, fuel-outs, faults, gold@R250/R500,
deaths/game, finish round per cell).
