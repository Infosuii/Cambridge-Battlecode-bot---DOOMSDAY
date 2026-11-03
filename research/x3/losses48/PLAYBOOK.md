# Strategy playbook: map categories x strategies learned from the teams that beat us (3 Nov 2026)

## 1. How the system works (works on unseen maps)

1. **Map features from the bot's own world model** at game start (`bots/x3/src/x1_atlas.h`): size, team size,
   group count, gems, blocked share, jackpot / top-3 share, harmless / strong-camp share, own / contested / enemy-side
   gem shares, gems within 15 / 30 steps, unreachable share, nearest and mean group distance, altars, camp health per
   gem. Offline values come from the bot's own print (`X1_ATLAS`, `tools/mapatlas/collect.py`): 86/86 maps match the
   bot's fingerprints exactly.
2. **Category** by a depth-3 tree on those features (`tools/mapatlas/categorise.py --source bot`, generated C++
   `x1_categories.h`; runtime check: 28/28 games classified as offline). Categories (`research/x3/atlas/CATEGORIES.md`):

| Category | Maps | Rule | Plainly |
|---|---|---|---|
| C1 | 18 | small; mean group distance <= ~22 steps; fighting camps | small, close, contested farm |
| C2 | 4 | small; close; > 62% of gems in harmless camps | small peaceful race |
| C3 | 24 | small; spread; < 17% harmless | small, spread, dangerous camps |
| C4 | 13 | small; spread; some harmless | small, spread, mixed |
| C5 | 21 | large; dangerous camps; most gems beyond 30 steps | large, expand far |
| C6 | 3 | large; dangerous; gems near home | large, rich home |
| C7 | 3 | large; mostly harmless | large peaceful |

3. **Strategy profile per category** (`x1_portfolio.h`, `X1_PORTFOLIO`): profiles and the category -> profile table
   are data; test builds force one profile everywhere (`X1_PORTFOLIO_FORCE`, bots `pf1`..`pf7`).

## 2. What the teams that beat us did (last 48 h, rated >= 2000)

898 distinct losses (459 ranked, 439 unranked) to 40 teams on all 86 maps (`tools/ladder/losses_recent.py`,
`summary_profile.py`, `archetypes.py`; first 294 analysed so far, all 898 pending). Consistent across categories:

| | winners | us, same games |
|---|---|---|
| wards placed per game | 80-170 | 40-90 (about half, every category) |
| first deposit (round) | 90-230 | 70-600 (later in 5 of 7 categories) |
| deposits per game | 15-38 | 6-38 (1.4-2.5x fewer in most) |
| Bruiser shards by round 300 | 3-12 | 0 |
| Treasure opening | 10-40% of games | 0% |
| teleport crystals | 1-4 | 1-10 (we buy more) |
| first kill (round) | earlier in 5 of 7 categories | |

Archetypes (k-means on 24 strategy features; overlapping tendencies, silhouette ~0.08):
- **Raid and bank** (31%): 23% of their gem pickups on our half (us 10%), 22% / 19% of mid / late clears on our
  half (us 10% / 6%), 39 deposits a game (us 22).
- **Treasure opening** (22%): 88% open with a Treasure emblem (+10% gold); we open Jungle 86%.
- **Hoarder** (5%): first deposit ~round 1100, 188-gem deposits.
- **Bruiser + altar locks**: Bruiser first, 7.6 locks a game.
- **Balanced, slightly more on our side** (the rest).

## 3. Strategy profiles (first set)

| Profile | Name | Rules |
|---|---|---|
| 0 | v92 | unchanged |
| 1 | Vision | spend every ward charge on scouting wards: furthest unwatched tile towards the enemy, near our target group, bushes preferred (`ward_vision`) |
| 2 | Raid and bank | vision; from round 300 enemy-half camps at 0.7 value; raider on; bank at 0.75x bag |
| 3 | Stat fighter | vision; Treasure + Bruiser item plan; engage only with a numbers edge; focus fire |
| 4 | Early bank | vision; bank at 0.6x bag until round 400 |
| 5 | Top-team economy | vision; Treasure / Jungle / Bruiser / Power opening; bank at 0.8x bag |
| 6 | Fortress | vision; own half only; aggression 0.8; bank at 0.7x bag; antifeed |
| 7 | Push | vision; invade from the start; aggression 1.2; hunt +2; Bruiser; numbers; focus |

## 4. Test plan

- Local: crash / fault / fuel check of pf1..pf7 (14 maps x 2 sides vs v92).
- Ladder duel plan `research/x3/duel/duel_20261103b.json`: the 12 teams rated >= 2000 that beat us most in 48 h
  (0xDEADBEEF, QS2isLaw, an iq too high, we were fed fish, Shawarma, Nameless, bbas, 剑桥夜爬者, Beehive, will
  think later, smurphy, EggsAfter11AM), 2 groups each, 64 maps. Arms: v92, pf1..pf7, v92 again (drift check).
- Per category: each profile's paired result vs v92 on that category's maps; the category table takes the best
  profile where it clearly beats v92, else v92. Then one portfolio arm (category table) on a fresh plan.

## 5. Local check of the profiles (14 maps x 2 sides vs v92; v92 vs itself = 14 / 28)

| profile | wins / 28 | faults | fuel-outs | deaths / game |
|---|---|---|---|---|
| 1 vision | 11 | 0 | 34 | 13.5 |
| 2 raid and bank | 8 | 0 | 38 | 15.7 |
| 3 stat fighter | 10 | 0 | 28 | 14.0 |
| 4 early bank | 9 | 0 | 34 | 13.5 |
| 5 top-team economy | 10 | 0 | 34 | 16.1 |
| 6 fortress | 9 | 0 | 26 | 12.9 |
| 7 push | 8 | 0 | 29 | 17.4 |

No faults; fuel normal. Every profile is below even against v92 in self-play (v92 is tuned against its own play),
which self-play cannot tell apart from ladder value; the ladder duel (plan b) decides.

## 6. Archetypes on all 898 losses (k = 9; research/x3/losses48/ARCHETYPES.md)

| archetype | losses | signature (them vs us, same games) | counter idea |
|---|---|---|---|
| Our-half killers | 244 | 63% of their kills on our half (ours 29% on theirs) | vision (wards), group up at home, no lone walks |
| Treasure openers | 163 | 87% open Treasure, 13 Treasure shards by 300; first kill round 250 (ours 557) | earlier stats, punish their greedy opening |
| Raiders | 126 | 20 / 26 / 32% of clears on our half early / mid / late (us 11 / 12 / 10%); 36 deposits (us 16) | defend home groups, counter-raid, bank more |
| Contested farmers | 122 | 58% of early clears in the contested middle | contest the middle early with numbers |
| Pacifist racers | 80 | no kills (first kill ~1740); they out-farm us | pure farming speed, early banking |
| Bruiser openers | 64 | 15 Bruiser by 300, more early deposits, altar locks | numbers edge, avoid even fights early |
| Hoarders | 54 | first deposit ~950; 256-gem deposits (us 48) | hunt their loaded carriers (killer takes the bag) |
| Early brawlers | 32 | 3.8 kills by 300 | fortress until stats, then fight |
| Power invaders | 13 | 10 Power by 300; 31% of pickups on our half (us 1%) | defend, vision |

Second axis next to the map category: the opponent's style. If it shows in their draft (visible after the draft)
or in early sightings, the bot can switch to the counter profile.

## 7. What the replays add (all 898 losses; research/x3/losses48/REPLAY_FINDINGS.md)

| | winners | us |
|---|---|---|
| time on own half, rounds 0-150 -> 800+ | 0.83 -> 0.70 (they expand steadily) | 0.86 -> 0.83 (we stay home) |
| grouped in the opening (ally within 4, rounds 0-150) | 68%, nearest ally 4.6 tiles | 57%, 5.8 tiles |
| allies at first contact (same round, ~90) | 2.1, health 0.89 | 1.7, health 0.85 |
| champions working a camp together | 1.72 | 1.44 |
| recalls | 20-30% more | |
| clears 400-800 / 800+ | 19 / 17 | 16 / 11 |

Per category the late game is where it breaks: C1 own half after round 800 0.68 vs 0.92 and late clears 22.5 vs
9.8; C4 late clears 23.4 vs 7.3; C7 they are on our half from the start (0.62 vs 0.88). We sit on a farmed-out half.

New profiles from this: 9 progressive expansion (enemy-half value ramps from base at round 300 to full by 900),
10 pack opening (cohesion x4 until round 250), 11 pack + expand + vision light. Profile 1 (vision, ward + world
update) lost 47-57 on the ladder; profiles 2-7 now run without vision; profile 8 is vision light (spare fuel, no
extra update).

## 8. Ladder duel b so far (vs v92 57 / 120 on the same plan)

| profile | wins | v92-only / profile-only games | z |
|---|---|---|---|
| 1 vision | 47 | 24 / 14 | -1.62 |
| 2 raid and bank | 47 | 22 / 12 | -1.71 |
| 3 stat fighter | 42 | 26 / 11 | -2.47 |

Every change so far (two batches) lands 5-15 below v92. Either v92's balance breaks under any change, or opponents
updated their bots between arms (the duel did not pin them). From profile 5 on, each arm pins every opponent's bot to
the one it ran in v92's base group (`--source-group`, tools/replay/ladder_duel.py); the v92 re-run (also pinned)
checks that the pinning reproduces the base exactly. Profiles 1-4 get pinned re-runs if opponents drifted.

## 9. A machinery bug, found and fixed (3 Nov ~19:20 UTC)

Every portfolio build ran the map analysis on round 1, on top of v92's own heavy first turn: 30 fuel-outs in 28
games against v92's 6 (24 of them in round 1), even with profile 0 (v92's own play). Fix (e5031161): the analysis
runs on the first turn from round 3 with 70k fuel left (it costs 12-54k); fuel-outs back to 6, profile 0 = 14 / 28
like v92. The ladder arms of profiles 1-4 (and the unfinished combo arm) carried the bug; all profiles are re-run
on plan c (`research/x3/duel/duel_20261103c.json`: plan b's groups and v92 base, opponents pinned), order: 13 pack
play, 4 early bank, 10 pack opening, 9 progressive expansion, 8 vision light, 2, 3, 1, 5, 6, 7, 11, 12, v92 re-run.

Pack play (profile 13) behaviour check (28 local games vs v92, our team's replay metrics):

| metric | v92 | pack play | winners (loss replays) |
|---|---|---|---|
| grouped, rounds 0-150 | 0.60 | 0.71 | 0.68 |
| grouped, rounds 150-400 | 0.48 | 0.58 | 0.54 |
| nearest ally, early | 5.9 | 4.5 | 4.6 |
| champions working a camp | 1.40 | 1.61 | 1.72 |
