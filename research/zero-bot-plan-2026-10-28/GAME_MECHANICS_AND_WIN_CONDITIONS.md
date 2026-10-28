# Complete game reference: every rule, quantity and engine fact (engine 2.0.0, CLI/SDK 4.0.0)

This is the single source of truth for the DOOMSDAY Zero bot. Every quantity has a **status**:
- **V-ENG**: read from the engine at runtime (`research/misc/SPRINT3_SDK_FACTS.json`, probed 2026-10-26), or from the
  fuel trace budget words.
- **V-REP**: verified from saved replays or summaries (method given).
- **SDK**: stated in the official SDK header `sdk/cpp/cambc.h` (4.0.0).
- **RULES**: stated only in `game rules/GameRules.md`, which is **outdated in several places** (see §12).
- **OPEN**: unverified. Each OPEN item has a conformance test (CT-#) in ENGINE_CONFORMANCE_SUITE.md.

**Design rule.** The bot reads every numeric value it can from the engine at startup: `constants::*`, champion
designs, ability payloads, item and consumable info, camp designs. Nothing in this table is hard-coded except as a
fallback default with a startup self-check.

## 1. Match structure and victory

| Item | Value | Status |
|---|---|---|
| Winning condition | first team to **tribute** `winning_gems` = 1000 wins immediately | V-ENG |
| Round limit | `max_rounds` = 2000 | V-ENG |
| Tiebreak at the limit | tributed gems, then lifetime gold earned, then kills; full tie means Team B wins | RULES |
| Score query | `global_submitted_gems(team)`, available for **both** teams at any time | SDK |
| Round query | `round_number()` | SDK |
| Team size | 3–5 champion picks depending on map (`team_size()`); C&I is one pick but two bodies | RULES / SDK; OPEN whether `team_size` counts picks or bodies (CT-21) |
| Draft rounds | `sdk_draft_num_rounds` | SDK; value OPEN (CT-20) |
| Resign | `resign()` (never use) | SDK |

## 2. Execution model (what the program actually is)

- **One bot instance per role.** There is a separate draft instance (`is_draft()` true) and one instance per champion
  body, including separate Cassi and Issac instances.
- **Persistent process.** Each instance is a long-running `main()` that yields with `end_turn()`. Static and global
  memory persists for the whole game.
- **Fuel budget per turn** (V-ENG, from the fuel trace budget words `(10000000, 100000, 200000, 100000)`):

  | Turn | Budget |
  |---|---|
  | **First draft turn** | **10,000,000** (100×; the rules wrongly say 10×) |
  | Later draft turns | 100,000 |
  | Each champion's first play turn | 200,000 |
  | Every later turn | 100,000 |

  Unused fuel is lost.
- **Running out of fuel suspends execution mid-instruction stream. The next turn resumes from that exact point**
  (RULES; consistent with Wasmtime fuel semantics [B24]). Consequences:
  - Code after a suspension point runs in the *next* round, with stale local variables.
  - The bot must re-check `round_number()` before every action and abandon a decision computed in an earlier round.
- **Fuel metering** (Wasmtime): guest wasm operators cost fuel (about 1 per instruction; control operators 0).
  - Work done inside host calls (engine BFS, shadowcast, distance fields, `move_towards`) is free *unless the engine
    charges it*. cambc has a `fuel_adjust` import, so it can.
  - The cost of each host primitive is **OPEN** (CT-1) and must be measured on Day 1.
- **`debug_block` / `CAMBC_DEBUG`.** Free fuel only in debug builds (`cambc run` default). It is **skipped in
  `--release` and always on the platform**. Never rely on debug-only behaviour; always test release builds.
- **Exceptions.** An uncaught exception or abort is a **bot fault**, which appears in summaries as `botFaults`. The
  effect is presumably that the champion stops acting for the rest of the game (OPEN, CT-19; deliberate test only).
  Policy: catch everything at the turn boundary, then `end_turn()`.
- **Determinism.** The engine is deterministic for a given (wasm pair, map). Bots may seed their own RNG; the game
  outcome is then fixed.

## 3. Round and turn order

- **Round start**, in this order:
  1. camp respawns
  2. spell, buff and ward updates
  3. **camp captures** (the capture phase)
  4. camp turns: awake camps attack the nearest champion in range
- **Then champion turns.** Teams alternate, and the starting team swaps every round. Within a team, higher
  `priority` acts first, with ties broken by draft order. `set_priority(p)` takes effect **from the next round** and
  persists; `prev_priority()` gives the current round's value (SDK).
  - OPEN (CT-6): whether the alternation is champion-by-champion (A1 B1 A2 B2…) or team blocks.
- **Dead champions** still get a turn, and can shop.
- **Inside a champion's turn:**
  - at turn start: respawn check, ward recharge, buff and shield expiry, then channels
  - then the bot acts
  - at turn end: timers decrement and spawn healing applies
- **Recall arrival** happens at turn start, so staying on spawn that turn heals at turn end.

## 4. Actions and allowances (per champion per turn)

| Action | Rule | API | Status |
|---|---|---|---|
| Move | One step in 8 directions. Ranged: move **or** basic attack. Melee: both. Exclusive-with-movement spells forbid moving after casting, and casting after moving | `move(delta)`, `move_absolute`, `move_towards(target)` (engine shortest path avoiding walls, holes, altars, enemy spawn, visible units, teleport reservations) | SDK |
| Blocked move | An unseen occupant: returns `false`, the tile is revealed for the round (`tile_reveal_rounds` = 1), and the allowance is kept. Moving onto a known-occupied tile throws | same | SDK / RULES |
| Basic attack | Damage = strength before modifiers; Chebyshev range 1 (melee) or 3 (ranged); visible target. Also works on altar locks | `attack(unit)`, `attack(altar_lock)` | SDK |
| Ability | One successful cast per turn across both slots. Cooldown `max_cooldown` = 8 owner turn ends. Payload kinds: attack_reset, damage, aoe_damage, cc (stun), heal, dash, shield | `abilities()[s].use()`, `.use(tile)`, `.use(champion)`, `.use(camp)`; `damage_amount(target)` predicts health lost after mitigation and shields | SDK |
| Recall | Channel of `recall_time` = 5 turn ends (3 with Home). Interrupted by damage, stun or death; manually cancellable. One start and one cancel per turn | `recall()`, `cancel_recall()` | V-ENG / SDK |
| Tribute | Within `submit_gems_range` = 1 of an altar, with gems. Duration `max(min=1, ceil(0.1 × bag))` turn ends. Banks the whole bag at completion. **Not interrupted by damage**; interrupted by stun, death or a new altar lock | `submit_gems(altar)`, `cancel_submit_gems()` | V-ENG / RULES |
| Shop | On own spawn or while dead (Tavi: shards anywhere). Tavi can sell at spawn for the full value | `buy(item, n)`, `buy(consumable)`, `sell(item, n)`, `can_buy`, `can_sell` | SDK |
| Ward | One active ward (`active_wards` 1, `ward_charges` 1); placement within `ward_placement_radius` = 2; vision radius 6; permanent (`ward_lifetime` −1); recharge `ward_cooldown` = 10 rounds; a new ward replaces the old one | `place_ward(tile)`, `ward_cooldown()`, `ward_placement_tiles()` | V-ENG |
| Consumables | 10 gold each (`consumable_info.cost`); carry at most one of each (`carry_limit`) | `consumables()[k].use(tile)` | V-ENG (2 types) |
| Teleport crystal | A 3-turn-end channel (`tp_crystal_time` 3), then a flash to a reserved tile within 3. Damage does not interrupt; stun or death does; cannot be cancelled. The destination is reserved and visible to others | consumable | V-ENG / RULES |
| Altar lock | Placed on an altar within 2. Blocks enemy tribute and cancels enemy channels there. Removed by `altar_lock_hits` = 5 basic attacks. An enemy tribute attempt becomes an attack on the lock | consumable | V-ENG / RULES |
| End turn | `end_turn()` yields | SDK | |

**Turn-state flags** (`champion.state()`): alive, recalling, submitting_gems, can_move, can_attack, can_cast,
completed_turn, recall_started, submit_gems_started, recall_cancelled, submit_gems_cancelled, teleporting.

**Restrictions** (`restrictions()`, from buffs): move, attack, cast, shop, consumable, ward.

**Buffs** (`buffs()`): shield (duration, value; the earliest-expiring absorbs first), stun (duration), enhanced
attack (duration).

## 5. Champions (V-ENG values; the bot reads them from `champion_designs` at startup)

| Champion | HP (+growth) | Str (+) | Focus (+) | Range | Slot 0 (engine) | Slot 1 (engine) | Passive (`passive_type`) |
|---|---|---|---|---|---|---|---|
| Ryth | 1200 (+100) | 45 (+4.5) | 100 (+10) | 1 | aoe stun: range 4, radius 1, 1.0×F, 1 turn | attack reset | health_strength: +1% of bonus HP as Str |
| Vesper Vale | 1000 (+100) | 45 (+5) | 100 (+10) | 3 | attack reset | dash 2 | bonus_gold +33%, applies to **all** gold including kills (V-REP) |
| Vendetta | 1000 (+100) | 70 (+6) | 100 (+10) | 1 | attack reset | dash 2 | reset cooldowns on credited kill, camps included |
| Cassi | 600 (+65) | 30 (+3) | 100 (+13) | 3 | damage 2.0×F @4 | stun 1 turn @4 (cc, mod 0) | linked fate with Issac |
| Issac | 900 (+80) | 45 (+3) | 100 (+10) | 1 | attack reset | dash 2 | linked fate |
| Stellar | 650 (+65) | 30 (+3.5) | 70 (+8.5) | 3 | damage 2.0×F @4 | aoe 1.4×F r1 @4 | — |
| Prism | 700 (+65) | 35 (+2.5) | 80 (+8) | 3 | cc 1.5×F + stun 1 @4 | aoe 1.0×F r1 @4 | gem_focus +1.5 F per carried gem |
| Marcella | 1200 (+100) | 45 (+4.5) | 60 (+14) | 1 | enhanced-attack reset (next hit stuns 1) | damage 2.0×F @4 | stun_immunity; +2 gold per gem tributed |
| Willow | 700 (+50) | 55 (+3) | 140 (+5) | 3 | heal ally 3.0×F @4 | attack reset | — |
| Ren | 900 (+100) | 35 (+5) | 100 (+9) | 1 | cc 1.1×F + stun 1 @4 | dash 2 | retaliation 0.2×F per hit taken |
| Varg | 1000 (+100) | 45 (+5) | 100 (+10) | 1 | attack reset | shield 2.5×F, 5 turns | splash = Str to others within r1 of the target |
| Tavi | 900 (+75) | 45 (+5) | 110 (+10) | 3 | attack reset | cc 1.6×F + stun 1 @4 | remote_shop (shards anywhere; sell at spawn) |
| Heart of Ruin | 1000 (+100) | 30 (+3) | 100 (+10) | 1 | shield 1.5×F, 5 turns | dash 2 landing 1.5×F r1 + stun 1 | missing_health_damage: up to +50% at 0 HP, linear |

Common to all champions: vision radius 8 (symmetric shadowcasting); speed 1; `camp_damage_multiplier` 1; ability
cooldown 8.

**Per-ability engine fields** (read at runtime): `max_cooldown`, `valid_targets` (camps, enemies, allies, self,
ground), `exclusive_with_movement`, range, modifier, radius, duration, `enhanced_attack`.

## 6. Camps, groups and capture

| Camp | HP | Str | Range | Gold | Gems | Respawn | Status |
|---|---|---|---|---|---|---|---|
| Wolf | 1350 | 20 | 3 | 40 | 4 | 40 | HP/Str/range V-ENG; rewards V-REP (receipts 40/4) |
| Elk | 2400 | 60 | 4 | 90 | 15 | 60 | as above |
| Golem | 5000 | 120 | 4 | 160 | 36 | 80 | as above |
| Monolith | 20000 | 200 | 5 | 300 | 200 | 150 | as above |
| Gem cluster | 120 | 0 | – | 0 | 7 | 50 | V-REP (receipt 7) |
| Gold cluster | 120 | 0 | – | 20 | 0 | 50 | as above |

Rewards and respawn are also per group at runtime: `camp_group.gold_value()`, `gem_value()`, `max_respawn_timer()`.

**Rules:**
- **Groups** are cardinally connected camps. Rewards combine over the group, and respawn uses the longest member timer.
- **Waking and sleeping** (camp vision 8; camps see through bushes; camps do not chase).
  - Damage wakes the *whole group*.
  - Awake camps attack the nearest champion in range each camp turn, with a 2-round attack cooldown in their ability
    record (OPEN whether that means one hit every 2 rounds; CT-11).
  - They sleep after `camp_sleep_time` = 2 rounds with no champion in range.
- **Damaged camps do not regenerate while unattended** (V-REP: 1,846 observed round-pairs of a damaged, alive camp
  with no champion within 9 tiles; HP unchanged in all 1,846, increased in 0). Partial clears persist until death or
  respawn.
- **Capture.**
  - After every member of the group is dead, a champion must stand on one of the group's spawn tiles, uncontested.
  - The timer starts at a capture phase and counts down over later phases: `capture_time` = 5, or **3 with a Capture
    emblem**. V-REP: the last-kill-to-reward delay has a mode of 6–7 rounds without the emblem and 4–5 with it, over
    6,000+ captures.
  - An empty or contested region resets progress.
  - Extra allies do not speed capture. The reward is **split among the allies present**, with the remainder going to
    the lowest ID.
  - `capture_state()` returns the timer and status (no_capture_available, ally_capturing, contested,
    enemy_capturing, capture_available). It needs **group visibility only**.
- **Respawn.** After the reward is claimed, the group respawns after `max_respawn_timer`. **Any occupied spawn tile
  delays the respawn of the whole group.** `camp_group.state()` is alive, reward_available, or respawning(timer), and
  is only available while the group is visible ("remembered state outside vision is not exposed").
- **Group visibility.** A group is visible when any of its original spawn tiles is in effective vision.
- **Camp kills** destroy the victim's carried gems.

## 7. Gold, items and modifiers

**Shop:**
- A shard costs 30 gold. Five matching shards combine automatically into an emblem (150 gold total). Only the emblem
  grants the family passive, and a second emblem of the same family adds no further passive.
- Stats from every shard count, including those inside emblems.
- Greed is the exception: 25 shards (750 gold) combine into a +35-stat emblem with no passive.
- **Spawn purchases of Health heal by the amount gained.** Tavi's field purchases do not.

**Emblem families** (14 in the engine; 7 in the rules):

| Family | Engine passive (magnitude) | Verified meaning | Status |
|---|---|---|---|
| Monster | 0.15 | +15% damage to camps (rules say 10%) | SDK comment |
| Power | — | counts as 6 shards | SDK |
| Durability | 0.10 | −10% incoming damage | SDK |
| **Treasure** | 0.10 | **+10% on all gold gains, kills included** (rules say 20%). V-REP: 40→44, 100→110, 90→99 | V-REP |
| Jungle | 0.30 | −30% damage from camps | SDK |
| Home | 0.5 | recall 3 turn ends instead of 5 | SDK |
| Bruiser | — | 5 of the chosen stat + 1 of each other | SDK |
| **Tribute** | 0.33 | unknown: tribute speed or bonus | **OPEN (CT-12)** |
| **Capture** | 3 | capture time 3 | V-REP |
| **Prospector** | 0.25 | **+25% gems from gem clusters, floored** (7→8, 14→17, 21→26); wolf and elk receipts unchanged | V-REP (9,196 events); golem/monolith OPEN (CT-13) |
| **Hunter** | 50 | +50 kill gold (presumably 100→150) | V-ENG metadata; effect OPEN (CT-14) |
| **Skirmish** | 0.05 | probably +5% damage to champions | OPEN (CT-15) |
| **Greed** | — | 25 shards → 35-stat emblem | V-ENG |
| **Collectors** | 0.01 | probably +1% per owned emblem family | OPEN (CT-15) |

**Gold multipliers stack additively** (V-REP):
- Vesper: +33%
- Vesper with Treasure: **+43%** (40→57, 100→143). The rules' "53%" assumes the old 20% Treasure.
- Marcella: +2 gold per gem tributed.

**Gold sources:**
- captures (reward split among allies present)
- kills: `kill_gold` 100 to the champion credited with the kill
- Marcella's tribute gold

`assist_gold` = 0 and `passive_gold` = 0 (V-ENG).

## 8. Death, recall and recovery

- **Respawn.** `respawn_time` = 60 owner turn-end ticks, then respawn at the next turn start (when a spawn tile is
  free) with full HP and abilities reset.
- **Kill rewards.** The killer receives the bag and 100 gold (plus 50 with Hunter). A camp kill destroys the bag.
- **Cassi & Issac.** If either dies, both die; one kill reward plus both bags go to the killer.
- **Spawn healing.** `spawn_healing` = **1.0 of max HP per round** on own spawn, so one round on spawn is a full heal
  (V-ENG).
- **Respawn timers.** Teammates' respawn timers are queryable (an `api_champion_alive` error exists for alive
  champions; `api_not_teammate` for enemies). Enemies' respawn must be tracked from observed deaths (60 rounds).

## 9. Vision, information and communication

- **Vision.** Radius 8, symmetric shadowcasting. Walls block it. Bushes block it from outside; a champion inside a
  bush cluster sees across it and out of it, but not into other bushes. Holes do not block sight.
- **Not shared.** Allies' vision and wards are not shared, and every query is from this champion's perspective.
  `in_vision(tile)` covers self plus own ward.
- **Always available (no vision needed):**
  - static map: terrain masks, altars, spawn regions, symmetry, camp groups with members, rewards and timers
  - champion identity (type and team) of all champions via `champions(team)`
  - both teams' submitted gems
  - the round number
  - own state: gold, gems, items, cooldowns, channel, wards
- **Needs vision:**
  - other champions' position, HP, stats, buffs, cooldowns (`sdk_champion_cooldown` on visible enemies; OPEN
    CT-8), channel time (`remaining_channel_time`), gems, items
  - camp HP and state
  - group state and capture state
  - wards, locks, teleports
  - `is_alive()` of others (OPEN CT-9: does it work without vision?)
- **Shared memory.** 8 bytes per team, read and write all match, invisible to the opponent. Writes are immediate,
  and a later champion in the same round sees them.
- **Draft memory.** 1024 bytes, written in the draft (a write submits immediately; truncated at capacity), and
  read-only snapshot at champion startup.
- **Map symmetry.** `map::symmetry()` returns horizontal, vertical or rotational180. Mirroring gives the enemy's spawn
  and objectives exactly.

## 10. Movement and terrain

- **Tiles.**
  - Wall: blocks movement, dashes and sight. A teleport can target next to walls; landing on a wall is not allowed.
  - Hole: no walking, but dash over it and see over it.
  - Bush: blocks sight from outside; walkable.
  - Altar: not enterable.
  - Spawn: enemy cannot enter; heals allies.
- **Dash.** Up to 2 steps on a legal path, which may cross holes. Teleport range is 3, ignoring terrain. **Landing**
  is never on a wall, hole, altar, enemy spawn or occupied tile.
- **Maps.** From 30×30 to 100×100.
- **Engine-side helpers (SDK):**
  - `bitboard.reachable_tiles(origin, d)` (BFS)
  - `bitboard.shadow_cast(origin, d)` (vision)
  - `distance_field.compute(walls, roots, visited, max)` and `compute_to(…)`
  - `next_move_from(p)` / `next_moves_from(p)`
  - `champion.visible_tiles_from(p)` (hypothetical vision)
  - `ward::visible_tiles_from(p)`
  - `unit.attack_tiles()`, `ability.valid_tiles()`
  - bitboard set algebra, shifts, reflection, `draw_circle` / `draw_chebyshev`

  Their fuel cost is **OPEN (CT-1)**.

## 11. Draft

- **Picks** are made one per draft round, **simultaneously** by both teams, and revealed as they go
  (`current_draft(team)`).
- **Champions are not exclusive.** Both teams may own the same champion, so there are no denial picks.
- **C&I** is one pick.
- If the draft bot yields, exhausts fuel or crashes without picking, **the remaining picks are random** (RULES), so
  the draft must always pick.
- **The whole map is visible during the draft:** all camp groups, terrain and spawns. Champion designs and abilities
  are available too.
- The first draft turn has a 10M fuel budget.

## 12. Where the published rules are wrong (verified engine wins)

| Rules text | Engine truth |
|---|---|
| Draft first turn 10× fuel | **100× (10M)** |
| Treasure +20% gold | **+10%** |
| Vesper + Treasure = 53% | **43%** |
| Monster +10% | **+15%** |
| 7 emblem families | **14** (Tribute, Capture, Prospector, Hunter, Skirmish, Greed, Collectors added) |

Champion stats where the rules differ from the engine:
- Vesper strength 55 (engine **45**)
- Cassi focus 70 (engine **100**)
- Issac strength 40 (engine **45**)
- Varg strength 40 (engine **45**)
- Willow focus 120 (engine **140**)
- Ren stun 0.75×F (engine **1.1×F**)
- Tavi stun 1.4×F (engine **1.6×F**)
- Ryth strength growth 5 (engine **4.5**)
- Marcella strength growth 5 / focus growth 15 (engine **4.5 / 14**)
- Stellar focus growth 7 (engine **8.5**)
- Prism HP growth 60 (engine **65**)
- Heart focus growth 12 (engine **10**)

## 13. Platform and season facts

- **Engine releases are frequent.** cambc versions 2.1.x (Oct 13), 2.2.x (Oct 16–17), 3.0.x (Oct 20–22) and 4.0.0
  (Oct 25) [B25]. **Expect another balance change before the finals.** The bot must read all values at runtime, and
  the conformance suite must be re-run on every new CLI.
- **Local and platform engines match:** engine build hash, map hashes and fuel behaviour verified 2026-10-28.
- **The official engine source is not public** (the listed GitHub repository returns 404). Rules text and SDK headers
  are the only documentation.
- **Map pool.** 70 local maps equal the platform pool. Whether the finals use them is OPEN (user question Q1).

## 14. Derived economics (formulas the bot uses; all inputs runtime-read)

- **Gems per 1k HP:** wolf 3.0, elk 6.3, golem 7.2, monolith 10, gem cluster 58.
- **Capture-bound objectives** (clusters): one champion is optimal; cycle = travel + 1 + capture time.
- **Damage-bound objectives** (camps): cycle = travel + HP / crew DPS + capture. Crews add DPS, not capture speed.
- **Death cost** ≈ 60 rounds × the champion's income rate + bag + 100 gold to the enemy, so roughly 50 gem-equivalents
  plus the bag.
- **Banking** is an optimal-stopping problem (ALGORITHM_SPECIFICATIONS §4).
