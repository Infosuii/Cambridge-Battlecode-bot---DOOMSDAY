# Fuel-out reduction: results (2026-11-04, engine 2.0.0 / cambc 4.0.0, pre-patch-4)

All games release builds, real 100k fuel, paired on identical cells. Training maps = all 50 training-split maps x
both sides; dev = 15 development maps x both sides. Builds from bots/claude-native-1104 (commits 8595a231, c98bdabe).

## Where fuel-outs come from (CLFP profiler, native, 16 training games)

| stage | share of overruns |
|---|---|
| nn_turn_end block refresh (optional end-of-turn work) | 69% |
| v92 work after the native camp scoring | 18% |
| inside nn_lazy_score (scoring) | 6% |

Causes: the refresh drops overrun samples, so its cost estimates never learn the expensive cases; the estimates decay
below real cost; the reserve is only 1k. Unused fuel averages ~30k per turn, and ~60% of turns end with > 20k left.

## CLFS (fuel-safe native base; opt-in `#define CLFS 1`; default build unchanged, f0ad2c27)

Learn from overruns, no decay below the last measured cost, est/4 + 3k margins, nn_need decay 1/64, scoring gate
+ est/8, warm-up/rebuild margins. With CLFS on, route search starts at 35k (A2_ROUTE_FUEL; 55k otherwise).

| matchup (games) | build | wins | own fuel-outs |
|---|---|---|---|
| training vs v92 (100) | native | 47 | 2057 |
| | CLFS (route 55k) | 51 | 807 |
| | CLFS + route 35k | 58 | 953 |
| training vs v92 (100) | exact v107 | 45 | 2204 |
| | v107 + CLFS (route 55k) | 42 | 844 |
| training vs native Agent 2 (100) | CLFS (route 55k) | 56 | 832 |
| | CLFS + route 35k | 55 | 995 |
| dev vs v92 (30) | native | 19 | 461 |
| | CLFS (route 55k) | 15 | 101 |
| | CLFS + route 35k | 12 | 132 |
| dev vs native Agent 2 (30) | CLFS + route 35k | 18 | 124 |

Paired deltas (family-clustered 95% CI):
- CLFS - native vs v92, training: +0.04 [-0.06, +0.16]
- v107+CLFS - v107: -0.03 [-0.16, +0.12]
- route35 - CLFS, training vs v92: +0.07 [-0.04, +0.18]
- route35 - CLFS, training vs native: -0.01 [-0.14, +0.11]
- CLFS - native, dev vs v92: -0.13 [-0.33, +0.03]

## Conclusions

- CLFS cuts own fuel-outs by ~60% on both the native base and exact v107, with no measurable strength cost. Against
  unmodified native Agent 2 it wins 56/100. Recommended as the runtime base.
- Route search at 35k is not established: +0.07 vs v92 on training maps, -0.01 vs native, and worse on the 30 dev
  cells vs v92. Do not adopt it without more evidence. The A2_ROUTE_FUEL gate is gated on CLFS in c98bdabe; revert
  that line if CLFS is adopted alone.
- A flat larger reserve (JOHNDOE's reserve5k) cuts fuel-outs similarly but lost strength vs native; CLFS keeps
  admission measured per stage instead.
- Remaining fuel-outs (~8/game) are mostly v92's own post-scoring work and scoring-stage overruns. The patch-4 engine
  (releasing 2026-11-05) needs a rebaseline before any of this is applied to the tournament build.

Reports: runs/rl_env_1104/eval/{clfs3-train-01, clfs3r35-train-01, v107clfs-train-01, clfsr-train-vsnative-01,
clfs3-01, clfsr-dev-01}; profiler tools/rl_env_1104/strategy/fuel_profile.py.

## Engine 3.0.0 (cambc 5.0.0, build 96ce858f) and v108 (2026-11-05)

The ladder moved to engine 3.0.0 (5 champions per team); everything above is engine 2.0.0. Re-measured on engine 3,
50 training maps x A/B, release:

| matchup | v107 | v107 + CLFS | paired CLFS - v107 |
|---|---|---|---|
| vs v92 | 50/100, 2319 fuel-outs | 46/100, 781 | -0.04 [-0.16, +0.09] |
| vs native Agent 2 | 48/100, 2174 | 48/100, 907 | 0.00 [-0.16, +0.15] |

Live: own fuel-rollovers 470 vs opponents' 147 in the user's 20 unique v107 games (JOHNDOE #142). Shipped as **v108** =
exact v107 source (d08636c5) + the CLFS nnrec.cpp/bot.cpp/main.cpp/clfp.h diff of 8595a231 + `#define CLFS 1`
(route search unchanged at 55k). Submitted 2026-11-05 via `cambc submit`; the team follows the newest ready version,
so v108 went live on build.

Item-build tests on engine 3 (vs v92, paired to v107): Bruiser-only after Prospector 24/100; Prospector, Jungle,
Durability then Bruiser 36/100; V58 emblems then Bruiser instead of Collectors + Greed 50/100 (identical). Not adopted.
