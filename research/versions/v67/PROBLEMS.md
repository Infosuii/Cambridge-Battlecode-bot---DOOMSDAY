# Why our lineage loses: measured problems (2026-10-27)

Evidence, unless noted:
- the 120 ladder duel games of v65 against the top 12 (`research/proxy/ladder_arms.json`, arm v65);
- their native summaries (`artifacts/local-only/duels/<match>.json`);
- their replays' per-round fight rows (`artifacts/local-only/proxy/style-ladder.jsonl`, from
  `tools/proxy/fight_style.mjs`).

Medians are over games.

## 1. Champions cannot coordinate: they don't know where their teammates are

- The API shows an allied champion only inside your own vision (measured in replays: about 80% of ally lookups
  fail).
- v65's 8-byte shared memory holds 6 camp-claim slots (8 bits each, plus "on site" and fight-order codes) and one
  enemy sighting (`bots/v65/src/bot.cpp` `write_claim`, `share_sighting`). It never holds teammates' positions or a
  team target.
- So every "fight with numbers / regroup / focus" rule in v65 is a per-champion guess. You cannot fight as a group
  when nobody knows where the group is.

## 2. Items: we buy passives, they buy raw stats

| Share of all shards bought | v65 | Top teams |
|---|---:|---:|
| **Bruiser** (5 of a stat + 1 of each other per emblem: about 40% more stats than a passive emblem) | **3%** | **63%** |
| Greed (an emblem needs 25 shards = 750 gold) | 28% | 0% |
| Prospector | 16% | 1% |
| Jungle | 14% | 8% |
| Durability | 13% | 7% |
| Monster | 10% | 3% |
| Capture | 9% | 1% |
| Collectors | 6% | 1% |
| Treasure | 0% | 8% |
| Power | 0% | 6% |

- v65's plan (`V58_ITEM_PLAN` in `bots/v65/src/bot.cpp` `build_for`) is six different passive emblems (900 gold),
  then Greed in 25-shard stacks.
- The 5th shard comes later: median round 505, against 425 for the top teams.
- Gold is spread more evenly: the top champion's share of team gold is 0.31, against 0.40.
- Caution: the proxy (v65 logic with the top teams' item orders) got *weaker* (v65's margin +298 → +197 without
  them). v65's farming logic assumes its passives (Jungle for tanking camps, Monster for camp damage). Items have to
  change together with how the team plays.

## 3. The economy gap opens in the mid game, through deaths, not early farming

| Team totals (v65 / top) | R100 | R250 | R500 | R1000 | End |
|---|---:|---:|---:|---:|---:|
| Earned gold | 276 / 308 | 758 / 938 | 1,658 / 2,248 | 3,042 / 5,398 | 3,466 / 6,616 |
| Gems collected | 34 / 47 | 97 / 148 | 236 / 362 | 628 / 978 | 726 / 1,053 |
| Camp damage dealt | 6.2k / 6.7k | 14.0k / 16.8k | 31.5k / 38.9k | 62k / 83k | 69k / 105k |
| Deaths | 0 / 0 | 2 / 1 | 5 / 2 | 10 / 4 | 12 / 4 |
| Kills | 0 / 0 | 0 / 1 | 1 / 3 | 3 / 8 | 3 / 10 |
| Champion damage dealt | 0.9k / 1.6k | 2.4k / 4.5k | 5.8k / 10.5k | 11.9k / 24.9k | 13.4k / 29.1k |

- Farming is close for the first 250 rounds.
- After that v65 keeps dying, and the gap grows: half the champion damage dealt, a third of the kills.
- Gems lost to enemy champions: **91 a game against 19.5**.
- Smaller bank trips: 24 gems per tribute against 35.

## 4. v65 is killed at home, alone and outnumbered

- **Where:** 1,149 v65 deaths happen in its own half and 570 in the enemy half; 207 of them within 6 tiles of its own
  spawn. Top teams die 441 times in their half and 354 in ours. The top teams invade, and v65 dies farming its own
  side.
- **In the 5 rounds before death:**

  | Measure | v65 | Top teams |
  |---|---:|---:|
  | Own HP (% of max) | 39 | 31 |
  | Friends within 5 | 1.69 | 2.06 |
  | Alone (no ally within 8) | 35% | 21% |
  | Local HP ratio (ours / theirs) | 0.60 | 1.10 |

  v65 dies outnumbered and alone. The top teams die in even fights.
- **Deaths in chains** (another teammate died within 10 rounds): 19% for v65, 14% for the top teams.
- **Death causes:** 1,553 to champions and 166 to camps (top teams: 677 and 118). It is the champions.

## 5. Map by map (all 6 ladder arms, 720 games)

- **We lose almost every map.** Only `00packs` (16/18), `02stalactites` (8/12), `00gem_fields`, `00ambush`,
  `00pilgrimage` and `00vault` are positive. The gap is general, not a few bad maps.
- **The worst maps lose by −750 to −1,000 every time:**
  - gem-fight/gem-combat maps: `00ribs`, `00gemfight`, `adgato_gemcombat3/5`, `01starvation`;
  - big-camp or contested maps: `00crater`, `01starfish`, `00road_of_riches`, `00the_line`, `00galaxy`, `02arena`,
    `00stampede`.
- **Hardest opponents** (v65's margin): Intercontinental Fish −798, prism best girl −705, Mite −527, Trzy Kwaterki
  −525.

## 6. Why fixes didn't work (process)

- **Fixes were layered** onto about 1,000 lines of fight switches and economy assumptions, so each was absorbed or
  cancelled. v62c cut deaths and farmed less, so it gained nothing.
- **The winners' behaviours only work as a package:** grouping + focus + burst + raw-stat items + picking fights.
  Tested one at a time, each piece looked neutral or negative (the Claudus copies lost −52 to −217 locally; the item
  copy lost about 100).
- **The tests couldn't see real gains.**
  - Self-play rewards beating our own habits: v58 +153 and v66a +52 locally, nothing or worse on the ladder.
  - A 120-game ladder duel has a standard error of about 50 gems; only 1 of 15 version pairs differed clearly.

## What this implies for v67

1. **Team knowledge first.** Use shared memory for teammates' positions (coarse, 10 bits each: see the mimic
   protocol), a team target and a rally point. Then fight and defend as a group, especially in our own half where
   we are invaded.
2. **Raw-stat items** (Bruiser / Power, one stat per carry, about 40% of gold on the carry). Pair them with a
   fighting playstyle; don't bolt them onto v65's passive-based farming.
3. **Pick fights by local HP and damage ratio** (we die at 0.6; they fight at about 1.1). Never stay alone when
   enemies are near. Leave or regroup instead of being chased down. Don't carry big bags through enemy-visible
   areas: bank more often or protect the carrier.
4. **Measure the mechanisms each change targets** (deaths, kills, gold at R500/R1000, gems lost to champions)
   against opponents outside our lineage, as well as wins.
