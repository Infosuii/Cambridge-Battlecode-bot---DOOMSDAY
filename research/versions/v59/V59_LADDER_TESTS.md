# Ladder tests (2026-10-26)

All unranked match groups, queued with the user's permission. The quota is 50 groups per rolling hour, not per
day. Match groups play the active version: a submission goes live (and unpins the active version) as soon as it
compiles, and re-pinning another version cancels a queued compile. So candidates are submitted one at a time.

## Platform versions

| Platform | Repository | Content |
|---|---|---|
| 57 | v58 | Sprint 3 economy |
| 58 | v59 | Bruiser stacks instead of Greed, outnumbered retreat (margin 2) |
| 59 | v60 | v59 + spawn home guard + gold funnel to Vesper |
| 60 | v61 | v60 + opening pack (3 champions take an own-side elk group first) |
| 63+ | v62c, v62a, ... | duel candidates (see below) |

## 1. Paired sets other teams ran against v58 (24 sets, 120 games per version, mostly mid-ladder)

| Version | Wins | Expected from v58's rates on the same sets |
|---|---:|---:|
| v59 | 79/120 | 78.7 |
| v60 | 79/120 | 78.7 |

96 of 119 paired v59/v60 games had the same result. On the same sets v59 cut our deaths from 8.62 to 7.08 per
game and gems lost on death from 163 to 115 (`tools/replay/ab_mechanisms.py`), but not the result. Half of these
sets are opponents we beat 80-100% of the time, so there is little room to improve; the user asked for top teams
instead.

## 2. Top-12 duel (`tools/replay/ladder_duel.py`, plan `duel_top1.json`)

Ranks 1-12, two groups each, random pool maps, alternating sides; each arm plays the identical 24 groups.

| Arm | Wins | Mean gem margin | vs v60 (paired) |
|---|---:|---:|---|
| v60 (platform 59) | 15/120 | -465.0 | baseline |
| v61 (platform 60) | 21/120 | -462.3 | +2.8 ± 34.1 margin; 12 vs 6 discordant wins, z = +1.41 |
| v62c (platform 63, group up) | 15/120 | -494.0 | -29.0 ± 44.0 margin; 9 vs 9 discordant |

Against the top 12 (v60's 117 decoded replays, `tools/replay/fight_review.mjs`): we die 15.5 times per lost
game to their 4.6, and they kill us 11.9 times to our 4.0. Gold at R100 is 295 vs 353 and at R500 1,704 vs
2,520. In contact we lose 36.6 hp per round to their 17.1. They cast spells on our champions about twice as often
(Marcella 23.7 vs 12.5 per game, Heart 20.2 vs 10.2, Ryth 22.7 vs 12.3) at the same total cast rate. We spend
cooldowns on camps; they arrive at fights with spells ready.

Final state: platform 60 (v61) active and pinned at 20:30 UTC. Ranked since 18:11 (versions switched during duels): 30/65.
