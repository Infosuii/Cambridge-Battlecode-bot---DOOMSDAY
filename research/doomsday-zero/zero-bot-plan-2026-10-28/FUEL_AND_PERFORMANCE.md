# Fuel and performance (DOOMSDAY Zero)

## 1. Facts

- **Budgets** (verified from fuel traces):

  | Turn | Budget |
  |---|---|
  | First draft turn | 10M |
  | Later draft turns | 100k |
  | First play turn | 200k |
  | Every later turn | 100k |

- **Running out suspends the bot.** It resumes mid-code next turn. The kernel's stale-turn guard makes this safe, but
  every suspension still loses most of a turn.
- **Metering.** Wasmtime fuel meters guest wasm operators. **Host-side work is free unless the engine charges it.**
  cambc can charge through `fuel_adjust`. Per-call costs are unknown until CT-1, so the plan budgets for two
  scenarios.
- **Previous-bot reference** (a different design): about 41k mean and 82k p99 per turn, dominated by camp scoring
  (32%) and world update (27%). DZ is designed to be lighter.

## 2. Budget plan per turn (champion instance)

Approximate figures in thousands of fuel.

| Subsystem | Typical (A: host cheap) | Typical (B: host expensive) | Worst | Notes |
|---|---|---|---|---|
| Kernel (begin turn, governor, guard) | 0.3 | 0.5 | 1 | |
| Observation (single reads) | 3 | 6 | 10 | Read each quantity once |
| Memory update (ledger, beliefs, protocol decode) | 1.5 | 2 | 4 | O(G + visible) |
| Lazy field build (scheduled) | 1–3 | 5–15 | Governor cap | Builds only with spare budget; nearest 25 groups by about R30 |
| Race | 0.2 | 0.2 | 0.5 | |
| Economy (contract check / replan) | 0.5 / 6 | 0.5 / 8 | 15 | Replan every 8 rounds or on events, FULL tier only |
| Threat + EE (threat turns, ~20%) | 9 | 10 | 12 | ≤7 stances × 2 variants × 4 rounds × ≤11 units |
| Action scorer | 3 | 5 | 8 | ≤60 candidates |
| Gear (spawn or dead turns) | 1 | 1 | 2 | |
| Protocol publish | 0.2 | 0.3 | 0.5 | |
| **Target total** | **≤25 mean** | **≤40 mean** | **≤80 p99** | Fuel-outs ≤ 0.3/game |

- **Boot** (first play turn, 200k):
  - designs, groups and masks: ≤20k
  - `F_spawn` and altar fields: ≤30k under scenario B
  - the first 5 group fields
  - the rest is scheduled
- **Draft:**
  - optimiser ≤1M
  - opening planner ≤5M (rollouts)
  - always pick within the first 1M of the 10M

## 3. Governor

| Tier | Remaining at module entry | Allowed |
|---|---|---|
| FULL | ≥ 60k | everything |
| LEAN | 25–60k | EE optimistic variant with ≤4 stances; economy contract check only; no field building |
| FALLBACK | < 25k | SafeMode only |

**Rules:**
- **Pre-flight.** Each module calls `gov.allow(worst_case_estimate)` before running, and again inside any loop that
  may exceed 5k.
- **Hard reserve.** 12k must remain after any module.
- **Resumed turns.** A turn resumed after a suspension starts with less fuel, so its tier adjusts automatically.
- **Spend only for gain.** Unused fuel is not a target.

## 4. Complexity bounds

| Algorithm | Bound |
|---|---|
| Ledger | O(G + visible camps + E) |
| Single rates | O(F·G′), G′ ≤ 25 after pruning |
| Crew growth | O(M·F²) |
| EE | O(S·V·H·n) |
| Escape model | O(path·E) |
| Action scorer | O(candidates·E) |
| Draft | ≤792 lineups × O(features) |
| Opening | ≤200 rollouts × 120 rounds × F |

## 5. Caching

- **Group fields** are built once (the terrain is static) and reused all game. Memory is W·H·2 bytes each, at most
  2.2 MB for 112 groups.
- **Single rates** are cached per champion, and invalidated by moving more than 2 tiles, a group state change, an
  item change, or after 4 rounds.
- **The scene** is built once per turn.
- **Scratch bitboards** are allocated once and reused with the `_into` APIs; avoid constructing temporaries.

## 6. Memory

| Item | Size |
|---|---|
| Fields | ≤2.3 MB |
| Ledger | ~2 KB |
| Beliefs | ~0.5 KB |
| Scene | 1 KB |
| Caches | ≤16 KB |
| Shared word | 64 bits (fully allocated) |
| Draft memory | ≤108 of 1024 bytes |

## 7. Instrumentation (DZ_TRACE builds only; never used for strength claims)

- **Per module:** fuel at entry and exit, and counts of replans, EE evaluations, tier usage, errors and stale-turn
  aborts.
- **Authoritative fuel measurement** for release builds: the engine fuel traces (`team-X.fuel` in replay bundles),
  parsed with `research/strategic-audit-2026-10-28/scripts/fuel.py`. This works on DZ unchanged; it reads engine
  output only.
- **Gate on every build that changes runtime:**
  - p99 ≤ 85k
  - fuel-outs ≤ 0.3/game
  - zero bot faults
  - measured on the idle bench and against two contested opponents
