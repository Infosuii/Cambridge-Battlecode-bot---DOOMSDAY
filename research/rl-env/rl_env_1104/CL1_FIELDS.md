# cl1 field map (authoritative, as implemented)

Source of truth: `bots/claude-rlenv-1104/src/clrl_rec.h` (`ClrlFriend::encode`). This file replaces the field lists
in `CL1_SCHEMA.md` (a proposal) wherever they differ. Layout id 10 in `contract.py`, 448 int16 values per row, every
value cleared to 0 before each row is filled.

Conventions: `q()` = integer clamp to ±32000. "frac" = ×1000 of a ratio, `-1` if the denominator is 0. "age" =
`min(2000, now − then)` rounds, `-1` = never seen. Positions are tile coordinates; `dx, dy` = target − self.

**Sources** (what the body may legally know):
- **SDK-global:** public engine queries (`round_number`, `global_submitted_gems`, `symmetry`, `fuel_remaining`).
- **self:** `bc::self()` and v92's per-turn self snapshot (`refresh_self`, read this turn).
- **World-vis:** v92's `World`, refreshed this turn from this body's vision (`w.allies`, `w.enemies`: visible now).
- **World-mem:** `World` records that persist across turns. They hold this body's earlier observations **and sightings
  shared through team memory**: `GroupRec.state`, `seen_round`, `CampRec.hp`, `dead`. `age` says how old they are.
- **own-mem:** the recorder's own per-body table of enemy sightings (only `w.enemies`, i.e. this body's view).
- **static:** map geometry and settings, the same for the whole game.

## g: globals (offset 0, 16)

| i | field | value | source |
|---:|---|---|---|
| 0 | round | `round_number` | SDK-global |
| 1 | our score | `global_submitted_gems(ally)` | SDK-global |
| 2 | enemy score | `global_submitted_gems(enemy)` | SDK-global |
| 3 | win target | `constants::winning_gems` | static |
| 4 | team size | v92 `team_size` (champion bodies) | static |
| 5, 6 | map width, height | tiles | static |
| 7 | symmetry | `int(bc::symmetry())` enum | static |
| 8 | my slot | 0..5 | static |
| 9 | allies visible + 1 | `w.allies.size() + 1` | World-vis |
| 10 | enemies visible | `w.enemies.size()` | World-vis |
| 11 | enemies seen ≤ 50 rounds ago | count in own-mem | own-mem |
| 12 | distance to own spawn | Chebyshev to nearest own spawn tile, -1 none | static + self |
| 13 | distance to nearest altar | Chebyshev, -1 none | static + self |
| 14 | draft memory present | 1 if non-empty | static |
| 15 | fuel left ÷ 100 | `fuel_remaining()/100` at capture | SDK-global |

## s: self (offset 16, 32)

| i | field | value |
|---:|---|---|
| 0 | champion type | `int(champion_type)` enum |
| 1, 2 | x, y | tiles |
| 3, 4 | health, max health | integer |
| 5, 6 | strength, focus | integer |
| 7, 8 | gems, gold | carried |
| 9 | state bits | bit 0 alive, 1 recalling, 2 submitting, 3 can_move, 4 can_attack, 5 can_cast, 6 teleporting, 7 recall_started, 8 submit_started |
| 10, 11 | ability 0 / 1 cooldown | rounds (v92 `cooldown[]`) |
| 12 | attack range | tiles |
| 13 | melee | 1 / 0 |
| 14 | wards placed (active) | `ward_positions().size()` |
| 15..30 | reserved | 0 (items by family not yet encoded) |
| 31 | engine champion id | `my_id`, an identifier: **strip before the model** |

All from self (this turn).

## a: allies (offset 48, 5 × 16), by slot order excluding self

| i | field | value | source |
|---:|---|---|---|
| 0 | present | 1 if the slot exists | static |
| 1 | type | `slot_type[slot]` enum | static (draft) |
| 2 | visible now | 1 if in `w.allies` this turn | World-vis |
| 3, 4 | dx, dy | only when visible, else 0 | World-vis |
| 5 | health frac | only when visible | World-vis |
| 6 | distance | Chebyshev, only when visible | World-vis |
| 7 | strength | only when visible | World-vis |
| 8 | attack range | only when visible | World-vis |
| 9..15 | reserved | 0 | |

No shared-memory claims or positions of hidden allies (by design: no dependence on v92's protocol).

## e: enemies (offset 128, 6 × 16), own-mem order of first sighting

| i | field | value | source |
|---:|---|---|---|
| 0 | present | 1 once seen at least once | own-mem |
| 1 | type | enum, from the last sighting | own-mem |
| 2 | visible now | 1 if in `w.enemies` this turn | World-vis |
| 3 | age | rounds since last sighting (0 when visible) | own-mem |
| 4, 5 | dx, dy | last-known position − self (frozen while hidden) | own-mem |
| 6 | health frac | at last sighting | own-mem |
| 7 | gems | at last sighting | own-mem |
| 8 | distance | Chebyshev to last-known position | own-mem |
| 9 | attack range | at last sighting | own-mem |
| 10 | in my attack range now | 1 only when visible | World-vis |
| 11..15 | reserved | 0 | |

Enemies never seen by this body are absent; deaths aren't inferred from gaps.

## c: camp groups (offset 224, 12 × 16): the 12 nearest by Chebyshev distance from self to the group's camp centroid

| i | field | value | source |
|---:|---|---|---|
| 0 | present | 1 | static |
| 1, 2 | dx, dy | centroid − self | static + self |
| 3 | camps in group | count | static |
| 4..9 | camps by type | counts for `camp_type` 0..5 (wolf, elk, gem cluster, gold cluster, monolith, golem) | static |
| 10 | group state | 0 alive, 1 reward waiting, 2 respawning (`GroupRec.state`) | **World-mem** |
| 11 | dead camps | count of `CampRec.dead` | **World-mem** |
| 12 | health frac | remaining / max over the group | **World-mem** |
| 13 | distance | Chebyshev | static + self |
| 14 | age | rounds since any spawn tile was visible (`seen_round`) | World-mem |
| 15 | gem reward | `GroupRec.gems` | static |

Ordering: distance, then World group index. Groups beyond the 12 nearest are dropped; the macro label then becomes 12.
Coverage by map size will be measured. World-mem fields can include **teammates' shared sightings**; `age` tells the
learner how fresh they are.

## l: altars (offset 416, 4 × 8), World order

| i | field | value |
|---:|---|---|
| 0 | present | 1 |
| 1, 2 | dx, dy | altar − self |
| 3 | distance | Chebyshev |
| 4, 5, 6 | ally lock, enemy lock, lock hits | **-1 = not read yet** |
| 7 | in submit range | 1 if distance ≤ `submit_gems_range` |

## Labels with each row (not features)

- `action` / `teacher_action` (`target13-cl1`): v92's `target_group` at the end of the turn, mapped to its c-row; 12 if
  none or outside the 12.
- `prim`, `move_dx`, `move_dy`: **outcome diagnostics** from state diffs, not action labels. Full control will use a
  separate ordered per-call action schema.
