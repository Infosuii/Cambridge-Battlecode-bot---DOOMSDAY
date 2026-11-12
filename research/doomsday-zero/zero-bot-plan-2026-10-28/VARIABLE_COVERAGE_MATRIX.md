# Variable coverage matrix: every game quantity, how DZ obtains it, and where it is used

Purpose: prove that no rule or variable is unaccounted for.
- **Source:** RT = runtime-read from the engine; OBS = observed this turn (vision); MEM = remembered or inferred;
  MSG = shared word; DRAFT = draft memory.
- **Status:** V-ENG / V-REP / SDK / RULES / OPEN(CT-#), as in GAME_MECHANICS_AND_WIN_CONDITIONS.md.

## Game-level

| Quantity | Source | Status | Used by |
|---|---|---|---|
| winning_gems, max_rounds | RT `constants` | V-ENG | Race, exchange rates (T_end) |
| Our and their banked gems | RT `global_submitted_gems` | SDK | Race, λ_gold horizon |
| Round | RT `round_number` | SDK | Kernel stale guard; every timer |
| Team size, slot map | RT `team_size`, `champions(ally)` sorted by handle | OPEN CT-21 | Protocol, auction |
| Turn order and priority | RT `set_priority` / `prev_priority` | OPEN CT-6 | Crew leader, micro "acts before enemy" |
| Fuel budget and remaining | RT `fuel_remaining` | V-ENG (10M/100k/200k) | Governor |
| Map symmetry | RT `map::symmetry` | SDK | Enemy belief prior, draft |
| Engine fingerprint | RT hash of constants, designs, items | — | Conformance re-run trigger |

## Terrain and static map

| Quantity | Source | Status | Used by |
|---|---|---|---|
| Walls, holes, bushes, altars | RT `map::*` masks | SDK | Fields, vision planning, dash, wards, banking |
| Spawn regions (both) | RT `spawn_region` | SDK | Fields, safety, healing, shopping |
| Camp groups: members, types, spawn tiles, gold, gems, respawn | RT `camp_groups()` | SDK / V-REP | ObjModel, auction, ledger, draft |
| Camp designs: HP, str, range | RT `base_stats` | V-ENG | ObjModel D_taken, threat |
| Distance fields | RT engine compute | SDK; cost CT-1 | Travel, ObjModel, escape |

## Own champion (self, every turn)

| Quantity | Source | Status | Used by |
|---|---|---|---|
| HP, max HP, str, focus, range, position | OBS self | SDK | All |
| Allowances can_move, can_attack, can_cast; completed_turn | OBS `state()` | SDK | Actuator, action scorer |
| Channel kind and remaining time; recall/tribute started or cancelled this turn | OBS `state()`, `remaining_channel_time` | SDK | EE channel decision, actuator |
| Buffs (shield, stun, enhanced) with durations; restrictions | OBS `buffs()`, `restrictions()` | SDK | Action scorer, EE |
| Ability cooldowns, readiness, payload (range, modifier, radius, duration, targets, exclusive-with-movement, enhanced) | RT design + OBS cooldown | SDK | Spell policy, EE |
| Gold, gems, items (counts by type), consumables | OBS self | SDK | Gear, bank rule, EE (bag) |
| Ward cooldown and positions; placement tiles | OBS self | SDK | Ward planner |
| Can buy / can sell | OBS self | SDK | Gear |
| Passive type | RT design | SDK | Spell policy, ObjModel, gear |
| Emblem passives owned (Monster, Jungle, Durability, Treasure, Capture, Prospector, Home, Hunter, Tribute, Skirmish, Collectors) | OBS items + RT item info | V-REP / OPEN CT-12, 14, 15 | ObjModel, EE, gear |
| Respawn timer (when dead) | RT teammate query | OPEN CT-9 | Protocol DEAD, auction |

## Allies

| Quantity | Source | Status | Used by |
|---|---|---|---|
| Type, team | RT identity (no vision needed) | SDK | Crews, synergy |
| Position, HP, stats, buffs (visible) | OBS | SDK | EE scene, crews |
| Objective and on-site status | MSG slot record | design | Auction residual, crews |
| Dead or alive | MSG DEAD code / OBS | design | Auction |
| Crew stance and leader | MSG CREW_STANCE | design | EE adoption |

## Enemies

| Quantity | Source | Status | Used by |
|---|---|---|---|
| Type, team | RT identity | SDK | Draft best response, threat stats |
| Position, HP, stats, buffs (visible) | OBS | SDK | EE, threat, pressure |
| Ability cooldowns (visible) | OBS | OPEN CT-8 | EE optimistic variant |
| Channel kind and remaining time (visible) | OBS `remaining_channel_time` | SDK | Perma-recall detector, stun-to-interrupt |
| Bag, items (visible) | OBS | OPEN CT-8 | KillValue, threat |
| Last seen, reach ramp, `dead_until` | MEM | design | Pressure, phantoms |
| Banked score and income | RT + MEM | SDK | Race |
| Style class | MEM (R100) | design, optional | Parameter set |

## Camps, groups, objectives

| Quantity | Source | Status | Used by |
|---|---|---|---|
| Camp HP and state (dead, awake, asleep), visible | OBS | SDK | Clear executor, ledger |
| Group state (alive, reward, respawning timer), visible | OBS | SDK; visibility rule CT-10 | Ledger |
| Capture state (timer; ally, enemy or contested) | OBS (group visible) | SDK | Capture executor, EE HOLD |
| Persistent partial HP | MEM | V-REP (no regeneration) | ObjModel T_clear |
| Respawn round (unseen groups) | MEM from CAMP_EVENT + static timer | design | Auction arrival windows |
| Spawn-tile occupancy delaying respawn | OBS / MEM | RULES | Capture tile choice; optional denial |
| Reward split among capturers | rule | RULES, CT-24 | Single-capturer rule |
| Prospector cluster bonus; Capture time 3 | rule | V-REP | ObjModel, gear |

## Wards, locks, teleports

| Quantity | Source | Status | Used by |
|---|---|---|---|
| Visible wards (both teams) | OBS `wards()` | SDK | Vision planning; enemy-ward avoidance (optional) |
| Altar locks (team, hits remaining) | OBS | SDK | Bank altar choice; lock removal |
| Teleport reservations (visible) | OBS | SDK | Threat (arrival prediction), movement legality |

## Economy constants

| Quantity | Source | Status | Used by |
|---|---|---|---|
| Shard and emblem costs, combine counts, stats, passives | RT `item_info` | V-ENG | Gear |
| Consumable cost and carry limit | RT `consumable_info` | V-ENG | Gear, locks |
| kill_gold, assist_gold, passive_gold | RT | V-ENG (100/0/0) | λ, KillValue |
| Gold multipliers (Vesper 0.33, Treasure 0.10, additive) | RT passive + V-REP | V-REP | ObjModel, KillValue, gear |
| Marcella tribute gold 2 per gem | RT constant | SDK | Bank rule |
| capture_time, camp_sleep_time, respawn_time, recall_time, tribute multiplier and minimum, submit range | RT | V-ENG | ObjModel, bank, EE |
| spawn_healing 1.0 | RT | V-ENG | Recovery planning |
| Ward settings, lock hits, teleport time | RT | V-ENG | Ward and lock executors |

## Draft-time

| Quantity | Source | Status | Used by |
|---|---|---|---|
| Revealed picks (both) | RT `current_draft` | SDK | Best response |
| Draft rounds, timing | RT | OPEN CT-20 | Draft loop |
| Full map, groups, designs | RT | SDK | Utility, opening planner |
| Draft memory (1024 B) | write | SDK | Opening, lineup intent |

**Unaccounted quantities:** none known. New engine fields in a future release are detected by the fingerprint
(CT-27) and reviewed before use.
