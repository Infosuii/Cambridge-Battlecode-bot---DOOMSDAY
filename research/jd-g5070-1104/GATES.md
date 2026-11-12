# Gates for run g5070-1104

All games use official fuel (no `--fuel-quantum`), release builds, frozen candidates (`jdrun.py freeze`), both sides,
and the paired runner `tools/jd_g5070-1104/jdrun.py` (candidate and base on the same opponent/map/side cells).
Eval root: `c:\projects\cambridge battlecode\battlecode part 2\jd-eval` (outside the repo). Full map-set SHA-256
digests are in RUN_MANIFEST.json (`map_sets`).

## Anti-overfitting rule (user directive, 2026-11-04 ~01:45Z; binding on every later step)

1. **Frozen partitions.** Development, selection and final-holdout partitions of maps AND opponents were frozen
   before any tuning (table below). Their hashes are in RUN_MANIFEST.json. Never tune, debug or trace defects on the
   holdout. `jdrun.py run` refuses holdout maps/opponents unless `--holdout` is passed, and records the partition in
   each run's `run.json`. Use `--holdout` only for final confirmation and for reporting-only baselines.
2. **Selection.** Select on matched paired wins across diverse opponents and maps, with map-clustered uncertainty.
   Do not select on v92 self-play or on one familiar opponent. v81/x1 are inflated in v92-family fits and are not
   used as selection evidence.
3. **Knobs.** Keep the number of knobs small. Prefer geometry/continuous features over map-identity rules (no
   per-map-name tables in new code).
4. **Reporting.** Report the dev-vs-holdout gap for every finalist. A gain that holds on dev/selection but not on the
   holdout is "Conditionally useful" (experimental), not "Accepted".
5. **Ladder.** Do not chase single ladder results.

## Partitions

| Partition | Maps (set name: count) | Opponents | Use |
|---|---|---|---|
| development | `dev`: 90 = 30 from `mapmake6.js seed 1104` + 60 Agent 2 poolfresh maps (sorted first 60, prefixed `pf_`). `conf`: the 16 largest `dev` maps | v92, x3inv, p65pack, public-khiri | debugging, defect tracing, fuel profiling, conformance, early screens |
| selection | `select`: 100 = 40 from `mapmake6.js seed 3307` + 60 poolfresh maps (sorted 61-120, `pf_`) | v92, x3ctr, p65, v86h | choosing between revisions and finalists |
| final holdout | `pool`: 86 competition maps (contains all 70 `official70` maps) + `fresh51104`: 100 from `mapmake6.js seed 51104` | v92, b5_c3, v61_c3, public-decrest, public-wardens, x3mf2 | confirmation only, after the 09:05Z tuning freeze |

Cross-set check: no generated or poolfresh map duplicates any other set by SHA-256; `official70` is a subset of
`pool`. v92 appears in every partition because it is the paired base, not a tuning target.

The run `base-v92-pool-01` (v92 vs x3inv, b5_c3, v61_c3, public-khiri on `pool`) was played before the directive.
It is relabelled **holdout baseline, reporting only**: do not use its replays to tune or trace defects. The
development baseline for FEAT-002/FEAT-004 is `base-v92-dev-01` (v92 vs x3inv, p65pack, public-khiri, v92 on `dev`).

## Level 1: conformance (per switch, before any screen)

`jdrun.py run --name conf-<switch>-NN --cand <frozen> --base v92 --opps v92 --maps conf --jobs 14` (16 maps x 2 sides).

Pass requires all of:
- 0 bot faults (`botFaults`) and 0 missing/failed games.
- Fuel-outs (engine `fuelExhausted` events, cross-checked with the replay `team-?.fuel` trace) not above v92 on the
  same cells.
- The mechanism's trigger counter > 0 (logged by the switch). A mechanism that never triggers has no evidence.
- Default build (all JD_* = 0) still hashes to `5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47`.

## Level 2: screen and selection

Screen on `dev` vs the development opponents (4 x 90 x 2 = 720 cells per arm), then decide on `select` vs the
selection opponents (4 x 100 x 2 = 800 cells per arm). Decide on the paired score delta (win 1, draw 0.5, loss 0;
reported in points = 100 x score) with the map-clustered bootstrap 95% CI (2000 resamples, seed 1104), plus banked
gems and deaths, per-opponent and per-size strata. Stop a mechanism after two sound revisions without a credible gain
and move to the next one.

## Level 3: frozen confirmation (at most three finalists)

`--holdout` runs on `pool` (86) + `fresh51104` (100) vs the holdout opponents, both sides: 6 x 186 x 2 = 2,232
matched cells per arm. Report exact played/missing/failed counts, per-opponent, per-map-category and per-size strata,
draws, the map-clustered CI, `fresh51104` separately, and the dev-vs-holdout gap. A clean rebuild of each finalist
must reproduce its hash.

## Promotion rule (mission sec.8)

A candidate is promoted only with all of:
1. Zero new faults or illegal actions versus v92 on the same cells.
2. Fuel-outs not above v92 on the same cells, and no new suspension failure mode.
3. Paired delta > 0 on the level 3 holdout, with the CI reported. If the aggregate is positive but `fresh51104` alone
   is inconclusive, the candidate is labelled experimental and v92 stays recommended.
4. No opponent stratum or map category with a paired delta below -10 points unless the cause is explained.
5. A gain on dev/selection that does not hold on the holdout is "Conditionally useful", never "Accepted".

Ladder trials additionally follow the #5 LOCK / Claude ACK / UNLOCK protocol and the promotion policy in Claude's
issue #5 message #5 (pinned paired duel, >= +6 net wins over a fresh v92 rerun, repeated on a second plan seed).

Outcome classes (AGENTS.md): Accepted / Retry required / Conditionally useful / Parked / Rejected.
