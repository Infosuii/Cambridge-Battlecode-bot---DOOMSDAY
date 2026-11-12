# SDK and engine interface: what DZ calls, when, and what can go wrong

**Authority.**
- `sdk/cpp/cambc.h` (SDK 4.0.0, 5,527 lines) wraps 154 raw imports (`sdk/cpp/imports.h`).
- `game rules/BotAPICpp.md` is an older rendering: it lacks the 7 new item families.
- When in doubt, read `cambc.h`.

## 1. Program shape

```cpp
int main() {
  if (cambc::is_draft()) { /* draft instance */ for (;;) { /* decide */ cambc::draft::pick(x); cambc::end_turn(); } }
  /* champion instance */ boot(); for (;;) { turn(); cambc::end_turn(); }
}
```

- **Instances.** One draft instance, then one instance per body (Cassi and Issac are separate).
- `cambc::self()` throws in the draft. `is_draft()` is free (no host call).
- Global and static state persists across turns. There is no shared memory between instances except the 8-byte team
  buffer and draft memory.
- **Stale snapshots.** `buff_collection`, `ward`, `teleport` and `altar_lock` objects are snapshots. Call again for
  fresh values.
- **Debug output.** `debug::draw_dot` / `draw_line` and stdout are for local analysis only.
  - Stdout costs fuel in release.
  - `debug_block` is free only in debug builds and is skipped entirely in `--release` and on the platform. Never put
    logic inside it.

## 2. API by module (with visibility requirements)

| Module | Calls | Visibility / perspective rules |
|---|---|---|
| Boot / StaticWorld | `constants::*`; `champion_designs[13]`; `champion(type).abilities()[s].info()`; `item_type(i).info()` for i < count; `consumable_type::*.info()`; `map::width/height/walls/bushes/holes/altars/spawn_region(team)/symmetry()`; `map::camp_groups()` (also works in the draft); `group.camps()`, `spawn_tiles()`, `gold_value()`, `gem_value()`, `max_respawn_timer()`; `camp.base_stats()` | Static and always available |
| Fields | `distance_field::compute(walls, roots, visited, max)`; `compute_to(...)`; `get(p)`; `next_move_from(p)` / `next_moves_from(p)`; `bitboard::reachable_tiles`, `shadow_cast` | Host-side; **fuel cost OPEN (CT-1)**. Fields are per instance and cannot be shared |
| Observation: self | `self().state()`, `health()`, `max_health()`, `strength()`, `focus()`, `position()`, `gold_count()`, `gem_count()`, `item_count()`, `consumables()[k].count()`, `abilities()[s].cooldown()` / `is_ready()`, `buffs()`, `restrictions()`, `remaining_channel_time()` (throws if not channelling), `ward_cooldown()`, `ward_positions()`, `priority()` / `prev_priority()`, `can_buy()`, `can_sell()` | Self always |
| Observation: others | `champions(team)` (all handles, including hidden); `.champion_name()`, `.team()` (no vision needed); `.is_visible()`; `.position()`, `.health()`, `.max_health()`, `.strength()`, `.focus()`, `.attack_range()`, `.state()`, `.buffs()`, `.gem_count()`(?), `.item_count()`(?), `.abilities()[s].cooldown()`(?), `.remaining_channel_time()` | Vision required; **CT-8, CT-9** for gems, items, cooldowns and `is_alive` of hidden units |
| Observation: map state | `map::camps()`, `champions()`, `camp_groups()` (visible ones); `camp.state()` (throws if hidden); `group.state()`, `group.capture_state()` (group visible if any spawn tile is in vision); `map::wards()`, `altar_locks()`, `teleports()`; occupancy masks `champion_tiles`, `camp_tiles`, `awake_camp_tiles`, `ward_tiles`, `altar_lock_tiles`, `teleport_tiles`, `visible_tiles()`, `in_vision(p)` | Own perspective (self plus own ward) |
| Scores | `global_submitted_gems(team)`, `round_number()` | Always |
| Actions (Actuator only) | `move(delta)`, `move_absolute(p)`, `move_towards(p)`; `attack(unit)`, `attack(altar_lock)`; `abilities()[s].use()`, `.use(tile)`, `.use(champion)`, `.use(camp)`; `recall()`, `cancel_recall()`; `submit_gems(altar)`, `cancel_submit_gems()`; `buy(item, n)`, `buy(consumable)`, `sell(item, n)` (Tavi); `consumables()[k].use(tile)`; `place_ward(p)`; `set_priority(p)` | See §3 |
| Prediction | `ability.damage_amount()` (outgoing, before target mitigation); `damage_amount(target)` (after mitigation and shields, capped at HP; target visible); `heal_amount(target)`; `shield_amount(target)`; `unit.attack_tiles()`; `ability.valid_tiles()`; `champion.visible_tiles_from(p)`; `ward::visible_tiles_from(p)` | Visible target |
| Shared memory | `shared_memory.read(0, span)`, `.write(0, span)` (8 bytes) | Immediate; team-private |
| Draft | `draft::team_size()`, `current_draft(team)`, `pick(champion_draft)`, `draft_memory = bytes` (submits immediately), `champion_designs`; `map::*` and `camp_groups()` available | Draft instance only |

## 3. Action semantics and error handling

**Return values.**
- `true`: success.
- `false`: a newly revealed hidden obstruction. The allowance is **not** consumed, so retry another tile in the same
  turn.
- Throws `cambc::error(code)` for known-invalid actions. The full list of error codes is in `cambc.h:300–569`.

**Codes the Actuator must handle explicitly (never let them escape):**
- **Movement:** `invalid_action_move_cant_move` (21), `_bad_destination` (22), `_already_moved` (36),
  `_out_of_range` (37), `_unreachable` (38), `move_exclusive_spell_cast` (127).
- **Spells:** `spell_cast_already_cast` (27), `_on_cooldown` (28), `_bad_target` (30), `_out_of_range` (31),
  `_bad_destination` (32), `_already_moved` (126).
- **Attack:** `attack_cant_attack` (40), `_already_attacked` (41), `_bad_target` (42), `_out_of_range` (43).
- **Channels and state:** `cant_act` (33, stunned), `is_recalling` (34), `is_submitting_gems` (35), `is_teleporting`
  (123).
- **Tribute:** `submit_gems_out_of_range` (48), `submit_gems_altar_locked` (125), `submit_gems_already_used` (114).
- **Shop:** `buy_item_not_on_spawn` (49), `not_enough_gold` (52), `inventory_full` (53), `stats_overflow` (54).
- **Wards:** `place_ward_*` (62–65, 117).
- **Locks:** `altar_lock_*` (118–120).
- **Vision:** `api_not_in_vision` (97).

**Policy.**
- **Pre-check.** Check allowance flags (`can_move`, `can_attack`, `can_cast`), restrictions and range before every
  action.
- **On a thrown error:** log it (in diagnostics), mark that allowance as unavailable for the turn, and let the action
  scorer pick the next-best candidate that does not need it. At most 3 retries per turn.
- **Stale guard.** Every action first compares `round_number()` with the turn context (MASTER §3).

**Ordering rules inside a turn:**
- **Melee:** attack and move in either order. Prefer attack-then-move when retreating, and move-then-attack when
  closing.
- **Ranged:** move **or** basic attack, never both, unless an attack reset restores the attack.
- **Exclusive-with-movement spells:** cannot cast after moving and cannot move after casting.
- **Walk-compatible spells:** dash, reset, shield, heal, Cassi's stun, Marcella's reset.
- **One successful cast per turn.**
- **Channels:** starting a recall or tribute ends other actions. Start a channel *last* in the turn.
- **Shop before leaving spawn.** Buying Health on spawn heals by the amount gained.

## 4. Performance and caching notes

- **Terrain masks are cached** by the SDK (`map::walls()` and so on are references). **Camp groups are re-queried on
  every call** of `map::camp_groups()`, so cache them at boot.
- **`bitboard` construction** allocates host-aligned memory and calls `clear()` (a host call). Reuse scratch boards
  and use the `_into` variants.
- **`distance_field`** buffers are size W×H×2 bytes: 20 KB for a 100×100 map. 112 group fields come to 2.2 MB per
  instance, which is acceptable in wasm memory, but build them lazily.
- **Snapshots and repeated calls.** `champion.state()` and stat calls each query the host. Read them once per turn
  into the Observation.
- **Unknown host costs.** Host-call fuel costs are unknown until CT-1. FUEL_AND_PERFORMANCE.md gives budgets under
  two scenarios (host work cheap or expensive).

## 5. Determinism and randomness

- The engine is deterministic.
- DZ uses a seeded xorshift RNG, seeded from (map hash, slot) and used only for tie-breaking. Results are therefore
  reproducible for paired evaluation.
