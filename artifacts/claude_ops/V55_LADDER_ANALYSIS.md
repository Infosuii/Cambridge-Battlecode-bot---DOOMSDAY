# Why platform v55 loses on the ladder

Claude Code, 2026-10-25. Every v55 game from its upload (18:53:28 UTC) to 19:54 UTC: **210 games, 112-98**. All 210
replays decoded (local-only, `artifacts/local-only/v55-ladder`); tables in `V55_LIFE_DATA.md`, rows in
`V55_LIFE_DATA.json`; listing `data/ladder/v55_games_20261025.json`. Offline omniscient analysis, descriptive.

## 1. The record is two different stories

| Opponent | Kind | v55 W-L |
|---|---|---:|
| **Claudus Maximus (rank 4)** | unranked, 10 queued groups covering 25 maps × 2 | **1-49** |
| everyone else | ranked | **22-8** |
| everyone else | unranked | 89-41 |

Against the field v55 wins 69% (ranked 73%). The unranked losses are mostly one top-5 team. Of the other 49
losses, the main opponents were Turbo Gold Clusters (8), Electric Tributers (7), Rogue Elk (7) and Velvet
Tributers (6).

## 2. Against Claudus Maximus: out-farmed, then out-fought

Medians over the 49 losses, us | Claudus:

| | Us | Claudus |
|---|---:|---:|
| equipment R100 / R250 / R500 | 180 / 510 / 1230 | 240 / 1050 / 3000 |
| capture gold per champion R250 / R500 | 112 / 240 | 241 / 614 |
| gold per attack/cast round R500 | 2.9 | 4.8 |
| camp-attack share of alive time R250 | 0.16 | 0.24 |
| gems from 20+-gem captures by R500 | 70 | 229 |
| respawn-wait champion-rounds by R500 | 89 | 86 |
| champion-rounds dead | 756 | 243 |
| deaths | 13 | 4 |
| P(die within 5 rounds in contact) | 0.080 | 0.023 |
| enemy hp lost per contact round | 31 | 59 |
| completed banks / median bank | 10 / 18 | 30 / 28 |
| ward placements | 43 | 111 |
| median margin | −826 (games end ~R979) | |

Claudus drafts Vesper + Vendetta + Heart in every game (plus Marcella/Tavi or Ryth); our drafts are Ryth/Vendetta/
Marcella/Ren/Varg or Prism/Cassi variants with no Vesper. They double our capture income by R250, attack camps 50%
more of the time, earn 65% more gold per attack round, and then win the fights (twice our damage per contact round,
a third of our death rate). Dead-camp waiting is **not** the difference here.

## 3. Against the rest of the field (49 losses)

Same direction, smaller gap: equipment 510 vs 870 at R250 and 1410 vs 2280 at R500; capture gold per champion R500
324 vs 476; gold per attack round 2.8 vs 4.1; big-capture gems 80 vs 201; **respawn waits 94 vs 33**; deaths 7 vs 4;
damage per contact round 32 vs 53; wards 57 vs 243. Time allocation is similar (camp attacks 0.21 vs 0.24). In our
111 wins over the same teams, the signs reverse (capture gold 455 vs 290 at R500, deaths 3 vs 14).

## 4. Ruled out

* **Enemy altar locks.** Winners place 2-5 locks per game against our 0-1, but our tribute completion is 95-96%. We
  bank less because we start fewer tributes (14 vs 32 against Claudus), i.e. we make fewer gems.
* **Missing Treasure.** v55 buys Treasure first. Earlier tables suggesting otherwise were partly an analysis bug,
  fixed today: `actor_ledger.mjs` ignored purchases made while dead (dead champions shop), which hid emblems and
  delayed "first purchase" for both teams. In losses our Treasure still completes late because our gold arrives
  late (median 0 champions with Treasure at R250 vs 2 for winners; 2 vs 1 in our wins).

## 5. What would move these games

1. Income rate per champion before R250: draft and farming (gold per attack round 2.8-2.9 vs 4.1-4.8). The
   opponents' Vesper/Heart core is the largest visible difference; a forced-Vesper draft failed before without a
   supporting economy, so this needs the coupled draft + reward-ownership approach.
2. Dead-camp waiting against ordinary teams (94 vs 33 champion-rounds by R500).
3. Survival when out-geared (3.5× our death rate per contact against Claudus): disengage earlier from stronger
   local groups.
4. Gem production: big-camp gems are a third of the winners' in every cohort.

## 6. Update: full Claudus series and camp-clearing analysis (20:16 UTC)

A further 30 Claudus games (0-30) completed the series: **1-79 over all 40 maps, both sides** (listing
`data/ladder/v55_games2_20261025.json`). `tools/replay/camp_clear.mjs` measures solo camp clears per team:

| Clears per game (gems) | Own half | Middle | Enemy half |
|---|---:|---:|---:|
| Claudus | 26.4 (383) | **14.4 (455)** | 4.7 (69) |
| us vs Claudus | 23.9 (251) | **7.9 (117)** | 1.5 (17) |
| winners vs us (other teams) | 26.4 (467) | 13.6 (321) | 4.7 (100) |
| us in those losses | 30.7 (442) | 10.2 (201) | 3.2 (45) |
| us in our wins | 31.3 (441) | 15.5 (336) | 5.6 (110) |

* While engaged with a camp, attack use is identical (0.62 vs 0.63): the controller does not waste turns at camps.
* Camp damage per engaged champion-round is 23% lower against Claudus (88 vs 115), 12% lower against others.
* Solo elk clears cost the same (40% of max health, 1-2% deaths), so the soak model is not blocking them.
* The middle is where games are decided. `UB_ENEMY_CAMP` 0.6 (a 40% value cut for camps an enemy was seen near)
  ceded it; v57 sets it to 1.0 (`bots/v57/CHANGES.md`).
* Remaining dead-camp waiting concentrates on disconnected maps (islands, big-world) and yellow-brick-road, mostly
  champions without a dash; crystal crossing was tried and rejected (islands −345 to −414).

