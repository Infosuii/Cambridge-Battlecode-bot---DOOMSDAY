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

## Known gap: recorder fuel is not exactly zero

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
