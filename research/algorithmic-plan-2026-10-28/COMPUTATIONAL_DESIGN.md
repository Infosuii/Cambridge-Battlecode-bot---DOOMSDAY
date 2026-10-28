# Computational design: fuel, memory, complexity and efficiency

E-numbers refer to FINAL_DEEP_ANALYSIS.md.

## 1. Facts

- **Fuel.** 100k per turn for C++. 10× on the first draft turn, 2× on the first play turn. Unused fuel does not
  carry over.
- **Running out suspends the bot and resumes it next turn.** A fuel-out therefore costs at least a turn of actions
  for that champion and can leave half-applied plans (GameRules "Fuel").
- **v76 (engine trace, E1):** mean 40–44k, p50 ≈41k, p90 ≈67k, p99 ≈82k, fuel-outs 0.49/game.
- **v76 profile (E2, instrumented, shares only):**

  | Section | Share |
  |---|---|
  | farm | 45% (score_groups 32%) |
  | world update | 27% (hot zones 17%) |
  | handle_enemies | 7% |
  | tactical_decide | 3% |
  | campnet | 1.3% |
- **Lethal examples:**
  - APEX_TSEARCH: 16 fuel-outs/game, −366 (E27)
  - v81 without a guard: 35.9 fuel-outs/game
  - logging that read garbage fields: 90.5/game
- **Shared memory** is 8 bytes and fully allocated (E26). **Draft memory** is 1024 bytes, ~8 used by the brain header.

## 2. Budget plan per turn (OCC at full stage)

| Component | v76 now (≈) | OCC target typical | OCC worst | Notes |
|---|---|---|---|---|
| World update (v76) | 11k | 10k | 25k | Optional: hot-zone recompute only on enemy-set change (−3..−5k) |
| Ledger + EnemyBelief | — | 1.5k | 4k | O(G) timers; visible-camp updates |
| Knob layer (v76) | <1k | <1k | <1k | unchanged |
| Combat: v76 handle_enemies | 3k (7%) | replaced | — | still compiled in as fallback |
| EE (contact turns only, ~15–25% of turns) | — | 8k | 12k | ≤12 simulations × ≤1.3k ops |
| TEP check / replan | 13k (score_groups) | 1k / 6k | 15k | replan every 8 rounds or on events; skipped in LEAN tier |
| Executors (move, cast, capture, shop) | 8k | 8k | 20k | v76 |
| Beacon / claims | <0.5k | <0.5k | <0.5k | |
| **Total** | **≈41k mean** | **≤48k mean** | **≤88k p99** | |

## 3. Fuel governor (M8)

Tiers are chosen at turn start from `bc::fuel_remaining()`. On normal turns that is 100k. On a resumed turn after a
fuel-out it is lower; v76's `kDetSafety` logic already handles resumption.

| Tier | Condition | Allowed |
|---|---|---|
| FULL | remaining ≥ 60k at module entry | everything |
| LEAN | 25k ≤ remaining < 60k | EE with the optimistic variant only; TEP contract check only (no replan); no opportunistic actions |
| FALLBACK | remaining < 25k | the v76 paths for combat and farming (cheaper and proven); no new module may run |

Every module checks `gov.allow(est)` with its worst-case estimate before starting, and again inside any loop that
can exceed 5k. Estimates are calibrated from APEX_PROFILE-style counters in trace builds. Hard reserve: 12k left at
the end of any OCC module.

## 4. Complexity per module

| Module | Complexity | Parameters | Worst ops |
|---|---|---|---|
| Ledger | O(G + V_camps + E) | G ≤ 112 groups | ~2k |
| ObjModel single rates | O(F·G'), with G' ≤ 25 after distance or value pruning | F ≤ 5 | ~10k |
| TEP crew assembly | O(M·F²), M = 8 | | ~1k |
| TEP follow-up | O(M·G') | | ~4k |
| EE simulation | O(S·V·H·n) | S ≤ 6 stances, V = 2, H = 4, n ≤ 11 | ~16k |
| EE escape model | O(path length ≤ 12 · E ≤ 5) | | ~0.5k |
| Draft optimiser | O(C(12,k)·features) | ≤792 lineups | ~250k (draft turn 1) |
| Opening schedule | ~200 rollouts × 120 rounds × F | | ~600k (draft turn 1) |

Fuel per wasm op is near 1 for scalar loops in our build, judging from v76's profile ratios. Budgets assume 1:1 with
a 1.5× margin.

## 5. Memory

- **Per champion (wasm linear memory).**
  - GroupBelief 112 × ~16 B ≈ 2 KB
  - EnemyBelief 5 × 32 B
  - Assignment, stance memory, caches: < 8 KB
  - Distance fields: v76's existing slots, unchanged
- **Shared.** 64 bits: claims 6 × 7 bits plus a typed beacon of 2 + 20 bits (COMBAT_AND_COORDINATION_DESIGN §C.8.1).
  No growth possible, so all new coordination is multiplexed.
- **Draft memory.** Brain header (8 B), opening schedule (≤32 B), map summary (≤32 B). Under 7% of 1024 bytes.

## 6. Efficiency opportunities (optional; only if the budget tightens)

1. **World hot-zone recompute (17% of fuel).** Recompute only when the visible enemy set or awake camps change.
2. **TEP pruning.** Reuse v76's branch-and-bound over distance-ordered groups.
3. **EE.** Skip the pessimistic variant when no hidden phantoms and no unknown cooldowns exist.
4. **Remove dead flagged code from the hot path.** No fuel effect, since it is compiled out; readability only.

## 7. Safe fallbacks (must exist before any live test)

| Situation | Fallback |
|---|---|
| Governor tier FALLBACK | v76 `handle_enemies` and `farm()` |
| ObjModel infeasible for all objectives | v76 `score_groups` |
| EE exception or NaN | v76 verdict path for this turn |
| Ledger inconsistency (e.g. claim names a group out of range) | ignore that claim (v76 does the same) |
| Draft optimiser exception | V70 table → ML draft → presets |
| Opening schedule mismatch | drop the schedule for the rest of the game |

## 8. Measurement protocol

Every build that changes runtime:
- **Fuel.** Run the engine fuel trace (`team-X.fuel`, parsed by `research/strategic-audit-2026-10-28/scripts/
  fuel.py`) on the idle bench and one contested opponent. Report mean, p50, p90, p99 and fuel-outs per game.
- **Gate.** p99 ≤ 88k and fuel-outs ≤ 0.6/game against both.
- **Instrumented profiling.** Builds with `APEX_PROFILE`-style counters alter behaviour (26.7 fuel-outs/game, E2).
  Use them for shares only, never for strength or fuel-out claims.
