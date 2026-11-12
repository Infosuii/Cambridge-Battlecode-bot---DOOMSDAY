# Results and evidence

DOOMSDAY has two kinds of performance record: historical ladder snapshots and frozen local benchmarks. They use
different versions and opponents. The final recommended local bot is **v306AltarPressureReach**.

## Extended frozen comparison

The primary pool contains 240 fresh maps across five terrain/reward families, three draft sizes and variable altar
positions/counts. Each bot faces four references from both sides: **1,920 conditions per bot**.

| Bot | Random wins / 1,920 | Published wins / 420 | Direct wins vs v306 / 240 |
|---|---:|---:|---:|
| **v306AltarPressureReach** | **1,398** | **276** | — |
| v320CampChannelCore | 1,395 | 278 | 120 |
| v348LethalFinishSafety | 1,374 | 270 | 124 |

| Candidate | Paired random-pool gain | 97.5% map-cluster interval | Classification |
|---|---:|---:|---|
| v320 | −0.156 percentage points | [−0.417, +0.104] | Retry required |
| v348 | −1.250 percentage points | [−2.708, +0.208] | Retry required |

The primary intervals account for two candidate comparisons. Neither newer variant demonstrated a gain on the
primary pool, so v306 remained recommended. Direct matches and subgroup splits are secondary/descriptive.
The published-map cohort is a separate validation panel; it is not the official ladder.

**Reliability:** the report records zero native bot faults for these cohorts. Fuel exhaustion remains nonzero:
the v306 baseline has 3,470 exhausted-fuel events across its 1,920 primary games. These are distinct measures.

Sources: [readable report](../research/doomsday-movement-20261110/crew-next/long15-261110355-REPORT.md),
[aggregate measurements](../research/doomsday-movement-20261110/crew-next/long15-261110355-report.json),
[frozen identities](../research/doomsday-movement-20261110/crew-next/long15-261110355-freeze.json),
[report correction record](../research/doomsday-movement-20261110/crew-next/long15-261110355-analysis-correction.json).

## Independent supplied-opponent matchup

A user-supplied bot, identified by ZIP SHA-256
`7d9b610b0fd4e0fc40a6a50734c6a0670508d3b62ac6c2a14b32617c199079e0`, was tested on 100 fresh random maps and
30 published maps, both sides, against each of two frozen builds.

| Bot | Random W–D–L / 200 | Random win rate, 95% map-cluster interval | Published W–D–L / 60 |
|---|---:|---|---:|
| **v306** | **104–0–96** | **52.0%; 44.0–60.5%** | **45–0–15** |
| v348 | 103–0–97 | 51.5%; 43.0–59.5% | 44–0–16 |

The random-map intervals are wide and do not establish a reliable advantage. The 75% published-map score for
v306 should not be substituted for the random-map result.

The major-objective family is a clear investigation target: v306 won only **2 / 40** games in that descriptive
subgroup. The opponent also spent more early gold and collected more late large-camp gems, while suffering more
deaths. Those associations suggest hypotheses; they do not isolate a causal mechanism.

Source: [full matchup report](../research/doomsday-movement-20261110/crew-next/mediumzip-7d9b610b-261111401-REPORT.md),
[measurements](../research/doomsday-movement-20261110/crew-next/mediumzip-7d9b610b-261111401-report.json),
[frozen identities](../research/doomsday-movement-20261110/crew-next/mediumzip-7d9b610b-261111401-freeze.json).

## Historical competition record

- **UK lobby peak: #5**, recorded in the project's competition history.
- **International peak: #41**, rating **2206**, with v112 on 8 November 2026.
- The earlier v106 neural blend recorded **54.6% against v92 over 1,440 games** under its historical evaluation conditions.

See the [dated ladder table](timeline.md) and [neural blend report](../research/neural/nnq4-blend/README.md).
These earlier milestones do not establish a ladder rank for v306 or a final tournament placement.

## What makes a result reproducible

1. Frozen source and binary identities, with the engine/SDK/CLI environment recorded.
2. Shared map, opponent and side conditions across baseline/candidate comparisons.
3. Random-map coverage and a separately reported published-map cohort.
4. Map-clustered uncertainty, keeping paired map sides together.
5. Separate fault and fuel measures, plus recorded failures and report corrections.

The archive preserves source and aggregate evidence. Some raw replays and simulation caches were removed during
cleanup. Exact reruns may require restoring the source capsule, resolving historical paths and using the recorded
toolchain. Synthetic terrain families are a stress panel, not a forecast of finals map frequencies.
