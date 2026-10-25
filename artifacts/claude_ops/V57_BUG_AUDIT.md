# v57 basic bug audit

Claude Code, 2026-10-25, on the submitted v57 (platform version 56, source `dff699d5…`). The goal was to rule out
basic defects before the v58 work. Data: 176 local v57 games (120 on the 15 fresh pool maps against v55, 56
development games against v58) and the 80 v55-vs-Claudus ladder replays, which play v57's lineage.

## Checked and clean

| Check | How | Result |
|---|---|---|
| Compiler | every `src/*.cpp` with wasi clang `-Wall -Wextra -Wshadow -Wuninitialized -Wconditional-uninitialized -Wunreachable-code` | 0 errors, no uninitialised use. 4 shadows, all intended locals (`slot`, `mode`, `focus`); constant-logic and unreachable warnings are compile-time flags |
| Spell kits | `A2_MICLOG` debug build prints each champion's parsed kit (Ryth, Vesper, Vendetta, Marcella, Heart) | kinds, ranges, radius and target masks match GameRules; Ryth's area stun is `aoe_damage` on ground and is cast at a tile, correctly |
| Ranged walk-then-cast | `fight_camps` returns before `cast_on_camp` after a ranged champion walks | only Cassi's stun is a walk-compatible spell on a ranged champion; negligible |
| Item labels and shopping | item counts dumped from replay state against the SDK `item_type` order | ledger indexes correct (22/23 = Treasure shard/emblem); purchases follow `build_for`; median carried gold 8-10 at R250/500/750 (no hoarding) |
| Stuck at spawn | rounds alive on own spawn at full health with no move | 0.8% of alive rounds; longest run median 1 round |
| Fuel | fuel-out steps (`tools/replay/fuel_outs.mjs`) | about 1 per game |
| Respawn blocking (any occupied spawn tile delays the group) | `tools/replay/respawn_delay.mjs`: delay past each group's shortest observed timer, by who stood on the tiles | 15 extra group-rounds per game for v57 (Claudus 7, v55 against them 21) over about 60 respawns per game: not a defect; the wait code already steps off the tiles |
| Faults | bench summaries | 0 native faults in every run |

## Not bugs, but measurable gaps (`tools/replay/sanity_audit.mjs`)

| Per game or per 100 alive champion-rounds | v57 local | v55 vs Claudus | Claudus |
|---|---:|---:|---:|
| basic attacks per 100 alive rounds | 21.1 | 20.4 | **26.6** |
| casts per 100: Ryth / Tavi / Marcella | 4.5 / 6.4 / 6.8 | 5.5 / 6.9 / 6.1 | **8.5 / 9.8 / 8.2** |
| idle alive turns (no move, attack, cast or shop) | 21.5% | 23.6% | 18.7% |
| wards per game | 69 | 54 | **115** |
| tribute starts per game | 27 | 14 | 27 |
| deaths per game | 16.1 | 15.5 | **5.6** |
| gems lost per death | 13.3 | 6.1 | 8.5 |
| deaths carrying 40+ gems, per game | 1.22 | 0.74 | **0.30** |

Each local v57 game has v57 against our own lineage, so its rows compare with the v55 row, not with Claudus's
opponents. The two that matter: we act less per alive round (fewer attacks, fewer casts on champions with
excludes-walk spells, more idle turns), and we die far more, with bigger bags.

## Verdict

No basic defect found. v57's losses to the top teams are strategic (economy loop, survival, vision), not a
broken mechanic. New tools: `tools/replay/sanity_audit.mjs`, `tools/replay/respawn_delay.mjs`.
