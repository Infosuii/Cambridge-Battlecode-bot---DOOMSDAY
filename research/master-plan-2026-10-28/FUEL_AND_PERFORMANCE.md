# Fuel and performance design

## 1. Facts

- **Budget.** 100k fuel per turn. 10× (1M) on the first draft turn and 2× on the first play turn. Unused fuel is
  lost.
- **Running out suspends the bot**, which resumes next turn. This is lethal in fights: tsearch had 16 fuel-outs per
  game and lost 366 gems/game.
- **v76 (engine trace):** mean 40–44k, p50 ≈41k, p90 ≈67k, p99 ≈82k, 0.49 fuel-outs per game.
- **v76 profile shares:**

  | Section | Share |
  |---|---|
  | farm | 45% (score_groups 32%) |
  | world update | 27% (hot zones 17%) |
  | handle_enemies | 7% |
  | tactical_decide | 3% |
  | campnet | 1.3% |
- **Computation is not shared across champions.** Each champion runs its own instance, and only the 8-byte word is
  shared.

## 2. Per-subsystem targets

Approximate figures in thousands of fuel.

| Subsystem | v76 now | OCC typical | OCC worst | Gate |
|---|---|---|---|---|
| World update (v76, with optional hot-zone caching) | 11 | 8–10 | 25 | — |
| Ledger + EnemyBelief + race | — | 1.5 | 4 | p99 ≤ 4k |
| TEP contract check | — | 0.5 | 1 | — |
| TEP replan (every 8 rounds or on events; FULL tier only) | 13 (score_groups, every turn) | 6 | 15 | p99 ≤ 15k |
| EE (threat turns, ~15–25%) | 3 (+ tdecide 1.2) | 9 | 12 | p99 ≤ 12k |
| Micro scorer (optional) | — | 5 | 8 | — |
| Gear planner (spawn or dead turns) | <1 | 1 | 2 | — |
| Executors (v76) | ~8 | ~8 | 20 | — |
| Protocol | <0.5 | <0.5 | <0.5 | — |
| **Turn total** | **≈41 mean / 82 p99** | **≤48 mean** | **≤88 p99** | fuel-outs ≤ 0.6/game |

**Draft.**
- First draft turn: the optimiser takes ≤250k and the opening schedule ≤600k, within the 1M limit.
- Later draft turns: ≤50k.

## 3. Algorithmic complexity

| Algorithm | Complexity | Bound |
|---|---|---|
| Ledger sync | O(G + visible camps + E) | ~2k ops |
| ObjModel single rates | O(F·G′), G′ ≤ 25 after pruning | 125 × ~60 |
| Crew assembly | O(M·F²), M = 8 | ~200 |
| Follow-up | O(M·G′) | 200 × ~30 |
| EE | O(S·V·H·n), S ≤ 7, V = 2, H = 4, n ≤ 11 | ~9k |
| Escape model | O(path ≤ 12 · E) | ~0.5k |
| Local danger window | 17×17 × E | ~1.5k |
| Micro scorer | ≤60 candidates × E | ~5k |
| Draft optimiser | ≤792 lineups × ~300 ops | 250k |

## 4. Governor policy

| Tier | Entry condition (remaining at module entry) | Allowed |
|---|---|---|
| FULL | ≥ 60k | everything |
| LEAN | 25k ≤ remaining < 60k | EE: optimistic variant and ≤4 stances; TEP: contract check only; no opportunistic actions |
| FALLBACK | < 25k | v76 `handle_enemies` / `farm()`; no OCC module |

**Rules:**
- Each module calls `gov.allow(est_worst)` before running, and again inside any loop that can exceed 5k.
- **Hard reserve:** 12k must remain after any OCC module.
- **Resumed turns** (after a suspension) start with less than 100k, so the tier adjusts automatically.
- **Unused fuel is not a target.** Spend it only when the expected decision gain is positive: FULL-tier replans,
  pessimistic variants.

## 5. Caching and incremental computation

- **Distance fields.** Per group, plus spawn and altars. v76 builds them incrementally under a budget. Keep this, and
  build the fields of the top-25 static-value groups first.
- **Single-champion rates** ρ({c},g) are cached per champion and invalidated by:
  - a position change of more than 2 tiles
  - a group state change
  - an item change
  - every 4 rounds
- **Hot zones.** Recompute only when the hash of visible enemies and awake camps changes. Saves an estimated 3–5k per
  turn (to be measured).
- **EE scene.** Built once per turn and shared by all stance evaluations.
- **Gear planner.** Runs only on spawn or dead turns, or when gold crosses the next item price.

## 6. Memory budget (per champion)

| Item | Size |
|---|---|
| Ledger | ≈2 KB |
| EnemyBelief | 160 B |
| Caches | ≤6 KB |
| Scene | 1 KB |
| v76 fields | Unchanged; the largest consumer |
| Shared word | 64 bits, fully allocated (DATA §4) |
| Draft memory | ≤72 of 1024 B |

## 7. Instrumentation (trace builds only)

- **Per module.** Fuel at entry and exit, and counters for replans, EE evaluations, tier distribution and errors.
- **Fuel traces.** Collect `team-X.fuel` traces from every run with `research/strategic-audit-2026-10-28/scripts/fuel.py`.
  This is the authoritative fuel measurement.
- **Gate on every build that changes runtime:** p99 ≤ 88k and fuel-outs ≤ 0.6/game, measured on the idle bench and
  against two contested opponents.

## 8. Degradation behaviour (stress cases)

| Case | Behaviour |
|---|---|
| 100×100 map, 112 groups, early turns with few fields | ObjModel uses the 1.3·cheb estimate with a low-confidence flag, so no long commitments. Fields are built under budget |
| Large brawls (5v5 plus camps) | EE caps the scene at 11 units by distance, and uses the LEAN tier if needed |
| A fuel-out happened | The next turn starts in LEAN or FALLBACK. The assignment is kept; no replan |
| Repeated module exceptions | The module disables itself after 3 errors |
