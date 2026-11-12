# Handoff: state at 2026-10-26 20:30 UTC (Claude Code -> next agent)

Read this before `docs/handoff.md` (older background). Evidence is in `research/v59/`.

## Live bot

**Platform version 60 = `bots/v61`, active and pinned.** Team DOOMSDAY: rank 54, rating 1939.
Lineage: v58 (platform 57) -> v59 (58) -> v60 (59) -> v61 (60). The sources of v59-v61 are read-only on
purpose: each equals its submitted bundle in `artifacts/release/v5x/v6x-source.zip`. Copy a bot before
editing; `tools/make_variant.py` does this and makes the copy writable.

| Version | Adds | Switches |
|---|---|---|
| v59 | Bruiser stat stacks replace v58's Greed milestones; retreat when outnumbered by 2+ | `V59_ITEMS 2`, `APEX_OUTNUMBERED 2` |
| v60 | Hold our spawn (full heal every round there; enemies cannot enter) while visible enemies at least match us; camp gold funnels to Vesper | `V60_HOME_GUARD 1`, `UB_GOLD_FUNNEL 1` |
| v61 | Opening pack: 3 champions take the best own-side elk-size group first, until captured or round 90 | `V61_OPEN_PACK 1` |

## Where we stand against the top 12 (ladder duel, identical 24 groups per arm, ranks 1-12)

| Arm | Wins | Mean gem margin |
|---|---:|---:|
| v60 | 15/120 | -465 |
| v61 (live) | 21/120 | -462 |
| v62c (group up: `A2_TEAM 2`, `APEX_COHESION 0.3`) | 15/120 | -494 |

The gap is large. Against the top 12, per game: deaths 14.2 vs 5.0, kills 4.0 vs 11.9, gold 4,156 vs 7,108.
Gold already trails at R100 (295 vs 353) and R500 (1,704 vs 2,520). In contact we lose 36.6 hp per round to
their 17.1. They cast spells on our champions about twice as often at the same total cast rate: we spend
cooldowns on camps, they arrive at fights with spells ready. Their Vesper captures 18 camps per game and earns
2,700 gold; ours earns 870. v61's opening pack lifted our R100-R200 gold and gems by 7-13% against the same teams,
but it did not change the margin.

## The process lesson (most important)

- **The local bench does not predict the ladder.** v58 beat v57 by +153 locally and was no better on the
  ladder (opponent-adjusted residual -0.001 vs v57's +0.047). Every local opponent is our own lineage. Self-play
  is a brawl where both sides die 16 times per game; top teams die 5. Ladder-motivated switches (retreat, burst
  danger, spell hold, gold funnel, team hold, opening pack) were all written from ladder evidence and then
  switched off because they lost in self-play.
- **Use the ladder as the judge.** Unranked quota: **50 match groups per rolling hour** (`cambc match-groups quota
  --json`, `resetsAt`). `tools/replay/ladder_duel.py` plays two versions on identical groups (same opponents,
  maps, sides) back to back and reports paired wins and gem margins. A new candidate needs one arm against an
  arm already played on the same plan (`research/v59/duel_top1.json` has v60, v61 and v62c arms).
- **Submission mechanics.** A submission compiles only while it is the selected version, and it goes live when it
  finishes. Submitting unpins the active version; `submissions activate N` pins N and cancels any queued compile.
  So test one candidate at a time: submit, wait (`tools/replay/await_active.py N`), play its arm, then the next.
  `tools/replay/duel_pipeline.sh <plan> <baseline arm> <bot dirs...>` automates this. Leave a chosen version pinned
  at the end (`ladder_duel.py restore --version N`).
- **Noise.** With 120 games per arm, the margin difference has an SE of about 35-45 gems, and about 20 of 120
  paired games differ by chance. Only large effects are detectable.
- Local gauntlet (`tools/gauntlet.sh`, 70 maps, pool of older versions) is a safety net for faults, fuel and
  catastrophic regressions only.

## Candidates built but not ladder-tested (all in `bots/`)

| Bot | Change | Local vs v61 (840 games) |
|---|---|---:|
| v62a | Winner item build `V59_ITEMS 1` (Treasure, Jungle, Bruiser health, Durability, then Bruiser) | -58 |
| v62b | Maximum disengage `APEX_OUTNUMBERED 1` + `V59_ALONE 1` | -122 |
| v62d | Spell hold `APEX_SPELL_HOLD 3` (no camp spells near enemies, no stuns on camps) | -75 |
| v62e | v62d + `APEX_SAVE_DASH 1` | -100 |
| **v62f** | **Stun hold `APEX_SPELL_HOLD 2` + `NOVA_STUN_FOCUS 1.0`** | **-23** |

v62f and v62d target the measured 2x damage-exchange gap most directly; test them first. Local losses are
expected for this kind of change and are not disqualifying.

## Ideas not yet built

1. **Fight with spells ready.** Hold damage spells too when enemies are likely nearby, then open fights with a
   coordinated burst and stun chain. The top teams' kills come from this.
2. **Real gold concentration.** One carry (Vesper when drafted, otherwise the best-scaling hero) captures what the
   team clears and stacks Bruiser in the main stat. The current funnel is local to Vesper and passive.
3. **Stop death spirals.** In losses 23% of our deaths come within 60 rounds of respawning, and about half happen
   within 15 tiles of our own spawn. The home guard covers visible enemies only; nothing yet handles regrouping
   after respawn.
4. **Our Vesper plays badly.** Drafting Vesper first lost -90 locally; our Vesper earns less than our Vendetta
   despite +33% gold. The meta draft cannot work until this is fixed.
5. A large inventory of ladder-motivated switches is still off; see `research/v59/V59_LOSS_ANALYSIS.md` section 1,
   and grep `common.h` for `ladder` / `top team` near `#define X 0`.

## Tools added this session

`tools/replay/`: `fetch_v59_review.py` (summaries and replays, `--no-replay`, `--kind`), `v59_loss_review.py`,
`fight_review.mjs` + `fight_report.py` + `hero_actions.py` (engine-2 replay fight, death and per-hero action
review), `ladder_calibration.py`, `ladder_ab.py`, `ladder_duel.py`, `duel_pipeline.sh`, `await_active.py`,
`ab_mechanisms.py`, `spawn_heal_probe.mjs`, `probe_snapshot.mjs`. `tools/`: `gauntlet.sh`, `gauntlet_report.py`,
`make_variant.py`. Raw ladder data stays in `artifacts/local-only/`.
