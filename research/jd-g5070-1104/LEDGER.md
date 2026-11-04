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
- Claude then named his maps (00corners, 00crater, 01gold-rush). `conf-smoke-02` on them: 3/6, 0 faults,
  0 fuel-outs, mean banked 734.7, an exact match. Toolchain identity **Accepted**.
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

## FEAT-002 fuel contract, governor, memory (2026-11-04 01:58Z-)

- Profiling runs on the dev partition only. The FEAT text said base-v92-pool-01, but that run is holdout (FEAT-001
  partition rule), so `base-v92-dev-01` is used instead.
- Conformance used the 16 `conf` maps x {v92, x3inv, p65pack} x both sides (96 cells), a superset of GATES.md's
  "vs v92", for two reasons. v92 self-play hides most suspensions, and the same cells were used for the profile.
- **JD_FUELPROBE** (diagnostic) `diag-fprobe-02`: 32 games, 0 faults. The fuel contract is in fuel_contract.json
  (phases, draft-VM lifetime, no carry-over, no global transfer, respawn = plain 100k). **Accepted** as diagnostic.
- **JD_FUELPROF** (diagnostic) versions:
  - v1 (A2_TEL + printf dumps) `diag-fprof-01`: 32,618 fuel-outs. **Rejected**.
  - v2 (chunked dumps) `diag-fprof-02/03`: 9,732 / 8,730 fuel-outs. **Rejected**.
  - v3 (own trail, deferred aggregation, self-limiting dump) `diag-fprof-04`: 136 fuel-outs vs v92's 147 on the same
    cells, +7.6k mean fuel per turn. **Accepted** as diagnostic.
  - v4 adds the JDSUS trail of each suspended turn (`diag-fprof-06`).
- **Memory fixtures** (`host_tests.py`, mem_test 32,253 checks, 0 failures) prove two reader defects in the current
  schema: phantom respawn events from the mod-256 wrap, and the mod-64 sighting age wrap. They also show a latent
  ML-plan byte erase (A2_MLPLAN + A2_DPLAN both on, default off) and no claim aliasing for 1-255 groups (groups
  >= 126 are dropped to idle). Schema and answers are in MEMORY_SCHEMA.md.
- **JD_MEM** (owner/merge + codec; bit-identical bytes in the default config) + **JD_EVTONCE=160** + JD_SIGHTAGE,
  run `conf-mem-01` (JD_MEMLOG build): 0 faults, fuel-outs 141 vs 147, paired +9.4 points (95% CI +4.2 to +15.6, 96
  cells, 16 maps). Triggers: evt_phantom 775 (27/96 games), evt_horizon 404 (51 games), sight_phantom **0**.
  - JD_MEM + JD_EVTONCE: conformance passed, so they go to the dev screen.
  - **JD_SIGHTAGE: Parked.** The fixture proves the defect, but the case never triggered in 96 real games: a
    sighting is never left unchanged for 64+ rounds while being read.
- **JD_GOV** whole-turn reservations. The stages come from the JDSUS trails: first-turn field-order prep, ward_reveal
  bush labelling and siege opacity table.
  - `conf-gov-01` (first version, JD_GOVLOG build): 0 faults, 57 fuel-outs vs 147, paired +7.3 (CI -1.0 to +16.7).
    Bit 2 as a one-shot admission was refused 607 of 610 times, which in effect disabled siege sight filtering on
    big maps. **Retry required**; it was reworked to a row-chunked build.
  - `conf-gov-02` (JD_GOV=7, row-chunked bit 2): 0 faults, **55 fuel-outs vs 147 (-63%)**, paired +4.2 (CI -5.2 to
    +13.5). Triggers: field_order skipped 3,800 times (18 games; all 468 VMs eventually prepared it), siege rows
    1,523 built / 401 deferred (37 games), bush_deferred 580 (32 games). Conformance passed, so it goes to the dev
    screen.
- Dev screens (90 dev maps x {v92, x3inv, p65pack, public-khiri} x both sides = 720 paired cells; the base arm
  reproduces base-v92-dev-01 exactly: 511 wins, 461 fuel-outs):
  - `scr-gov-01` JD_GOV=7: 0 faults, **fuel-outs 56 vs 461 (-88%; games with any 9 vs 97)**, paired +2.2 points (CI
    -1.25 to +5.28). Per opponent: x3inv +5.6, v92 +2.2, p65pack +1.1, khiri 0 (100% both). Per size: small +1.7,
    medium +3.1, large +0.8. No opponent or size stratum is below -10. **Conditionally useful**: an enabling fuel
    fix with a dev-only, not significant win delta. Selection and holdout confirmation happen in FEAT-005; the
    default stays 0.
  - `scr-mem-01` JD_MEM + JD_EVTONCE=160 (+ JD_SIGHTAGE, which never triggers): 0 faults, fuel-outs 456 vs 461,
    paired +1.25 (CI -1.39 to +4.03). Per opponent: p65pack +2.2, x3inv +2.2, v92 +0.6, khiri 0. **Conditionally
    useful**: a correctness fix (phantom respawns) with no measurable dev gain; the default stays 0.
