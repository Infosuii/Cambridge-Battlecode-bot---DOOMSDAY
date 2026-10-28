# Implementation plan (DOOMSDAY Zero, clean slate)

**Not authorised yet.** Implementation starts on user approval. DZ contains **no code from previous bots**.

**Allowed inputs:**
- the official SDK, CLI and CMake
- repository research findings and data
- repository *evaluation* tools: `research/v81/run_experiment.py`, `paired_strict.py`, `tools/v67/c_paired.py`,
  replay decoders, `scripts/fuel.py`, and the deep-analysis puppet harness

These tools operate on any bot directory and are not part of the bot.

## 1. Project structure

```
bots/dz/src/               main.cpp kernel.* config.h static_world.* observation.* memory.* protocol.* crew.* race.*
                           objmodel.* economy.* gear.* threat.* engage.* actions.* safemode.* draft.* trace.h
bots/dz/CMakeLists.txt     official template (GLOB_RECURSE src/*.cpp, -O3), same as the platform build
tests/dz/host/             native unit tests of pure cores (objmodel, engage evaluate, protocol codec, draft utility, gear ΔGE)
tests/dz/scenarios/        puppet warm-state cases (deep-analysis tests/loss_cases format) + DZ-specific scenario specs
artifacts/tmp/dz-conformance/   diagnostic bots for ENGINE_CONFORMANCE_SUITE (never candidates)
artifacts/tmp/dz-styles/        scripted style opponents (rusher, turtle/perma-recall, cluster farmer), evaluation-only
research/dz/               CONFORMANCE.md RESULTS.md SEED_LEDGER.md HOLDOUT.md CALIBRATION.md DECISIONS.md
```

## 2. Build order (each step leaves a playable bot)

| Step | Deliverable | Depends on | Effort | Exit test |
|---|---|---|---|---|
| Z0 | Conformance diagnostics CT-1..27 (parallel); `research/dz/CONFORMANCE.md` | — | 1 d | Every CT has an observed value or a documented inability |
| Z1 | Kernel: main loop, TurnContext, Governor, Actuator with stale-turn guard, exception boundary, `config.h` | — | 0.5 d | Host tests; a game runs to completion with no-op turns; 0 faults |
| Z2 | StaticWorld and Observation (boot, lazy fields, masks, designs, groups, fingerprint) | Z1 | 1 d | Boot within the 200k budget on a 100×100 map; field correctness check vs `move_towards` on 50 random pairs |
| Z3 | SafeMode: flee, nearest-group clear and capture, bank at 30, fixed build | Z2 | 0.5 d | **Walking skeleton:** 140 idle games and 140 vs v65, 0 faults, fuel gate; income measured |
| Z4 | Draft engine (prior lineup, utility, always-pick), draft memory writer | Z2 | 0.5 d | Legal picks on all 70 maps; ≤1M fuel |
| Z5 | Memory and protocol (codec host-tested, ledger, beliefs) | Z2 | 1 d | Codec round-trip; ledger matches the replay truth on 5 games (offline compare) |
| Z6 | ObjModel plus offline validation (V-M1) using SA-IDLE-v76 replays (engine-measured clears, independent of v76 code) | Z2 | 1 d (parallel) | V-M1 thresholds |
| Z7 | Economy auction (crews, clusters, contracts, bank rule) | Z5, Z6 | 1.5 d | V-E1 idle: R250 gems ≥ 0.9× v76; no stuck jobs (contract releases < 2 per champion per 500 rounds) |
| Z8 | Action scorer: travel, clear (tank rule), capture, bank, shop, ward; spell policy | Z3 | 1.5 d | Scenario checks; idle parity G-P1 (below) |
| Z9 | Gear planner | Z7 | 0.5 d | V-E4 |
| Z10 | Threat and EE (offline calibration V-M2 in parallel from Day 3) | Z8, Z6 | 1.5 d | V-M2; scenario suite; contested league gate |
| Z11 | Crew protocol and race controller | Z10, Z5 | 1 d | V-C3; split-engagement share |
| Z12 | Opening planner (optional) | Z7, Z4 | 0.5 d | V-E3 |
| Z13 | Style opponents (evaluation tools) | Z3 | 1 d (parallel) | Legal games, 0 faults |
| Z14 | League tuning (scalars, per-map draft rows) and held-out validation | all | 1.5 d | G5/G6 |
| Z15 | Hardening: fuel, faults, conformance re-run, release dossier | all | 1 d | G0–G7 |

**Shortest path to a functional algorithmic prototype:** Z1 → Z2 → Z3 → Z5 → Z6 → Z7 → Z8 (about Day 5).

**Deferrable without undermining the core:** Z11 crew stance, Z12 opening, style adaptation, gear refinements.

## 3. Hook-free design

DZ has no legacy hooks. All decisions flow through the turn lifecycle (MASTER §4), and modules are switched by `DZ_*`
flags for A/B tests within DZ.

## 4. Testing hooks

- Host unit tests for the pure cores.
- `DZ_TRACE` decision logs (one line per decision: stance values, assignment and rate, fuel per module).
- Scenario specs (synthetic positions run with diagnostic setups).
- Puppet warm cases from the deep-analysis harness:
  - the harness replays *our* recorded ladder states, so it can be reused for DZ only for scenarios where DZ is
    dropped into the same state
  - this needs a "warm takeover" build: inject DZ at round R with v75's reproduced prefix
  - the deep-analysis tooling supports diagnostic takeovers; treat it as optional and expensive

## 5. Offline precomputation

- **ObjModel κ:** from replay clear times.
- **λ_gold coefficient:** regression on saved timelines.
- **EE scalars:** from contact datasets (local replays plus the examined ladder set).
- **Draft weights:** LOMO on DZ's own league runs (Day 10).
- **Per-map rows:** the league protocol (v70/v71 method, applied to DZ).

## 6. Fallback and release

- DZ's internal fallback is SafeMode.
- The **release fallback is the user's currently live bot**. Nothing in this plan changes the live version.
  Submission and ladder duels are separate, user-authorised actions.
