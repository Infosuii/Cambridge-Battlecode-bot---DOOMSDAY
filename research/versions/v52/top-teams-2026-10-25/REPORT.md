# Top-team replay findings and comparison with DOOMSDAY

25 October 2026 · official Cambridge Battlecode, engine 1.0.3

The most concrete source issue found is in **draft selection**: v52 excludes
champions already picked by the opponent, although **35 of these 36 official
games contain mirror picks**. The clearest observed gameplay failures are
**turning boss_battle's carried gems into score** and **securing repeated stampede
rewards**. A further economic difference worth testing is early Treasure emblems:
five of the six leading teams used them extensively; DOOMSDAY had none at the
measured checkpoints. These findings support specific experiments, not a claim
that copying one team will produce a stronger bot.

## Evidence and scope

Downloaded **36 original replay bundles** from the official website through the
official CLI: **24 games**, four selected for each of the current top six teams,
plus **12 DOOMSDAY games**. Downloads totalled **1,342,091 bytes**. The repository's
`decode_replays.mjs` decoded all 36, covering **7,959,573 timeline steps** and
**39,545 game rounds**. A second census reconciled every game's score, outcome,
rounds, drafts, actions, fuel events and replay checksum with the standard
decoder and official match metadata: **36/36 passed**. See [checks](checks.json),
[selection](selection.json), [watchable match index](MATCH_INDEX.md), [match provenance](matches.json) and
[reproduction instructions](REPRODUCE.md). The final [verification receipt](verification.json)
also checks unique replay hashes, the quoted draft/item counts and unchanged bot sources.

Selection was fixed before replay downloads and decoding. It preferred our weak
maps and stronger opponents, without selecting on the result. There are **15
maps** in the top-team sample and **8 shared maps** with DOOMSDAY. Top focal sides
are 13 A / 11 B; DOOMSDAY is 4 A / 8 B. Opponents and drafts differ. This is a
small purposive scouting sample, **not a paired strength benchmark**. Body and
checkpoint counts below are descriptive; they are not independent trials.

The ladder snapshot was generated at **14:10:35 UTC**:

| Rank | Team | Rating, rounded | Selected games |
|---|---|---:|---:|
| 1 | Intercontinental Fish | 2351 | 4 |
| 2 | Claudus Maximus | 2293 | 4 |
| 3 | Mite | 2279 | 4 |
| 4 | willow best girl | 2266 | 4 |
| 5 | Trzy Kwaterki | 2226 | 4 |
| 6 | prism best girl | 2216 | 4 |

DOOMSDAY was **rank 84, rating 1840**. Source comparison uses `bots/v52` at commit
`2e1dcc1cf859a3a9162e58c5f2b6285c8217bd8f`, documented as deployed at 12:02 UTC.
The selected DOOMSDAY matches were created between 12:10 and 14:10 UTC. Public
metadata and authenticated CLI match details hide submission versions, so their
exact source identity is **unverified**. They are labelled **post-v52 deployment**,
not asserted to be byte-identical v52 games. The separate `bot/` policy-v2
framework is not the live-bot comparison. See [source identity](source_identity.json)
and the detailed [source review](SOURCE_REVIEW.md).

## 1. Draft: an avoidable restriction, plus a different composition

In v52, `A2_MLDRAFT 1` attempts the learned draft on every map. A successful pick
returns before fixed lineup tables. Inside that path, both our picks **and the
opponent's picks** are marked `taken`, then skipped as candidates
([draft.cpp, line 645](https://github.com/Infosuii/neural-networkk-battlecode/blob/2e1dcc1cf859a3a9162e58c5f2b6285c8217bd8f/bots/v52/src/draft.cpp#L645)).
Yet the official engine replays and metadata agree on shared picks in **35/36
matches**. For example, both sides drafted Vesper Vale, Marcella and Heart of
Ruin in [willow best girl vs Intercontinental Fish](https://2026a.battlecode.co.uk/game/match-groups/24293b41-5828-49a6-8586-33321ba98949).
The current policy therefore excludes options the game permits.

| Champion | Top focal sides, 24 games | DOOMSDAY, 12 games |
|---|---:|---:|
| Vesper Vale | 23 | 1 |
| Marcella | 22 | 8 |
| Heart of Ruin | 17 | 4 |
| Vendetta | 17 | 10 |
| Ryth | 12 | 2 |
| Varg | 0 | 11 |
| Ren | 0 | 11 |
| Cassi & Issac | 3 | 5 |

**Next test:** correct the opponent-pick exclusion in an isolated draft-only
variant, keep weights unchanged, verify legal own-team duplicate handling, and
run the existing release/default-fuel gate against v52. Separately test selected
map compositions. The pick frequencies do not establish the best counter-pick
or explain all of DOOMSDAY's composition difference. [Draft evidence](draft_audit.json).

## 2. Economy: early income investment is common, with a strong exception

Exact round-boundary inventories show:

| Checkpoint | Top bodies with a Treasure emblem | DOOMSDAY bodies with one |
|---|---:|---:|
| Round 250 | 47 / 112 (42%) | 0 / 65 |
| Round 500 | 69 / 112 (62%) | 0 / 65 |

All selected games reached round 500, so these two comparisons do not exclude
shorter games. They include alive and dead bodies. Cassi and Issac are separate
bodies. At round 500, the median earned gold per body was **484.5** for top focal
sides and **400** for DOOMSDAY; at round 250 it was **168.5 vs 190**. Map, champion,
gold distribution and death differences prevent attributing this change to items
alone. [Inventories](inventory_checkpoints.csv), [checkpoint totals](inventory_summary.json).

The [SDK](../../../sdk/cpp/cambc.h#L1522) defines Treasure emblems as increasing gold gained by 20%. v52's normal
build paths have no Treasure purchase; its alternative Treasure/bruiser build
path, `UB_PROXY`, is disabled. This is a clear source/behaviour difference. However,
**prism best girl had 0/17 Treasure-equipped bodies at round 500 and won all four
selected games**. Treasure is a common successful approach, not a universal
requirement. The other five leading teams had 12–15 Treasure-equipped bodies
each across their four games.

On boss_battle, successful sides sometimes had one very wealthy carrier. Ad
Astra's Vesper Vale had **10,000 maximum health**, a Treasure emblem and **28
bruiser emblems** at the first full gate-group clear. This supports investigating
income investment and unequal resource distribution; the replay does not reveal
whether deliberate gold funneling caused it.

**Next test:** one isolated early-Treasure build variant on appropriate farming
maps, measuring round-250/500 gold and item readiness, clear time, deaths and final
score. Account for the initial cost and delayed combat items. Do not enable every
change in `UB_PROXY` together and attribute the result to Treasure alone.

## 3. boss_battle: scoring access is the bottleneck

The gate is **group 16**, two monoliths at (24,20) and (23,20), **40,000 total HP**,
400 gems and 600 gold. The older description of a 20,000-HP group understates the
combined health. v52 already detects camp-blocked altars, suppresses banking while
`no_bank` is true, and rebuilds the altar field when access opens. A lower bag
threshold alone cannot make a blocked altar reachable.

The table records the **match-wide first whole-group clear** and the eventual
winner's first completed bank. It does not attribute the clear to that winner or
imply both camps must die before any individual altar access tile opens.

| Selected match: eventual winner | First whole-group clear | Winner's first bank | Final scores, A–B |
|---|---:|---:|---:|
| willow best girl vs Intercontinental Fish: willow | 519 | 531, 53 gems | 1124–234 |
| Intercontinental Fish vs Claudus Maximus: Claudus | 538 | 727, 728 gems | 0–1124 |
| Univardisty of Shingtonwash vs willow: willow | 555 | 726, 294 gems | 46–1139 |
| Trzy Kwaterki vs Ad Astra: Ad Astra | 639 | 675, 418 gems | 0–1021 |
| Rogue Lock Pickers vs DOOMSDAY: Rogue | 951 | 975, 441 gems | 1039–0 |
| DOOMSDAY vs Manta: DOOMSDAY, gold tiebreak | Never | Neither side banked | 0–0 |

DOOMSDAY ended its two games carrying **908** and **2,140 gems**, with **zero
submitted gems in both**. Winning the 0–0 game by gold does not resolve this
scoring failure. By contrast, Claudus won while still holding 1,529 gems: a large
bag is not automatically a mistake when the side also converts enough to score.

In the Rogue game, the first gate damage was recorded at round 22; nearby
DOOMSDAY Cassi and Prism were already at **180/600** and **160/700 HP**, with no
emblems. This is state evidence, not proof of which action or decision branch
caused it. The prior v53 forced gate job was rejected and remains off.

**Next test:** a readiness-based gate plan that budgets damage and survival,
keeps a commitment through assembly, and explicitly uses an open access window
to bank. Track each individual gate camp, access availability, arrival times,
health/items and banking completion. Test draft/build readiness before reviving
the rejected whole-team rush. [Objective evidence and match IDs](objective_cases.json).

## 4. stampede: targeting the camp does not secure the repeated reward

The sole gem group has **20 camps, 16,080 HP and 160 gems**. v52's special rule
targets it from round 500 when health and bag guards pass. The downloaded games
show why target selection is only one part of the job:

| Match | First full clear | DOOMSDAY first bank | Final score and outcome |
|---|---:|---:|---|
| DOOMSDAY vs Sydney's Realist | 795 | 835 | 320–320; DOOMSDAY loses by gold |
| Live Love Larp vs DOOMSDAY | 619 | Never | 1120–0; DOOMSDAY loses |
| hello vs Claudus Maximus | 983 | — | 160–960; Claudus wins |

DOOMSDAY's first game banked earlier than the selected Claudus game, yet produced
only 320 score. In the 0-score loss, all five DOOMSDAY bodies were near the group
at its first damage census (round 567); at the first full clear (619), only its
Prism remained within eight tiles, alongside an opposing Ryth. Proximity is not
capture ownership or damage attribution, but it makes survival and reward
security a more useful next diagnostic than merely starting the attack earlier.
Claudus banked 960 across seven deposits, including two 80-gem deposits;
Live Love Larp banked 1,120. Whole-camp rewards can be split across carriers.

**Next test:** measure survival through the clear, capture progress/ownership,
who receives the gems, and time to return for the next spawn. Preserve the v52
targeting fix while addressing those stages individually. Two post-deployment
losses do not establish that the fix never helps.

## 5. Other maps and checks against easy explanations

| Shared map | Top focal sample | DOOMSDAY sample | Observation |
|---|---|---|---|
| concentrated_wealth | Mite: 1011 score, first bank 146 | 233 score, first bank 421 | Examine the early capture-to-bank cycle. First match-wide group-0 clears were 114 and 125; those do not establish capture ownership. |
| great_wall | Trzy: 1020 score, first bank 97 | 693/1004 score, first banks 308/227 | Delayed first scoring is worth inspecting; different opponents and sides remain a major limitation. |
| yellow_brick_road | willow: 1016 score, 0 body deaths | 763 score, 17 body deaths | Survival and combat exposure are plausible diagnostics here. One game per side is insufficient to select a fix. |
| islands | Mite: 1009 score, first bank 81 | 1007/1013 score, first banks 70/76 | The two observed DOOMSDAY wins give no reason to replace its working island movement indiscriminately. |
| elkring | Three top games, median score 1012 | One DOOMSDAY win, score 1012 | The historical weak-map label does not describe every current game. |

Across all focal games, median first banking was **116** for top teams versus
**85** for DOOMSDAY, among **23/24** and **9/12** games that banked. This excludes
bankless games and compares different map mixes. Median completed bank sizes
were **31 vs 29**. Neither result supports a universal earlier/smaller-bank rule.

Raw median body deaths were 4.5 vs 7, but deaths per 1,000 scheduled body-rounds
were essentially identical: **1.078 vs 1.079**. The rate includes dead-time and
counts both Cassi and Issac. The sample does not support a broad claim that top
teams die several times less often. Top focal sides had **439** fuel-exhausted
turns versus DOOMSDAY's **35**; 227 top-side hits came from Mite's island game,
which it won. Both cohorts had zero decoded error-turn events. Cap-hit counts
cannot measure headroom on other turns or explain a win by themselves.

The broader recent **metadata-only** window has DOOMSDAY at **26/55 wins**,
including 0/2 stampede, 2/2 islands, 2/2 big_world and 1/2 boss_battle. These small
map counts contextualise the selected replays; they are not additional decoded
games. [Recent metadata](recent_doomsday_metadata.json), [per-map comparison](map_comparison.csv).

## Recommended order for later development

1. **Draft eligibility correction:** small, concrete source discrepancy; test it
   alone with existing weights and legal own-pick masking.
2. **Economy/build experiment:** compare one early-income change against v52,
   with item readiness and final score as outcomes. Retain a no-Treasure control.
3. **boss_battle access plan:** diagnose per-camp gate openings and prepared
   arrivals, then bank within the window. Do not simply enable the rejected rush.
4. **stampede capture security and repeat cycle:** log survival, capture progress,
   recipient and re-entry, rather than only selected target.
5. **Map-specific banking/combat:** concentrated_wealth, great_wall and
   yellow_brick_road, with one change at a time and matched opponents/sides.

Use the existing development-map/seed gate for any candidate and the holdout
procedure for a later release. The scouting games are not holdout evidence.
Preserve the fuel-sensitive hot paths when implementing a hypothesis.

This work changed analysis tools and documentation only. **No training,
parameter updates, new matches, bot-source changes or submissions ran.** Raw
replays, downloads and full decoded action/state traces remain local and ignored.
The repository contains compact evidence and reproducible methods.
