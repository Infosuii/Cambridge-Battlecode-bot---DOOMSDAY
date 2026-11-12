# Why we lose: v67 ladder losses, round by round (2026-10-28)

Data: every ranked game of live platform version 67 (v66b) since it went live on 2026-10-27 22:10 UTC: 285 games,
145 wins (51%), 140 losses. Summaries for all, replays for every loss (`research/v75/collect_v67.py`,
`artifacts/local-only/v67-ranked/`). Each loss replay is decoded into a per-round timeline of every champion's
position, health, gold, gems, shards and actions (`tools/v67/c_timeline.mjs`, batch `tools/v67/c_timeline_batch.py`),
then audited by `tools/v67/c_forensics.py` (output `forensics_v67_losses.txt`, deaths `deaths_v67_losses.json`).
Individual deaths print round by round with `tools/v67/c_death_story.py MATCH ROUND CHAMP_ID`.

## 1. We die three times as often, and mostly by walking into fights we lose

Per lost game (140 losses):

| | Us | Winner |
|---|---:|---:|
| Deaths | 14.5 | 5.3 |
| Share of champion-rounds spent dead | 15.1% | 5.8% |
| Deaths walking toward enemies that outnumber us within 6 ("dive") | 5.1 | 1.7 |
| Deaths after fighting back ("traded") | 3.0 | 1.3 |
| Deaths fleeing without a hit | 2.6 | 0.8 |
| Deaths with no ally within 8 ("isolated") | 2.3 | 0.8 |
| Enemy shards / our side's shards around the victim | 3.0 | 1.35 |
| Victim at >= 60% health 8 rounds before death | 61% | 50% |

Melee divers die most: Vendetta 3.0 per lost game, Marcella 2.0, Cassi & Issac 1.8, Heart 1.5, Varg 1.5.
Before round 200 we already die 1.9 times per lost game against 0.9 (dives 0.8 vs 0.2) at equal shard counts.

Examples (`c_death_story.py`):
- 9d1d66a9 R516-530: our Vendetta (2 shards, 1,500 hp) walks alone toward four enemies while their Marcella (2,900 hp)
  follows behind it; dead in six rounds.
- 4dce9a6e R1530-1544: our Vendetta (2,500 hp) walks into four enemies including a 5,200-hp Vendetta while our hurt Heart
  and Ren retreat.
- 3f491cc4 R1531-1546 (01boss_battle): our team carries 1,166 gems (enough to win) behind a gated altar it never opens;
  our Heart holding 690 gems dashes into five enemies and dies; the bag goes to the enemy.

## 2. Where the code sends them in

Local death logs (v74 vs the proxy, a 12-turn ring with the verdict layer tagged: `artifacts/tmp/v67/v74-dl12c`,
`tools/v67/c_death_paths.py`), 1,463 deaths:
- 77% of deaths end in `flee`; the flee started with the enemy adjacent in 69% of them, with no ally within 4 in 66%,
  against a median 5.3x our health in view, after a `fight-champ` turn in about half.
- The verdict on the turn before a fatal flee: the formula said **winning while in danger** ("Fd") in 26% of all deaths.
  `winning = target_ttk * risk < min(ttd, 8) * aggression` (bot.cpp, handle_enemies): with aggression above 1 a champion
  accepts a damage race it loses (dies in 5 turns, kills in 7.5), and `winning` overrides `in_danger`.
- 42% of the fatal flee streaks entered from a fight were lone fights (no ally within 4) against at least twice our
  health.
- Neither verdict (enemy 6-8 tiles away): `handle_enemies` returns false and `farm()` / `hunt()` walk on toward the
  group. `hunt()` walks at any enemy sighting within 8 with no strength check.
- The outnumbered guard is off (`APEX_OUTNUMBERED 0`).

## 3. What the winners do differently

- Gold: in losses we trail from round 100 (244 vs 335 earned) to round 500 (1,472 vs 2,199); in wins we lead by the same
  margins. A gold lead at round 200 wins 73% of games, a deficit 33%. Two or more deaths before round 150: 40% wins.
- Same heroes, more income (all ranked games): their Marcella earns 1,749 gold per game to ours 1,226, Vesper 1,874 to
  1,192. Their Marcella opens with Treasure Shards of Focus; ours never buys Treasure.
- Gated altar (01boss_battle, v67 8/36 in this window): winners open the monolith gate at rounds 573-881 with 0-3 shards
  per champion in concentrated pushes (camp damage persists, so chipping adds up), then bank. We open it after round
  1,300 or never.
- Openings: on 00road_of_riches the winner cleared 23 camps by round 250 to our 14 (350 vs 770 gold at round 200),
  several in the same round at different places: they split into parallel squads; we farm as one group, walking 70-73% of
  the opening and hitting camps 8-12% of it (theirs 27%).
- Not a difference: shopping trips (we make fewer), bystanders at deaths, idle time on most maps.

## 4. What was tried (local, v74 base, fresh seed 23, 140 games per opponent)

| Change | proxy | v65 | v61 | v58 | Deaths |
|---|---:|---:|---:|---:|---:|
| V75_RACE 1.0: in danger, fight only a race we win | +11 | -60 | | | -1.3 to -1.8 |
| V75_LONE 2.0: no lone fight vs 2x our health | +31 | -33 | | | -0.8 to -1.3 |
| both | -13 | -61 | | | -1.0 to -2.5 |
| V75_LONE + V75_LONE_ALL (also when not fighting) | +4 | +13 | -54 | +32 | -0.5 to -1.7 |
| APEX_STAND 7 (stun-and-step, stand when cornered) | **-529** | **-523** | | | +7 to +9 |
| APEX_STAND2 3 (melee caught: hit home or stand) | **-347** | **-425** | | | +6 |

Every caution rule cuts deaths but not the local margin: our local league is our own lineage, which dives just as we do,
so the fights we skip were trades we won as often as we lost. Against the ladder, where the enemy around our deaths holds
3x our shards, the same rules are expected to pay; only ladder games can show it. Standing to fight is far worse: the
flee itself saves most champions, the deaths come from entering the fight.

## 5. Ladder tests (approved by the user 2026-10-28)

Top-12 duel plan `research/v59/duel_top1.json` (24 groups, 120 games), `research/v75/DUELS.md`:
v67 17/120 (-444), **v74 30/120 (-302; +142 +/- 54 over v67)**, v75 = v74 + lone guard 21/120 (-393; -91 +/- 54 vs
v74). The per-map work in v70-v74 transfers to the top teams; the caution rule does not. v74 is live (platform 68).

## 6. Against the top 12 (the 103 losses of the v67 duel arm, `forensics_duel_v67.txt`)

Same picture, stronger: deaths 14.6 vs 4.4, dives 5.1 vs 1.2, shards 24 vs 38 at round 800. Two kinds of top team:
- Killers (Intercontinental Fish 9.4 of our dives per lost game, prism best girl 8.8): fights decide.
- Farmers (hello, print dont int: they kill us only ~10 times, 2 dives): by round 500 they earned 2,750 / 2,592 gold to
  our 1,671 / 1,540 and banked 2.5x as much. In the first 500 rounds they spend 2-3% of champion-rounds dead (us 9-10%),
  6-17% idle (us 13-17%) and 23% hitting camps (us 17-19%).
v74's own first 500 rounds locally (`tools/v67/c_modes.py`, APEX_MODESTATS): approach 34%, camp fights 16%, waiting
for a respawn 11%, champion fights 7%, capture 5%, flee 5%, staging 5%; each champion abandons a still-alive target 10
times. Round 5 profiles (wait / nowait / solo / spread / shop / calm per map, `research/v75/knob_table_r5x.json`) target
that time; validated as bots/v76.

v74 against the top 12 (90 duel losses, `forensics_duel_v74.txt`): deaths 14.6 per lost game and dives 5.0, the same as
v67; its gain was economy (team shards at round 800: 30 vs v67's 24; top teams 38).

Round 6 (all 31 profiles, best per map on seeds 26-28; 35 maps switched, in-sample +124) gave bots/v77, which on fresh
seeds 32/33 is no better than v76: v65 -48, v61 -5, v58 +14, proxy +29 (all CIs span zero). Best-of-31 per map picks
noise; per-map knob profiles are exhausted. v76 remains the best unsubmitted candidate.
