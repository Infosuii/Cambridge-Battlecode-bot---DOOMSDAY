# g5060 status, 2 Nov 2026

Workers: 6 (threads-2).

## Notes that change how jobs run

1. `tools/dz.py` caps parallel games at `min(4, --workers)`, so `WORKERS=6` ran 4 at a time. build/z-plan-5060
   57af220 adds `DZ_MAX_PARALLEL` (default 4); I run 6: 121 games/min, replays still exact (results/J001.md).
2. `dz.py smoke` appends to `research/dz/SEED_LEDGER.md` and exits non-zero ("runtime gate failed") on any
   fuel-out, after writing results.json. x1_gate.sh tolerates that; I report every fuel-out.
3. Maze maps (J004): not available (msgs/0002).

## Running

- **J005 branch farm**: `tools/x1_farm.py run --name j005` (build/z-plan-5060 ce41381). x1 at e15b68d, 25 builds
  (base X1_PLAN=1 R5000 I6 + plans 1-8 x R250/150/350), all code sections be66c8804ef0, 25 distinct binaries.
  x2 + x2-s2, 70 ladder + 50 styled, both sides: 480 baselines + 11,520 branches. Every branch is diffed against its
  baseline: **3,427 of 3,427 so far equal the baseline before the switch round** (0 violations).
- pc/msgs/0002 applied: every row now has `cp` (both teams' banked, gems, gold, kills, deaths, collected, earned
  gold, damage at R150/250/350/500) plus gold250 / gold500; the per-switch-round position features already carried
  our and their deaths and kills. The farm was stopped at 3,681 games and restarted at 00:31; rows written before
  the change are replayed once (checked equal to the old row: `replay_match`). ETA ~01:55.
- Gate reports will add mean gold@R250, gold@R500, deaths per game and finish round (from results.json checkpoints).
- Stand-in (after J003): no "contact aura" bot on any branch; candidates to build from are `bots/mimic` and
  `bots/proxy` (top-team imitation, claude/compare-fix-replay-decoder and build/z-plan). Proposal follows after J003.

## Done

- J001 (results/J001.md): **done, exact.** Hashes ok; x1 vs x2 ladder 68/140 and x1 vs v86h 79/140 replay the
  PC's runs game for game (replay sha256 equal on all 280 games).
  Throughput 121 games/min with `DZ_MAX_PARALLEL=6` (build/z-plan-5060 57af220; stock cap is 4).
- J004: maze maps not available here (msgs/0002). Gates run ladder + styled until maps/x1-maze exists.

## Queue

J005 (running, ETA ~01:55) → **J006** antifeed gate (worktree `C:\x1run-846e8ce` at 846e8ce, ready; base gate
x1g-base-* on x2-s2 runs first, x2 base = x1e-cw-*-x2) → J002 sweep 1d → J003 retry round 1 → stand-in proposal.
Gate verdicts by tools/x1_gate_report.py (build/z-plan-5060 8fbea60): wins, fuel-outs, faults, gold@R250/R500,
deaths/game, finish round per cell.
