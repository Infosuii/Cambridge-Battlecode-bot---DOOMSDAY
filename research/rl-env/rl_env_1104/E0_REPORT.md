# E0 conformance: cl1 recorder and collector (real engine)

Run: `python tools/rl_env_1104/e0_tests.py -v` (stdlib only, ~30 s on the i5-1135G7). Maps `00corners`, `00crater`
(override with `E0_MAPS`). Recorder = `bots/claude-rlenv-1104` with `CLRL_REC 1`, non-release build; opponent v92.

| # | test | result |
|---|---|---|
| 1 | Recorder source with `CLRL_REC 0`, release build, has v92's SHA-256 (`5704d7ba41ac…`) | **pass** |
| 2 | Recorder (debug) vs v92 gives the same outcome, round count and both scores as release v92 vs v92 | **pass** on both maps (e.g. 574 vs 1051, 1,095 rounds) |
| 3 | The same game collected twice gives identical CLR1 rows | **pass** (4,755 rows) |
| 4 | Charged fuel per turn of the recorder's team vs a v92 debug build | **pass at ≥95%**: 96.7% (`00corners`), 99.7% (`00crater`) of turns identical. See known gap |
| 5 | Visibility: a visible enemy has age 0; a hidden enemy has age > 0 and its last-known position never moves until seen again | **pass** |
| 6 | Lifecycle: one terminal row per body, none at deaths; resets between bodies and bodies + deaths; validator OK | **pass** |

## Update (4 Nov ~15:00Z): debug twin results and why exact parity isn't reachable

The collector now runs a **v92 debug twin** with each game (same map, side, opponent and build mode) and writes
row-aligned `fuel_delta` / `fuel_diverged` columns (round-level: the fuel trace has no body ids) plus episode fields
`twin_rounds_diverged`, `twin_first_diverged_round` and `twin_outcome_equal`. Map-diverse batch `teach-div-01`
(6 maps × 2 sides vs v92):

| map | rounds diverged | outcome equal to twin |
|---|---|---|
| 02the-pack | 5–7% | yes |
| 00corners | 13–14% | yes |
| 01islands | 10–25% | yes |
| 02tangle | 21–29% | yes |
| 03the-front | 17–37% | yes |
| **00ambush (100×100)** | **90–93%** | **no** (both sides) |

Tried and measured on `00ambush`, recorder A vs v92, against the v92 debug twin:

| recorder placement | turns identical to twin | outcome |
|---|---|---|
| hook after `w.update` inside `play_turn` (committed design) | 3,412 / 7,842 | **changed** |
| no capture, end-of-turn call in `main.cpp` only | 7,715 / 7,724 | same |
| SDK-only capture in `main.cpp` before `play_turn`, in-block refund (reverted) | 191 / 7,724 (corners 914 / 6,588) | changed |

Causes, measured:
1. **Codegen:** a call inside `play_turn` changes how v92's own functions compile (inlining), shifting v92's instruction
   counts by a few fuel per turn. No refund can match that.
2. **SDK caches:** capture before v92 runs calls SDK queries that cache results (`map::altars`, `spawn_region`,
   `camp_groups`, `self`). v92's later calls then cost less (negative deltas), which shifts its fuel.
3. **Static state:** a global with a constructor is charged at VM start (draft turn +140, first turn +~550). Fixed by
   lazy allocation in the reverted attempt.

v92 runs at its fuel thresholds on big maps, so any shift cascades. **Conclusion:** a decision-time observation can't
be recorded with zero side effects here. Data use should therefore follow the twin flags: rows before
`twin_first_diverged_round` are pure v92 behaviour, later rows are the recorder build's own behaviour. Labels and
features are still consistent with each other, since that build is the policy that acted. On-policy collection is the
same: the logged policy *is* the actor build, and release gets its own parity gate.

## Earlier note: recorder fuel is not exactly zero

`debug_block` refunds its own guard overhead (2 fuel). The rest of each recorder block's call/guard cost was measured at
12 fuel per block (24 per alive turn) and is refunded with `CLRL_REFUND 12`. After the refund most turns match a v92
debug build exactly, but a residual of 3-7 fuel remains on some turns. v92 has fuel-threshold branches (field builds,
searches), so a residual can still flip one branch occasionally. Once flipped, a few following turns differ too (on
`00corners`, one cascade with a 29k delta), although the game outcome was unchanged on both maps.

Before relying on teacher traces for *timing-sensitive* labels (field availability, search admission), either:
1. measure the residual per path and refund it exactly; or
2. record a per-row flag `fuel_diverged` by running the v92 debug twin in the same batch and diffing traces.

Option 2 is cheap here (release games ~1 s, debug ~20 s).

## Not covered yet

- **Release vs collection for a learned actor:** the recorder only observes v92, so there's no sampled policy in the
  bot yet. That test comes with the first in-bot actor: debug greedy == release actions and fuel.
- **Primitive action exclusivity** within a turn: the labels exist (`prim` bits); the statistics report is next.
- **Ally rows:** use the body's own view only (`World::allies` = visible allies). Shared-memory claims aren't included.
