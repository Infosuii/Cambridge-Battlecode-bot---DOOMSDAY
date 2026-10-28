# How the top teams beat us in fights, and the team-fight system (2026-10-28)

## Research audit correction (2026-10-28, read first)

Research is paused at the user's request. New structural experiment results and exact continuation are in
`research/v81/RESEARCH.md` and `research/v81/HANDOFF.md`; fresh-laptop entry point is repository `CONTINUE_HERE.md`.
MG18208504 adds concrete objective-control evidence. Its600-gold groups span both spawns, so first-camp location
does not establish home ownership. A denial prototype and concentrated-objective prototype were tested and failed
their initial strength screens. No new bot is a proven replacement for v76. No live changes were made.

The historical contact table below used `kinds == {4}` for "move without hitting or casting". That excluded moves
accompanied by recall/cancel/ward and materially understated opponents' movement. The correct predicate is
`4 in kinds and not (kinds & {5,6})`. In the same 90 losses it is **46.6% ours vs 42.9% opponents**, not 44.7% vs 20.9%.
In our 30 wins it is 43.3% vs 45.3%. The type-specific strict-move comparisons below have the same defect and must not
support strategic conclusions. `micro.py` is now corrected; old output files are preserved as historical evidence.
`state_policy.py` already used the correct action predicate, but its local-health bins remain observational.

The cast gap (14.6% vs 20.2%) survives. Raw summed HP and a loss-selected sample do **not** establish equal effective
combat power or prove that retreat causes defeat. Exact native earnedGold in the 90 losses: R100 283/381, R200 631/844,
R300 996/1,407, R500 1,763/2,767 (87 pairs reach R500). These are descriptive disadvantages, not isolated causes.
Audit scripts/output and new structural experiments: `research/v81/RESEARCH.md`, `corrected_contact.txt`.

Read-only official status: repo v74 is active platform **68**; platform 69 is repo v75 and inactive. No platform changes
were made. Also, `ladder_duel.py run` activates each arm; the historical suggestion to use it without live activation
was incorrect. Any such future experiment needs explicit authorization for both submission and temporary activation.

Data: the v74 ladder duel against the top 12 (120 games: 90 losses, 30 wins; `research/v75/duel_v74.json`, timelines in
`artifacts/local-only/duel-v74/*/timeline.json`). v74 is live and v76/v78 differ from it only in per-map knobs, so its
losses are our current losses. Tools: `tools/v67/c_engage.py` (fights, numbers, focus, kill anatomy; output
`research/v75/engage_duel_v74.json`), `tools/v67/c_miclog.py` (our contact turns by bot mode, local A2_MICLOG runs).

## What does not separate us from them

| In the 90 losses | Us | Top team |
|---|---:|---:|
| Hits on the round's main target when 2+ champions hit champions (focus fire) | 86% | 86% |
| Fights started with at least even local numbers | 66% | 70% |
| Nearest teammate 5 rounds before a fight (median tiles) | 3 | 3-4 |
| Present champions that land a hit (2 present) | 78% | 86% |

Deaths per 1,000 champion-rounds by grouping 6 rounds earlier: alone 3.1, pair 3.0, tight 3.8 for us; 0.8, 0.8, 1.3 for
them. We die three to four times as often whether alone or grouped, so gathering alone cannot close the gap.

## What does

Fights are decided by local power, and we lose even fights. Fights by our local health ratio at the first hit (losses):
below 0.5: 0.73 of our deaths per fight vs 0.17 of theirs; 0.8-1.25: 0.58 vs 0.43; above 2: 0.31 vs 0.60. Even numbers,
even health, rounds 0-200 (no gear gap yet): 0.76 vs 0.36. In won games the same tables flip.

How each side spends contact rounds (an enemy champion within 4 tiles):

| | Us (losses) | Top (losses) | Us (wins) | Top (wins) |
|---|---:|---:|---:|---:|
| Hit a champion | 26.8% | 33.3% | 30.9% | 34.7% |
| Cast | 14.6% | 20.2% | 17.2% | 19.4% |
| Move without hitting or casting | 44.8% | 20.9% | 41.6% | 25.0% |
| ...of which away from the nearest enemy | 28.0% | 8.0% | 19.8% | 11.4% |
| Nothing | 14.1% | 7.8% | 12.8% | 7.5% |
| Health lost per contact round | 53 | 26 | 38 | 37 |
| Direction reversals per contact episode | 2.60 | 1.72 | 2.13 | 2.29 |

Same champion, same situation: Heart moves without acting in 38% of contact rounds (top teams' Heart 14%), Vendetta 42%
(12%), Marcella 51% (25%), Vesper 37% (18%). Healthy (70%+) and locally stronger (health ratio 1.2+), our champions
still step away without hitting in 20% of contact rounds (theirs 12%) and hit in 36% (45%).

Where our wasted contact turns come from (local, v78 vs proxy and v65, seed 24, 192,712 contact turns): `flee` is 28% of
contact turns and 53% of flee turns land nothing (15.1% of all contact turns); `fight-champ` approach steps that end out
of reach are 13.9%; camp approach 2.5%. The flee/fight verdict in `handle_enemies` re-races time-to-kill against
time-to-die every turn, so it flips as health and ranges change: fight, step away, step back in.

## The team-fight system (bots/v79, `V79_TF` bits; all off reproduces v78 = v76)

1. **Team verdict with commitment** (bit 1). Power at the contact point = summed health x summed damage of each side,
   champions weighted by how soon they can hit there. Every champion computes it from the same team vision, so teammates
   agree without messages. Engage at 1.3 and keep fighting while it stays at 0.8 or above (only health below 25% or a
   lethal burst next turn break it); leave at 0.7 and turn back only at 1.6 after 3 rounds. Carriers of 60+ gems need
   twice the edge.
2. **Team focus** (bit 2). The enemy the team kills fastest at the contact point (health over the damage of our
   champions that reach it next turn, discounted by its bag), the same pick for every teammate.
3. **Gather** (bit 4). Leaving champions fall back toward a healthy ally farther from the threat; a healthy champion
   without a big bag walks to an ally within 12 in contact when the fight there is a team win with it and not already a
   clear win without it.

### Where else the gap is (same data)

Early (rounds < 300) both sides' champions hit equally hard and have the same health (lone basic attack: Vendetta 70
vs 70, Ryth 45 vs 45; Heart, Marcella, Vendetta max health equal), yet even fights there cost us 0.76 deaths to their
0.36: behaviour. From round 300 a gear gap opens: their Vesper hits 130 (ours 85) with 1,700 health (1,000), Varg 110
(55), late Marcella 2,900 health (1,700); items per champion after round 700: 10.5 vs 7.6 in our losses, 6.8 vs 12.5
in our wins. Early contact by situation: healthy and locally stronger, they hit in 48% of rounds (us 41%) and step
away in 11% (17%); below 35% health with an even or better local ratio they keep hitting in 47-48% (us 33-35%) and
step away in 26-32% (43-44%).

## Local results (v79 variants vs v78 = v76, proxy per team, seed 24, 140 paired games, A2_MICLOG builds)

Contact turns locally: flip-flops (flee between fight turns within 3 rounds) are only 8% of flee turns; most flee turns
are sustained retreats (36% below 35% health, 31% above 70%).

| Variant | Margin vs base | Deaths/game | Gold/game | Flee share of contact |
|---|---:|---:|---:|---:|
| bits 1 (ratio opens; leave until 1.6) | -501 [-645, -353] | -3.3 | -1,402 | 57% (base 30%) |
| bits 1+2+4, same | -442 [-570, -326] | -2.1 | -1,028 | 51% |
| A: bit 1, leave only from a fight, 4 rounds | -31 [-123, +63] | -0.4 | +33 | 33% |
| B: as A, also leave at ratio 0.5 with an enemy in reach | -74 [-152, +11] | -1.5 | -136 | 39% |
| C: as A + focus + gather (bits 1+2+4) | +8 [-96, +107] | -0.6 | -27 | 30% |
| D: bit 1+8, the bot's own verdict opens the commitment | -1 [-94, +100] | -1.3 | +206 | 33% |
| E: D + focus + gather + join (bits 1+2+4+8) | -139 [-253, -23] | +1.0 | -344 | 34% |
| F: D with the leave lock only while the team ratio is below 0.8 | +4 [-93, +98] | -1.0 | +429 | |
| G: F + focus + retreat toward allies (bits 1+2+4+8) | -22 [-123, +84] | 0.0 | +319 | |
| H: F + fight together (bits 1+8+32) | -17 [-95, +55] | -0.3 | +92 | 31% |

Against v65 (same seed): D -93 [-225, +41] (deaths +0.3, gold -441), E -309 [-425, -193] (+2.6), F -95 [-231, +25]
(-0.2, -146), G -167 [-272, -57] (+0.8, -521), H -148 [-267, -44] (+0.4, -428). Joining allies' fights (A2_TEAM before, bit 16 now) costs farming every
time; focus and retreat-toward-allies add nothing locally.

The first leave lock broke the team apart: on 00vault two champions got a passing flee verdict at full health during
the opening 4v4 and stayed out for 4 rounds while the other two fought; base turns back in and wins that fight. Hence F.
00vault stays the most swung map for every variant: the opening rush there flips on a round of timing.

Splits in fights (ladder, `research/v75/teamfight_scripts/split.py`; two or more teammates within 3 and an enemy within 4):
in our losses one of ours hits while a neighbour leaves in 21.8% of those rounds (top teams 13.7%), all hit in 14.9%
(22.9%), all leave in 9.1% (2.8%); in our wins 14.3%, 19.0%, 4.8%, as the top teams. Bit 32 (beside a healthy teammate
the team ratio opens the fight) targets this.

## Validation of the default (bots/v79, V79_TF 9 = F, plain build) against v76 (= v78), seed 24, 140 paired games each

| Opponent | Margin vs v76 | Deaths/game | Gold/game |
|---|---:|---:|---:|
| v65 | -72 [-202, +55] | -0.3 | -59 |
| v61 | -107 [-214, +4] | -0.4 | -325 |
| v58 | -82 [-184, +18] | -0.4 | -382 |
| proxy | -24 [-129, +68] | -1.2 | -127 |

(`research/v75/v79_paired.txt`.) With V79_TF 0, v79 plays v78 game for game (10 games checked). Every opponent is below
zero: the commitment saves 0.3-1.2 deaths a game but loses farming and fights the old flip-flopping won. Against our own
lineage, at least, the team-fight layer is a loss; the one earlier fight rule tested on the ladder (V75 lone guard) was
neutral locally and -91 there, so the local sign has held so far. Not a release candidate on local evidence; only a
ladder arm beside v76 (same match groups) can show whether the top teams punish flip-flopping more than our league does.

## What the ladder data points to instead

1. Gear from round 300: the same champions out-stat ours (Vesper 1,700 vs 1,000 health and 130 vs 85 per hit at 4.7 vs
   3.6 items; items per champion after round 700 10.5 vs 7.6 in losses). Item choice and economy, not fight rules.
2. Early fights at equal gear (0.76 vs 0.36 deaths per even fight before round 300): they hit in 48-58% of contact
   rounds where we hit in 41-43%; the gap is in casting and in stepping away, not in focus or numbers.

Scripts for every ladder table above: `research/v75/teamfight_scripts/*.py INDEX FOLDER` (run from the repo root, e.g.
`split.py research/v75/duel_v74.json artifacts/local-only/duel-v74`).

## v80 continuation: measured fixes (2026-10-28)

The pending six-run screen completed. Every check below uses seed 24, all 70 maps/both sides, **140 distinct paired
games per opponent**. No platform version was submitted, selected or activated. Logged builds affect fuel and can
affect game outcomes: plain-build validation is the acceptance evidence.

Screen paired against the matching MIC80 all-off baseline (`v80_fix_paired.txt`):

| Variant | Proxy margin delta, 95% map-bootstrap interval | v65 delta | Deaths delta proxy / v65 |
|---|---:|---:|---:|
| SHARE | +25 [-54, +121] | -66 [-199, +70] | +0.8 / +2.3 |
| RECALL | +15 [-61, +96] | +29 [-29, +91] | -0.8 / -0.2 |
| Both | +34 [-69, +150] | -39 [-174, +100] | -0.3 / +2.4 |

SHARE is rejected as a default. It changes the intended behavior but hurts survival. Pooled over the same 140 proxy
games, grouped hit/leave splits fall 17.2% -> 14.7%, all-leave 4.3% -> 2.3%, all-hit rises 22.6% -> 27.2%; however,
early equal-HP/equal-number fights go from 0.38/0.51 deaths (us/them) to 0.50/0.48. More standing and fighting is not
a sufficient success measure. `v80_fix_replay_measures.txt` contains the original ladder scripts; `v80_fix_pooled.txt`
and `MIC80-*_metrics.json` pool wins/losses to avoid comparing changing loss cohorts.

RECALL alone passed no strength threshold in plain validation (`v80_recall_validation.txt`, versus Q-*-v78, seed 24
intersection): v65 -24 [-85,+37], v61 +8 [-31,+45], v58 -27 [-93,+43], proxy +4 [-53,+60]. Default is provisionally
RECALL=1, SHARE=0 for the recall-only control (`V80-*`). Final candidate defaults are recorded below. Recall is a
correctness candidate, not an established competition improvement.

### Casting audit and rejected forced casts

`audit.mjs` / `audit_batch.py` export actual champion-turn observations, spell cooldowns and actions from the **120
existing ladder replays**, through R500; `audit_report.py` reports early contact before R300. No extra games are used
for this diagnosis. In the 90 losses: ready offensive spell in geometric reach but no cast: Marcella 30.8% of contact
turns, Ren 42.5%, Ryth 36.0%; top equivalents 12.0%, 4.9%, 5.4%. Excluding turns without can_cast reduces ours to
30.2%, 36.6%, 30.7%. Top teams' cancelled recalls make their initial can_cast flag conservative, so compare both
columns. Our camp-spell cooldown explains 4.3% of all early contact versus their 6.8%, not the main casting deficit.

V80_CAST_FLEE=1 spends a ready movement-exclusive nuke/stun before retreat for a melee champion above 35% health
without a ready dash. Plain paired deltas over RECALL: v65 -1, v61 -98, v58 -69, proxy +38; **rejected**, left off.
Its proxy gain does not generalize (`v80_cast_validation.txt`).

A different, movement-preserving omission is now isolated: early losing contact has a basic hit with an unused ready
attack reset and no ready dash in 587/11,602 turns (5.1%) versus 64/12,246 (0.5%). This includes Marcella 9.3%, Varg
8.3%, Ryth 7.7%. `V80_RESET_FLEE` tests spending that reset before retreat, keeping dash escapes and avoiding a dead
target. Its measured local results and final status are recorded below.

### Gold per camp-hit decomposition

`v80_ladder_audit.txt` traces real camp reward transitions, uses static group gold, and counts both basic/spell camp
hits by acting champion. First R500 of ladder losses: base capture gold per hit 3.265 vs 3.809; base gold/game
1,389 vs 1,862; 1,919 vs 2,145 captures across 90 games. Average base gold/capture is 65.1 vs 78.1. Own hit rounds
converted to own captures 86.0% vs 90.3%; clear-to-capture delay 8.9 vs 7.2 rounds. Group choice and capture conversion
both contribute. Mixed groups are labelled by their first camp type; do not interpret these as pure-type cohorts.

Gold on capture rounds is 1.10x base for us, 1.18x for them, but that broad ratio includes concurrent payouts.
`capture_bonus.py` isolates single captures without champion deaths, tribute or item changes: Treasure-only
non-Vesper recipients receive exactly 1.10x across camp types. Prospector-only median is 1.083x in wolf-first groups,
1.045x in elk-first groups, 1.25x in gold-first groups. Mixed groups/other contributors mean this is **not** a proof of
Prospector's full engine formula. Vesper and Treasure stack additively: observed median ~1.43x, not 1.33*1.10.

V80_TREASURE=1 replaces the Prospector opening with same-stat Treasure. Four-opponent plain deltas over RECALL:
v65 +23 [-68,+115], v61 +4 [-81,+91], v58 +16 [-68,+97], proxy +44 [-27,+114]. Whole-game gold increases by
449/426/396/404 per game respectively. All margin intervals include zero: a consistent economy signal, no large
strength breakthrough (`v80_treasure_validation.txt`). Exact native R300 income changes +6/-1/+7/+3, R500 -8/+26/+41/+50
gold versus recall-only. This does **not** solve the gap opening at R300 (`v80_treasure_native_windows.txt`).

V80_SHARE=2 is a stricter diagnostic: count only allies within 3 of us, both at least half health, already in attack
range of the enemy; retain at least half the enemy threat. Paired v65 -20 [-106,+62], proxy -28 [-97,+35]; pooled grouped
hit/leave splits 16.8%/16.2% versus controls 16.3%/16.1%. No mechanism gain, keep off (`v80_cover_paired.txt`).

### Movement-preserving resets and combined candidate

RESET_FLEE alone versus recall-only: v65 +53 [-54,+165], proxy -31 [-115,+50]; deaths -0.5/-0.4. Contact cast rates
16.8% -> 18.0% (v65), 16.6% -> 17.3% (proxy). Early equal-number/HP fight deaths 0.34/0.49 -> 0.33/0.51 against v65,
0.36/0.51 -> 0.33/0.64 against proxy. This fixes the missed reset path; local strength is still uncertain.

The combined **RECALL + TREASURE + RESET_FLEE** candidate is `V80PKG-*`, 140 games per opponent, all plain builds.
Defaults in bots/v80 now match it. SHARE, CAST_FLEE and V79_TF remain off. This is a saved research candidate, **not a
validated competition upgrade**. Results versus v76 (Q-*-v78, only common seed 24):

| Opponent | Wins candidate / control | Paired gem delta [95% map-bootstrap interval] | Deaths/game delta | Whole-game gold delta |
|---|---:|---:|---:|---:|
| v65 | 89 / 91 | -12 [-119,+109] | +0.5 | +419 |
| v61 | 101 / 95 | -3 [-92,+84] | -1.2 | +427 |
| v58 | 98 / 98 | +52 [-38,+138] | -1.2 | +764 |
| proxy | 109 / 112 | -5 [-94,+90] | -0.5 | +411 |

Total wins 397/560 vs 396/560. No interval excludes zero. All candidate runtime-fault counts are zero; fuel exhaustion
0.49/0.51/0.60/0.56 per game. Detailed results: `v80_package_vs_v76.txt`; ablation versus recall-only:
`v80_package_validation.txt`.

Replay measures, **candidate vs recall-only control**, pooled across the same complete schedule (not changing loss sets):

| Opponent | Grouped hit/leave split | Contact cast | Early-even fight deaths us/them, candidate (control) | Farm gold/camp-hit |
|---|---:|---:|---:|---:|
| v65 | 15.3% (16.3%) | 17.4% (16.8%) | 0.36/0.51 (0.34/0.49), 168 vs 174 fights | 3.85 (3.85) |
| v61 | 16.7% (16.2%) | 17.7% (17.0%) | 0.41/0.63 (0.33/0.56), 164 vs 174 | 3.78 (3.73) |
| v58 | 15.9% (16.5%) | 18.2% (17.1%) | 0.47/0.64 (0.51/0.74), 174 vs 177 | 3.81 (3.74) |
| proxy | 15.7% (16.1%) | 17.2% (16.6%) | 0.36/0.68 (0.36/0.51), 132 vs 146 | 3.82 (3.86) |

`v80_package_replay_pooled.txt` / `V80PKG-*_metrics.json`; control rows are in `v80_cast_replay_pooled.txt` and
`v80_treasure_replay_pooled.txt`. More casting is measured; the original large split and early-fight gaps are not closed.
Native exact earnedGold (including kills/passives) at R300 changes -30/+2/+1/-6 versus recall-only, at R500
-26/+35/+90/+35. Later income improves, but the R300 gap remains. Windows exclude any pair where either game has
already ended (`v80_package_native_windows.txt`). Whole-game gold alone was an overly favorable description of the effect.

Clean official v80 build is byte-identical to the tested package:
`8d11f97cfa7269736330acf119e3c61b08123530220455a5f558aa51e0903c73`. Clean v76 also matches the Q-v65-v78 comparator.
Review source archive/per-file manifest: `artifacts/tmp/v67/v80-review/`; candidate summary: `bots/v80/CHANGES.md`.
No submission or live-version change occurred. Paired real-ladder v76/v80 testing needs the user's approval before
submitting either source tree. This data does not justify activation.

The added helpers have different CLIs; see their docstrings. Only the original ladder-table scripts take the blanket
`INDEX FOLDER` form. Payout attribution is at round resolution and recorded camp-target turns miss off-center AoE damage;
these are consistent diagnostic measures, not exact per-monster damage attribution.
