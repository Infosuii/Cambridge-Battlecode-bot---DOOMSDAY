# Game mechanics and win conditions (engine 2.0.0, CLI 4.0.0)

Evidence labels used in this document:
- **[ENGINE]** — engine metadata read at runtime through the official SDK (`research/misc/SPRINT3_SDK_FACTS.json`, probed 2026-10-26).
- **[SDK]** — the C++ SDK header `sdk/cpp/cambc.h`.
- **[RULES]** — `game rules/GameRules.md`. This is the published text and is *older than the engine* in several places.
- **[REPLAY]** — inferred from saved local or ladder replays.
- **[OPEN]** — unverified. Each one names a cheap diagnostic to run in the implementation phase.

Where the documentation and the engine disagree, the engine wins. **The bot must read champion, item and camp
metadata at runtime and never hard-code the numbers in GameRules.md.**

## 1. Victory

- **Immediate win.** The first team to *tribute* 1000 gems wins on the spot ([ENGINE] `winning_gems` 1000).
- **Round 2000 tiebreak.** If neither team has won by round 2000 ([ENGINE] `max_rounds`), compare in order:
  1. tributed gems
  2. lifetime gold earned (not the gold left to spend)
  3. champion kills

  If all three tie, Team B wins ([RULES]).
- **Carried gems do not count.** Only tributed gems score. When a champion dies its bag goes to the killer, or is
  destroyed if a camp landed the kill.

Implications:
- The game is a **race to 1000 banked gems**. Collected-but-unbanked gems are an asset at risk. Gold has value only
  through what it buys, except in a round-2000 tiebreak.
- Banked margin decomposes exactly as `banked = collected − lost − carried` (deep analysis, E9). Income accounts for
  77.5% of our mean loss deficit, bag losses for 17.8%.
- Late in the game the right objective changes:
  - Close to 1000 gems, time-to-1000 is what matters, so bank now, protect carriers and lock enemy altars.
  - In a round-2000 finish, lifetime gold is the second tiebreak, so kill gold and Vesper gold matter at the margin.

## 2. Turn and round structure ([RULES] verified by replays)

**Round start**, in this order:
1. camp respawns
2. spell and ward updates
3. **camp captures**
4. camp turns: awake camps attack the nearest champion in range

**Then champion turns** alternate between teams, and the starting team swaps every round. Within a team, higher
priority acts first. `set_priority` takes effect from the next round; ties fall back to draft order. Dead champions
still get a turn (to shop).

**Inside a champion's turn:**
- **Allowances.** One ordinary move, one basic attack and one successful ability cast (across both slots).
  - Ranged champions can either move or basic-attack in a turn, not both. Damaging ranged spells marked "excludes
    walking" also consume the move.
  - Melee champions can move and attack in the same turn.
  - Attack-reset abilities restore the attack allowance.
- **Channels.** Recall, tribute and the teleport crystal tick at the owner's turn end and complete at the next turn
  start once the timer has reached zero.
- **Blocked moves.** A move into an unseen occupied tile returns `false`, costs no allowance and reveals the tile for
  the round.
- **Fuel.** C++ gets 100k fuel per turn: 10× on the first draft turn and 2× on the first play turn. **Running out of
  fuel suspends the bot**, which resumes from that point on its next turn ([RULES]). Unused fuel does not carry
  over.

## 3. Champions: engine values ([ENGINE], with the [RULES] value where it differs)

| Champion | HP (+/shard) | Str (+) | Focus (+) | Range | Slot 0 | Slot 1 | Passive | Docs differ |
|---|---|---|---|---|---|---|---|---|
| Ryth | 1200 (+100) | 45 (+4.5) | 100 (+10) | 1 | area stun 1×F r1 @4 | reset | +1% bonus HP as Str | str growth 5 |
| Vesper Vale | 1000 (+100) | **45** (+5) | 100 (+10) | 3 | reset | dash 2 | +33% gold | **base str 55** |
| Vendetta | 1000 (+100) | 70 (+6) | 100 (+10) | 1 | reset | dash 2 | kill resets cooldowns (camps too) | — |
| Cassi | 600 (+65) | 30 (+3) | **100** (+13) | 3 | 2×F nuke @4 | 1-round stun @4 | shares fate with Issac | **focus 70** |
| Issac | 900 (+80) | **45** (+3) | 100 (+10) | 1 | reset | dash 2 | shares fate with Cassi | **str 40** |
| Stellar | 650 (+65) | 30 (+3.5) | 70 (+**8.5**) | 3 | 2×F nuke @4 | 1.4×F AoE r1 @4 | — | focus growth 7 |
| Prism | 700 (+**65**) | 35 (+2.5) | 80 (+8) | 3 | 1.5×F nuke+stun @4 | 1×F AoE r1 @4 | +1.5 focus per carried gem | HP growth 60 |
| Marcella | 1200 (+100) | 45 (+**4.5**) | 60 (+**14**) | 1 | enhanced reset (next hit stuns) | 2×F nuke @4 | stun-immune; +2 gold per tributed gem | str growth 5, focus growth 15 |
| Willow | 700 (+50) | 55 (+3) | **140** (+5) | 3 | heal ally 3×F @4 | reset | — | **focus 120** |
| Ren | 900 (+100) | 35 (+5) | 100 (+9) | 1 | **1.1**×F nuke+stun @4 | dash 2 | retaliates 0.2×F | **0.75×F** |
| Varg | 1000 (+100) | **45** (+5) | 100 (+10) | 1 | reset | shield 2.5×F 5 turns | splash = Str in r1 | **str 40** |
| Tavi | 900 (+75) | 45 (+5) | 110 (+10) | 3 | reset | **1.6**×F nuke+stun @4 | buys shards anywhere; sells at spawn | **1.4×F** |
| Heart of Ruin | 1000 (+100) | 30 (+3) | 100 (+12→**10**) | 1 | shield 1.5×F | dash 2 + 1.5×F r1 stun on landing | up to +50% damage at low HP | focus growth 12 |

Every champion has vision 8 and moves one tile per turn. All abilities have an 8-turn cooldown. Team size is 3–5
depending on the map.

## 4. Camps and capture

**Camp table:**

| Camp | HP | Str/round | Range | Gold | Gems | Respawn | Gems per 1k HP | Gold per 1k HP |
|---|---|---|---|---|---|---|---|---|
| Wolf | 1350 | 20 | 3 | 40 | 4 | 40 | 3.0 | 30 |
| Elk | 2400 | 60 | 4 | 90 | 15 | 60 | 6.3 | 38 |
| Golem | 5000 | 120 | 4 | 160 | 36 | 80 | 7.2 | 32 |
| **Gem cluster** | **120** | 0 | – | 0 | **7** | 50 | **58** | 0 |
| **Gold cluster** | **120** | 0 | – | 20 | 0 | 50 | 0 | **167** |
| Monolith | 20000 | 200 | 5 | 300 | 200 | 150 | 10 | 15 |

HP, strength and range are [ENGINE]. Rewards and respawn times are [RULES]; they are consistent with the reward
values observed in replays.

**Capture rules:**
- **Groups.** Cardinally connected camps form a group. Rewards combine over the whole group, and respawn uses the
  longest member timer.
- **Waking and sleeping.** Damage wakes the whole group. An awake camp attacks the nearest champion in range every
  round. Camps do not chase. After **2** rounds with no champion in range ([ENGINE] `camp_sleep_time`), the group
  sleeps again.
  - [OPEN] Whether a sleeping, damaged camp regains HP. Diagnostic: damage an elk, leave for 10 rounds, re-observe its
    HP. It decides whether partial clears can be resumed.
- **Capturing.** After every member of a group dies, a team must stand on one of the group's tiles, uncontested.
  - The capture timer starts at a capture phase and counts down over later phases: 5 rounds ([ENGINE]
    `capture_time`), or **3 with a Capture emblem**.
  - An empty or contested region resets progress.
  - Extra allies do not make it faster. The **reward is split among allies present**, with the remainder going to
    the lowest ID.
  - A team cannot capture a region one of its own champions is not standing on, and an enemy on the region resets
    the timer.
- **Respawn.** The group respawns after its reward is claimed, using its longest member timer. Any occupied spawn
  tile delays the respawn of the entire group (denial lever).

**Two economic classes of objective.** This is the most important economic consequence of the rules.

1. **Damage-bound camps** (wolf, elk, golem, monolith).
   - Cycle time ≈ travel + HP / crew DPS + capture.
   - Crews add DPS but not capture speed.
   - Camps also deal damage back (`str × rounds alive`), which costs HP and therefore recall time.
2. **Capture-bound clusters** (gem and gold clusters, 120 HP).
   - Cycle time ≈ travel + 1 + capture.
   - One champion is optimal: a second only splits the reward.
   - A **Capture emblem (5 → 3 rounds)** cuts cluster cycle time by up to 40% of the non-travel part.
   - **Prospector** raises gem-cluster yield by 25% ([REPLAY], §6).
   - Clusters deal no damage, so they never force a recall.

**Worked rates** (engine stats, a representative early crew, travel 10 rounds per leg; gem-equivalents GE = gems +
0.2·gold for illustration):

| Objective | Crew | Clear | Champion-rounds | Reward | GE per champion-round |
|---|---|---|---|---|---|
| Elk (single) | 3 champs, ~180 DPS | 13.3 | 3·(10 + 13.3) + 5 ≈ 75 | 15 gems + 90 gold | **0.44** |
| Golem (single) | 3 champs | 28 | 3·(10 + 28) + 5 ≈ 119 | 36 + 160 | 0.57, but takes 120 × 28 ≈ 3360 damage, so not feasible without Jungle or rotation |
| Wolf | 2 champs, 120 DPS | 11 | 2·(10 + 11) + 5 = 47 | 4 + 40 | 0.26 |
| Gem cluster | 1 champ | 1 | 10 + 1 + 5 = 16 | 7 gems | **0.44** |
| Gem cluster + Capture + Prospector | 1 champ | 1 | 10 + 1 + 3 = 14 | 8 gems | **0.57** |

Conclusions:
- Clusters are as productive per champion-round as elk, but they are **solo, safe and capture-bound**.
- A strong economy separates *crews on damage-bound camps* from *solo cluster circuits*.
- Respawn timers (50 for clusters, 40–80 for camps) make the right model a *periodic* routing problem: a team
  orienteering problem with time windows that recur ([EXTERNAL_RESEARCH.md §5](EXTERNAL_RESEARCH.md)).

## 5. Gems, altars and banking

- **Tribute.** Stand within Chebyshev distance 1 of an altar ([ENGINE] `submit_gems_range` 1) holding at least one
  gem. Tribute takes `max(1, ceil(0.1 · bag))` owner turn ends ([ENGINE] multiplier 0.1, minimum 1). Completion
  banks the **whole current bag**, including gems captured meanwhile.
- **What interrupts a tribute.** Damage does **not**. A stun, death or a new altar lock does.
  - Marcella is **stun-immune**, so only death or a lock can stop her tribute. She also earns +2 gold per gem
    tributed.
  - This is a mechanical reason for Marcella's 84% pick rate among the opponents who beat us (deep analysis).
- **Altar lock** (10 gold consumable).
  - Placed on an altar within 2 tiles. It blocks enemy tributes and cancels their tribute channels at that altar.
  - Removing it takes 5 basic attacks ([ENGINE] `altar_lock_hits`). An enemy tribute attempt against it becomes an
    attack on the lock.
  - Top teams place 2–5 per game; we place 0–1 (v58 findings).
- **Banking is an optimal-stopping problem** (the burglar problem, [EXTERNAL_RESEARCH.md §6](EXTERNAL_RESEARCH.md)).
  Carry while the expected loss from carrying, `bag × hazard × time`, is below the cost of the bank trip.

## 6. Gold, items and equipment ([ENGINE], [SDK])

**Purchasing:**
- A shard costs 30 gold and adds the champion's growth value for its stat.
- Five matching shards combine into an emblem (150 gold). **Only the completed emblem grants the passive**, and a
  second emblem of the same family adds no further passive.
- Buy on your own spawn tiles or while dead. Tavi can buy shards anywhere.
- Consumables cost 10 gold, and a champion may carry one of each.

**Emblem families. The engine has 14 families; the published rules list 7.**

| Family | Engine passive (magnitude) | Meaning | Status |
|---|---|---|---|
| Monster | 0.15 | +15% damage to camps (rules say 10%) | [SDK] comment |
| Power | — | counts as 6 shards | [SDK] |
| Durability | 0.10 | −10% incoming damage | [SDK] |
| Treasure | **0.10** | **+10% gold** (rules say 20%; "nerfed" in Sprint 3) | [SDK] comment |
| Jungle | 0.30 | −30% damage from camps | [SDK] |
| Home | 0.5 | recall takes 3 turn ends instead of 5 | [SDK] |
| Bruiser | — | 5 of the stat plus 1 of each other | [SDK] |
| **Tribute** | 0.33 | [OPEN]: probably tribute speed or bonus. Diagnostic: tribute 40 gems with and without it, compare channel length and gems/gold credited | v76 computes it but never uses it |
| **Capture** | 3 | capture takes **3 rounds** instead of 5 | v76 assumes this; [OPEN] confirm once |
| **Prospector** | 0.25 | **+25% gems from gem clusters, floored**. Over 9,196 SA-IDLE-v76 capture events, cluster receipts move from 7/14/21 to 8/17/26 after the emblem, while wolf (4) and elk (15) receipts stay the same | [REPLAY], high confidence; confirm on golems/monoliths |
| **Hunter** | 50 | +50 kill gold (100 → 150) | V58 build log, engine metadata |
| **Skirmish** | 0.05 | +5% damage to champions (v76's interpretation) | [OPEN] |
| **Greed** | — | 25 shards (750 gold) combine into a 35-stat emblem | [ENGINE] |
| **Collectors** | 0.01 | +1% per owned emblem family (v76 applies it to damage) | [OPEN] |

**Gold to power.** A Strength shard raises a Vendetta's basic damage by about 8.6% (6/70); a Health shard raises any
HP pool by 8–10%.

- **A conversion rate is derivable.** The marginal gem value of gold is
  `λ_gold(t) ≈ (Δ income rate per 30 gold) × (rounds remaining) / 30`.
  ALGORITHM_SPECIFICATIONS.md §2 derives it and gives a calibration procedure.
- **Gold is worth more early.** The same shard compounds over more remaining rounds, so λ_gold falls to roughly zero
  near the end, except for the round-2000 tiebreak.

## 7. Death, recall and recovery

- **Death.** The killer receives the bag and 100 gold ([ENGINE] `kill_gold`), plus 50 with Hunter.
  - Assists earn nothing ([ENGINE] `assist_gold` 0), and there is no passive income ([ENGINE] `passive_gold` 0).
  - A camp kill destroys the bag.
  - Respawn comes after 60 owner turn-end ticks ([ENGINE] `respawn_time`) with full HP and abilities reset. Dead
    champions can shop.
  - **Approximate cost of one death:** 60 rounds of that champion's income (about 0.4–0.6 GE per round, so 25–35 GE),
    plus the bag, plus about 20 GE of enemy gold, plus any objective lost. **Roughly 50 GE plus the bag.**
- **Recall.** 5 turn ends (3 with Home). Damage or a stun interrupts it.
- **Spawn healing.** `spawn_healing = 1` ([ENGINE]): a champion standing on its own spawn returns to **full HP each
  round**. Recall plus one round on spawn is therefore a full heal.
- **Cassi & Issac.** One pick, two bodies with independent turns. If either dies, both die, and the killer gets one
  kill reward plus both bags.

## 8. Vision, information and communication

- **Vision** is radius 8 by symmetric shadowcasting.
  - Walls block it.
  - Bushes block it from outside, but a champion inside a bush sees out of it.
  - **Vision is per champion and is not shared**, nor are allies' wards.
- **Wards.** One per champion: vision radius 6, placed within 2 tiles, permanent, re-placeable after a 10-round
  recharge.
- **Information available during the draft.** The whole map, with no hidden terrain. The enemy spawn region is known
  from the start. Camp groups and their composition are readable through `sdk_map_camp_group*` calls. Enemy picks
  are revealed as they are made.
- **Communication.**
  - 8 bytes of team shared memory, readable and writable all match, which the opponent cannot see.
  - 1024 bytes of draft memory, written during the draft and read-only afterwards.
  - Each champion runs its own bot instance, so **no other computation is shared**.
- **SDK 4 identity reads.** Champion identity is readable even out of vision (V58 build log), but position and HP are
  not.

## 9. Movement and terrain

- **Tiles.** Walls block movement, dashes and sight. Holes block walking but allow dashing and sight. Bushes block
  sight from outside but can be walked through. Altars cannot be entered. Spawn tiles cannot be entered by the enemy
  and heal allies standing on them.
- **Moves.** A move is 1 tile in 8 directions. A dash is 2 steps along a legal path and can cross holes. A teleport
  crystal reaches 3 tiles after a 3-round channel that damage does not interrupt.
- **Maps.** From 30×30 to 100×100. The local pool has 70 maps, matching the platform pool.
  - [OPEN] Whether the finals use this pool (OPEN item Q1 in EXECUTIVE_RECOMMENDATION.md).

## 10. Largest exploitable mechanics (ranked by evidence and leverage)

1. **Deaths are the most expensive event.**
   - About 50 GE plus the bag, and they hand gold to the enemy.
   - In losses we spend twice the champion-rounds dead (E11).
   - The top teams that beat us die 2.2–5.5 times per game against our 8–15 ([TOP_TEAM_REVERSE_ENGINEERING.md](TOP_TEAM_REVERSE_ENGINEERING.md)).
2. **Capture-bound clusters combined with Capture and Prospector emblems.**
   - These are solo, safe, high-rate objectives.
   - v76 buys Prospector first but never *values* clusters with it: `prospector_bonus` is computed and unused.
3. **Tribute ignores damage, and Marcella is stun-immune.** Banking under fire is a legal, strong play, and altar
   locks are the counter.
4. **The early gold compounding window (R0–R250).**
   - The strongest opponent earns 483 gold by R100 against our 278 in the same games, and against 329 for our own
     *uncontested* runs.
   - Side ahead on gold at R250 wins 75% of local mirror games.
5. **Respawn-timed arrival and denial.**
   - Groups respawn on a deterministic timer, and any occupied tile delays the respawn.
   - Arriving on time is free tempo.
6. **Spawn heals 100% per round, and recall is 5 rounds (3 with Home).**
   - Retreating to heal is cheap when no enemy is in reach.
   - A disengage that keeps an objective is better than a retreat.
7. **Altar locks.**
   - 10 gold denies an enemy carrier's tribute until five hits, and cancels an in-progress tribute.
   - A strong endgame and anti-carrier tool.
8. **Non-exclusive draft.** Both teams may pick the same champion, so the draft is a best response to revealed picks,
   with no denial value.

## 11. Open engine questions (each a one-game diagnostic in the implementation phase)

| ID | Question | Why it matters | Diagnostic |
|---|---|---|---|
| ENG-1 | Do damaged sleeping camps heal? | Partial clears; ObjModel | Damage an elk, leave for 10 rounds, read its HP |
| ENG-2 | What does the Tribute emblem's 0.33 do? | Banking value of the item | Bank 40 gems with and without it; compare rounds and gold |
| ENG-3 | Is capture exactly 3 rounds with a Capture emblem? Does Prospector affect non-cluster gems? | Item valuation | Capture logs on a golem map with both emblems |
| ENG-4 | What do the Skirmish and Collectors passives do exactly? | Combat model | Damage logs with and without them |
| ENG-5 | Within-team action order under `set_priority`, and when it takes effect | Crew leader freshness | Log round and slot order |
