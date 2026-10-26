# Why we never beat Claudus Maximus: what they do, and what did not transfer

Claude Code, 2026-10-25. Data: the 80 v55-vs-Claudus ladder games (1-79, all 40 maps both sides; listings
`data/ladder/v55_games_20261025.json`, `v55_games2_20261025.json`; replays local-only), decoded with the existing
ledger and camp tools plus two new ones: `tools/replay/capture_funnel.mjs` (who clears each camp group and who captures
its reward) and `tools/replay/fuel_outs.mjs` (fuel-out turns per champion). Local experiments: bench3, 28 development
maps × 2 sides × 4 seeds (224 games each), against v57. Descriptive; no holdout maps used.

## 1. What Claudus does

**Draft.** Vesper, Heart of Ruin, Vendetta in all 80 games, then Ryth or Tavi, then Marcella (3-champion maps: the
first three). We never drafted Vesper or Heart. Picks are not exclusive (both teams own Vendetta in every game).

**Vesper is the economy.** Per champion, medians (50 decoded games):

| Champion | capture gold R250 / R500 / R1000 | deaths | Treasure emblem |
|---|---:|---:|---:|
| Claudus Vesper | **466 / 1128 / 2829** | 0 | **R88** |
| Claudus Vendetta | 185 / 541 / 1313 | 1 | R176 |
| Claudus Heart | 147 / 489 / 934 | 1 | R226 |
| our Vendetta (best earner) | 185 / 320 / 540 | 3 | never by median |

Vesper takes 44-49% of their capture gold (she gains +33%, +53% with Treasure). About 30-45% of her gold comes
from captures of groups teammates did most of the hitting on: a partial funnel, not a full one.

**Elk-size groups early.** Capture gold before R250, by group size:

| | elk-size groups (≥2400 hp) | wolf groups | small/harmless |
|---|---|---|---|
| Claudus | 4.0 per game, **655 gold**, 2.7 hitters, 23-round clears | 2.4, 142 | 2.7, 197 |
| v55 against them | 2.3 per game, **266 gold**, 2.5 hitters, 27 rounds | 2.6, 136 | 3.9, 211 |

Their first elk-size clear starts at **R21 with 3.7 champions** and is captured at R50; ours starts at R36 with 2.7
and is captured at R80. Nearly all of the R250 income gap (994 vs 614 per game) is these groups.

Same time allocation: by R250 their Vesper spends 54 rounds clearing and 88 travelling, ours (meta-draft build) 51
and 86, yet earns 466 against 186. The difference is what is cleared and who captures it, not idleness.

## 2. What did not transfer (all against v57, 224 games)

| Variant (bots/v58 switches) | Result | Note |
|---|---|---|
| Claudus draft (`V58_META_DRAFT` 1: Vesper, Heart, Vendetta, Ryth, Marcella) | 92-132, **−89** | our Vesper earns 206 by R250 (theirs 485); team gold unchanged |
| + gold funnel (`UB_GOLD_FUNNEL` 1, existing) | 83-141, **−141** | allies leaving rewards for Vesper costs more time than +33% repays |
| + funnel + 4-champion jobs (`UB_JOB_MAX` 4) | 88-136, −129 | |
| + funnel + draft-turn opening plan (`A2_DPLAN` 1, existing) | 71-153, −217 | |
| Opening pack, own draft (`V58_OPEN_PACK`: whole team on the best own-side elk group) | 99-125, **−52** | works as built: first elk capture R40 (v57 R80), 4.1 hitters; but R250 gold 628 vs 630 and elk captures 2.7 vs 2.7 |

The meta-draft builds also run out of fuel more (fuel-outs ~3.7 vs 1.4 per game, spread over every champion), a
minor factor. Diff: `research/v58/rejected/v58-meta-draft-open-pack-vs-v57.diff`.

## 3. Reading

* Copying Claudus's visible choices (draft, funnel, team opening) on our controller loses to our own lineage every
  time. Their advantage is a coordinated farming loop (elk groups cleared by 3-4 champions, rewards routed to an
  early-Treasure Vesper, repeated through R250), not any single choice; pieces of it on their own cost more than they
  return.
* Losing to v57 does not show a change is worse against Claudus. Every local opponent is our lineage, which went 1-79
  against them. Since v53, ladder-motivated changes (camp choice fitted to top teams, offline-RL camp values, gold
  funnel, team plans) have all failed this same local test. The local bench measures self-play strength only.
* The opening pack is the clearest case: it reproduces Claudus's opening timing exactly, but the rest of our loop
  doesn't follow up on it.

## 4. New facts for evaluation

* The competition pool has **55 maps; 15 are new** and absent locally and from all our ladder listings: 00anvil,
  00breadcrumbs, 00crater, 00dunes, 00galaxy, 00oasis, 00quarry, 00ribs, 00the_line, 00vault, adgato_gemcombat1-5.
  They are untested ground for every version and a fresh holdout (`cambc maps pull` refreshes maps/).
* Unranked match groups: quota **50 groups (250 games) per day** (3 used when checked; it resets daily, next at 22:11 UTC). A group
  plays our *submitted* bot against a chosen team on five chosen maps. This is the only way to measure anything
  against Claudus.
