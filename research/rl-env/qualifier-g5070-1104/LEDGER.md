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
  - `scr-govmem-01` JD_GOV=7 + JD_MEM + JD_EVTONCE=160: 0 faults, fuel-outs 55 vs 461, but paired **-0.28** (CI
    -3.19 to +2.64). Per opponent: p65pack +1.7, v92 -1.7, x3inv -1.1; large maps -2.5. The two single-switch deltas
    do not add. Every fuel change reshuffles fight outcomes, so dev deltas of about 2 points are within game-chaos
    noise. No combination is carried forward on dev evidence.
- Claude (#6, 02:32Z) asked how JD_EVTONCE differs from X1_RESPAWNFIX (the v92audit bundle lost 47-57 on the ladder,
  only 10 games paired). X1_RESPAWNFIX only rejects decodes more than N rounds ahead, and still re-applies the same
  word every turn. The fixture shows it passes 279 of the 341 phantom turns. JD_EVTONCE applies each distinct word
  once and keeps the same horizon, so it is a superset. Claude also asked for the switch to be tested on its own
  through dev and selection: scr-mem-01 already ran it without JD_GOV, and selection runs follow.
- Selection screens (100 select maps x {v92, x3ctr, p65, v86h} x both sides = 800 paired cells; v92 base: 412 wins,
  317 fuel-outs in 109 games):
  - `sel-gov-01` JD_GOV=7: 0 faults, **fuel-outs 10 vs 317 (-97%)**, paired **-2.12** (CI -6.5 to +2.1). x3ctr
    -8.5 (CI -15.5 to -1.5); large maps -11.7 (CI -24.2 to +0.8), which is below the -10 stratum rule.
    **Rejected as a bundle.** Suspensions are not where v92 loses games: a suspended turn still finishes its work on
    the next budget and loses one action, while deferring the work costs decision quality on big maps.
  - Per-bit ablation:
    - `sel-gov1-01` (field-order admission): fuel-outs 308 vs 317, paired +0.12 (CI -1.12 to +1.38), small -1.1,
      medium +1.9, large -0.8. Neutral, safe infrastructure. **Conditionally useful** (keep available, default 0).
    - `sel-gov2-01` (row-chunked siege table): fuel-outs 246 vs 317, paired -1.5 (CI -4.0 to +0.9), large -5.5 (CI
      -16.4 to +3.9). The unfiltered ring during the build costs siege quality. **Parked.**
    - `sel-gov4-01` (resumable bush labelling, X1_BUSHPRE 50): **fuel-outs 83 vs 317 (-74%)**, paired -0.12 (CI
      -4.12 to +3.88). v86h +4.0, x3ctr -4.5, medium +2.8, large -3.1. Neutral within noise, and it removes the
      largest share of suspensions. **Conditionally useful.**
    - `sel-noop-01` neutral control (X1_NOOP: a behaviour-free volatile increment): paired -0.12 (CI -0.88 to
      +0.62), fuel-outs 316 vs 317. A tiny fuel shift changes few games. Switches that move a lot of fuel per turn
      (bit 4 prelabels every turn) reshuffle many more cells, hence their wider CIs. A deterministic v92 base is one
      draw per cell, and every candidate shares that draw, so their deltas are correlated. For example, every variant
      is negative on the same 16 large selection maps.
    - `sel-gov5-01` **JD_GOV=5** (bits 1+4): 0 faults, **fuel-outs 87 vs 317 (-73%; games 75 vs 109)**, paired
      **0.00** (CI -4.0 to +4.0). v86h +4.0, v92 +1.0, p65 -0.5, x3ctr -4.5; small -1.7, medium +2.8, large -2.3. No
      stratum below -10. **Conditionally useful**: neutral fuel-safety infrastructure with no win gain. It is the
      recommended governor setting if a later mechanism needs fuel headroom (NN inference, contact search). Default 0
      until FEAT-005.
- FEAT-002 decision: no JD_* default changes. JD_GOV and JD_EVTONCE do not raise win rate, and the evidence (Claude
  agrees, #6 02:52Z) says suspensions are not where v92 loses. Remaining effort goes to decision quality (FEAT-004)
  and the RL actor (FEAT-003). The governor API (`rb::admit_optional` with kNN/kTactical/kRoute) is the admission
  path for those mechanisms.
  - `sel-evt-01` JD_EVTONCE=160 alone: 0 faults, fuel-outs 320 vs 317, paired -0.88 (CI -3.75 to +1.88), large
    -5.5. With dev +1.25 and selection -0.88, it has no measurable game gain. **Parked**: correct by fixture, not
    worth enabling.
## FEAT-003 RL actor runtime, export, bounded training launch (2026-11-04 03:12Z-)
- User decision (supersedes the earlier "no training"): bounded branch-local RL training/distillation is allowed
  on this machine. Agent 2 keeps RL ownership; builder note posted in #6 (seq 16) before training. JOHNDOE
  registered the job as task `rl-distill-local` epoch 1 (03:54Z). Nothing is pushed to agent2-neural.
- Checkpoints preserved unchanged in `jd-eval/checkpoints` (student_i2, nn_rl3/best, nn_rl3/teacher_0,
  nn_rl2/best). The git blobs match 56b60b96; SHA-256 values are in MODEL_MANIFEST.json. **Accepted**. No `.pt` is
  committed.
- Torch: the pypi/cu128 index gave a CPU-only 2.15.0 wheel on Windows. Installed `torch 2.14.1+cu130` from the
  cu130 index into `.venv-jd` (outside the repo). The RTX 5070 Ti works.
- Export: Agent 2's `nn_export.py` unchanged, run twice: byte-identical header (sha256 36ad83e1...). **Accepted**.
  Finding: `%.7e` drops float32 round-trip precision (3.8e-3 max logit error vs the checkpoint; argmax
  unchanged). A branch-local `%.9e` exporter would fix it (Claude relays this to Agent 2).
- Port: `tools/jd_g5070-1104/mk_nn.py` (idempotent, lab blobs verified) applies nn_mkbot.py's patches behind
  A2_NN = JD_NN (default 0). The default build is still 5704d7ba (= v92). **Accepted** (working).
- Golden fixtures: `nn_golden.py` on nn-golden-05: 32/32 features identical between capture and use, argmax
  32/32, 1.1e-5 vs the exported network. Host C++ agrees on 64 saturated/random rows; `nn_infer_test` passes
  2803 checks. **Accepted**. Runs nn-golden-01..04 were debugging runs:
  - 01: Agent 2's overrun rule locked the pipeline after the 200k first turn.
  - 02: the stdout capture splits separate printf writes.
  - 03: one REC row printed with std::string + printf cost ~95k.
  - 04: the exporter rounding.
- `JD_NN_EVENT` runtime (event-driven, pipelined, governor-admitted, v92 fallback, farm() skips v92 scoring while a
  network target is held). It fits official fuel: 0 faults, 16/74 suspended network steps per 96/180 games after
  the v3 estimate fix. Network fuel per decision p50 ~105k, p95 ~128k, spread over 1-4 turns. Runtime **Accepted**
  as infrastructure.
- Benchmarks (NN_BENCH.md; paired vs v92):
  - nn-every (Agent 2's every-turn student at official fuel): 0/96 conf, 3/180 dev. **Rejected**.
  - nn-event: dev -9.4 (v1) and -11.1 (v3), CIs exclude 0; conf about 0. **Rejected for release** (heads OFF).
  - Cadence revision 1, target-only (`JD_NN=1`): conf -4.2. **Rejected**.
  - Cadence revision 2, KEEP-dominant residual (`JD_NN_RESID=1`): conf -5.2, dev -19.4. **Rejected**.
  - Two revisions without a credible gain: stopped revising, as planned.
- nn-zero (data-only control) is not neutral: conf +12.5 (+3.1, +20.8) in v1, +6.3 / +5.2 later; dev neutral.
  Prime suspect: `nn_feats` (A2_NN_FAST) builds every group distance field on the 200k first turn.
  **Conditionally useful (mechanism unverified)**. Conf/dev were used to find it, so isolate it as its own switch
  and judge it only on selection plus the large-map stratum, then holdout.
- Training `rl-dagger-01` launched 03:42:05Z: python PID 25780 (launcher 23600), pinned to CPUs 14-19, below-normal
  priority, 5 game jobs, self-stop 08:42Z.
  - Method: DAgger with nn_rl3/best as the expert. The student starts from student_i2. Data comes from the JD_NN_EVENT
    recorder at official fuel on poolfresh 121-209 vs v92/x3inv/p65pack; the eval is 40 poolfresh maps 210-249 vs
    v92/x3inv.
  - It was not relaunched after the runtime v2/v3 fixes; JOHNDOE grandfathered it. Its checkpoints get re-evaluated on
    the final runtime at harvest (FEAT-005).
  - iter0 (seed) eval: 95/160 vs v92's 93/160 (+1.25).
  - iter1: 91/160 (-1.25).
