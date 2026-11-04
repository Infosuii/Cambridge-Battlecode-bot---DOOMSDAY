# LEDGER: run g5070-1104

Autonomous decisions and outcomes (classes: Accepted / Retry required / Conditionally useful / Parked / Rejected).

## FEAT-001 foundation (2026-11-04 01:30Z-01:50Z)

- Candidate `bots/jd-g5070-1104/src` = copy of `bots/x3/src` + `jd_config.h` (all JD_* default 0). Default release
  build SHA-256 `5704d7ba...6d47` = v92. **Accepted** (strict zero control).
- Eval root `jd-eval` needs `cmake/` copied from the worktree, otherwise `cambc build` fails at cmake configure.
- `cambc run-batch` resolves manifest paths relative to the manifest's directory, and the eval path contains spaces,
  so `jdrun.py` writes `../../bots/...` and `games/...` relative paths.
- Toolchain-identity smoke `conf-smoke-01`: 3/6 wins, 0 faults, 0 fuel-outs (Claude's reference matches on these);
  mean banked 893.3 versus Claude's 734.7. Claude did not post his three maps, so this is recorded as a map-set
  difference, not a toolchain difference; the hash identity is the binding check. **Accepted**.
- Baseline `base-v92-pool-01` (v92 vs x3inv, b5_c3, v61_c3, public-khiri; 86 pool maps x 2 sides = 688 games):
  688 played, 0 missing, 0 failed, 0 faults, 72.1% wins, **705 fuel-outs in 183 games** (engine `fuelExhausted`
  events; the replay-trace count agrees exactly, 705). Fuel-outs concentrate on maps (02the-pack 99, 01islands 81,
  03the-front 79, 03contours 60, 02gift-wrapping 51) and are spread evenly across opponents (159-188). Self-play
  has none. Input for FEAT-002's fuel contract and governor.
- RL: no training, distillation, PPO or DAgger in this run (final user clarification). Agent 2 owns RL.
- **Anti-overfitting rule (user directive ~01:45Z, binding on every later step).** Frozen partitions of maps and
  opponents before any tuning: development (`dev` 90 generated/poolfresh maps, `conf` = its 16 largest; opponents
  v92, x3inv, p65pack, public-khiri), selection (`select` 100 generated/poolfresh maps; x3ctr, p65, v86h, v92),
  final holdout (`pool` 86 competition maps incl. all official70 + `fresh51104` 100; b5_c3, v61_c3, public-decrest,
  public-wardens, x3mf2, v92). Hashes in RUN_MANIFEST.json, rules in GATES.md. Never tune/debug/trace on the holdout
  (`jdrun.py run` refuses holdout maps/opponents without `--holdout`). Select on matched paired wins across diverse
  opponents/maps with map-clustered CI, not v92 self-play or one opponent; v81/x1 are inflated. Few knobs, geometry
  or continuous features rather than map-identity rules. Report the dev-vs-holdout gap per finalist; dev-only gains
  are "Conditionally useful". Do not chase single ladder results.
- The earlier draft used 10 pool maps in `dev` and pool maps for `conf`; both were replaced before any tuning.
  `base-v92-pool-01` (holdout maps + 2 holdout opponents) is relabelled holdout baseline, reporting only.
- Development baseline `base-v92-dev-01` (v92 vs x3inv, p65pack, public-khiri, v92 on `dev`, both sides): 720/720
  played, 0 faults, 71.0% wins, 461 fuel-outs in 97 games (trace count 462; the one-turn difference is the trace
  rule's respawn ambiguity). 498.9 games/min. Use these replays for FEAT-002 fuel profiling and FEAT-004 defect
  tracing.
