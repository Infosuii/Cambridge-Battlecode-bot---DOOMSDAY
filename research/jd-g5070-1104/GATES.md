# Gates for run g5070-1104

All games use official fuel (no `--fuel-quantum`), release builds, frozen candidates (`jdrun.py freeze`), both sides,
and the paired runner `tools/jd_g5070-1104/jdrun.py` (candidate and base on the same opponent/map/side cells).
Eval root: `c:\projects\cambridge battlecode\battlecode part 2\jd-eval` (outside the repo). Map-set digests are in
RUN_MANIFEST.json.

## Map sets

| Set | Maps | Source | Use |
|---|---|---|---|
| `conf` | 16 | ladder-pool: 00ambush, 00collision, 00great-wall, 00lanes, 00packs, 00the-line, 01big-world, 01corridors, 01islands, 01starvation, 02arena, 02famine, 02the-pack, 03colosseum, 03honeycomb, adgato-gemcombat3 | level 1 conformance |
| `dev` | 40 | 30 from `mapmake6.js <eval>/maps/dev 30 1104` + 10 fixed ladder-pool maps: 00crater, 00gem-fields, 00quarry, 00vault, 01gold-rush, 01hooks, 02crossing, 02tangle, 03reef, 03twisty | level 2 screen |
| `pool` | 86 | worktree `maps/ladder-pool` (competition pool) | baseline, level 3 holdout |
| `fresh51104` | 100 | `mapmake6.js <eval>/maps/fresh51104 100 51104` | level 3 holdout only, never used for tuning or debugging |
| `official70` | 70 | Agent 2 `v4/maps` @ 56b60b96 | spare / fuel profiling |

The 10 fixed dev maps and the 16 conformance maps are also in `pool`. Tuning on them is a known contamination of the
pool part of the holdout, so `fresh51104` is the unseen part of level 3 and is reported separately.

## Level 1: conformance (per switch, before any screen)

`jdrun.py run --name conf-<switch>-NN --cand <frozen> --base v92 --opps v92 --maps conf --jobs 14` (16 maps x 2 sides).

Pass requires all of:
- 0 bot faults (`botFaults`) and 0 missing/failed games.
- Fuel-outs (engine `fuelExhausted` events, cross-checked with the replay `team-?.fuel` trace) not above v92 on the
  same cells.
- The mechanism's trigger counter > 0 (logged by the switch). A mechanism that never triggers has no evidence.
- Default build (all JD_* = 0) still hashes to `5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47`.

## Level 2: screen

Opponents: v92, x3inv, x3ctr, p65pack, public-khiri. Maps: `dev`, both sides (5 x 40 x 2 = 400 cells per arm).
Select on paired score delta (win 1, draw 0.5, loss 0; reported in points = 100 x score) with the map-clustered
bootstrap 95% CI (2000 resamples, seed 1104), plus banked gems and deaths. Stop a mechanism after two sound revisions
without a credible gain and move to the next one.

## Level 3: frozen confirmation (at most three finalists)

Opponents: v92, b5_c3, v61_c3, public-decrest, public-wardens, x3mf2. Maps: `pool` (86) + `fresh51104` (100), both
sides: 6 x 186 x 2 = 2,232 matched cells per arm. Report exact played/missing/failed counts, per-opponent and
per-map-category strata, draws, and the map-clustered CI. A clean rebuild of each finalist must reproduce its hash.

## Promotion rule (mission sec.8)

A candidate is promoted only with all of:
1. Zero new faults or illegal actions versus v92 on the same cells.
2. Fuel-outs not above v92 on the same cells, and no new suspension failure mode.
3. Paired delta > 0 on the level 3 holdout, with the CI reported. If the aggregate is positive but `fresh51104` alone
   is inconclusive, the candidate is labelled experimental and v92 stays recommended.
4. No opponent stratum or map category with a paired delta below -10 points unless the cause is explained.

Ladder trials additionally follow the #5 LOCK / Claude ACK / UNLOCK protocol and the promotion policy in Claude's issue #5 message #5
(pinned paired duel, >= +6 net wins over a fresh v92 rerun, repeated on a second plan seed).

Outcome classes (AGENTS.md): Accepted / Retry required / Conditionally useful / Parked / Rejected.
