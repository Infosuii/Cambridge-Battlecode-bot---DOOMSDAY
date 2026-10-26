"""Agent A: assemble archive/agents/A/sdk_facts.json from the SDK header (line references) and the runtime probe
(archive/agents/A/evidence/sdk_probe_facts.jsonl, produced by archive/agents/A/probe/a_sdk_dump.cpp in one official match).

    python tools/audit_sdk_facts.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from nfs import engine  # noqa: E402

SDK = 'sdk/cpp/cambc.h'
IMP = 'sdk/cpp/imports.h'
KIND = {0: 'none', 1: 'attack_reset', 2: 'damage', 3: 'aoe_damage', 4: 'cc', 5: 'heal', 6: 'dash', 7: 'shield'}
TARGET_BITS = [(1, 'camps'), (2, 'enemies'), (4, 'allies'), (8, 'self'), (16, 'ground')]
PASSIVE = {0: 'none', 1: 'bonus_gold', 2: 'remote_shop', 3: 'gem_focus', 4: 'splash_attack', 5: 'health_strength',
           6: 'reset_cooldowns_on_kill', 7: 'retaliation', 8: 'stun_immunity', 10: 'missing_health_damage'}
ITEM_PASSIVE = {0: None, 1: 'monster', 2: 'durability', 3: 'treasure', 4: 'jungle', 5: 'home'}



_LINES = {f: (ROOT / f).read_text(encoding='utf-8').splitlines() for f in (SDK, IMP)}


def L(pattern: str, f: str = SDK, nth: int = 0) -> str:
    """Line reference of the nth line matching `pattern` (regex) in the SDK file; fails loudly if absent."""
    hits = [i + 1 for i, s in enumerate(_LINES[f]) if re.search(pattern, s)]
    if len(hits) <= nth:
        raise SystemExit(f'SDK pattern not found: {pattern!r} in {f}')
    return f'{f}:{hits[nth]}'


def ref(line: int | str, f: str = SDK) -> str:
    return f'{f}:{line}'


def ability(a: dict) -> dict:
    out = {'kind': KIND.get(a['kind'], a['kind']), 'max_cooldown_rounds': a['cooldown'],
           'valid_targets': [n for b, n in TARGET_BITS if a['targets'] & b],
           'exclusive_with_movement': bool(a['attributes'] & 1), 'abi_max_charges': a['max_charges']}
    for k in ('range', 'radius', 'modifier', 'duration', 'enhanced_attack'):
        if k in a:
            out[k] = bool(a[k]) if k == 'enhanced_attack' else a[k]
    return out


def main() -> int:
    probe = [json.loads(l) for l in (ROOT / 'archive/agents/A/evidence/sdk_probe_facts.jsonl').read_text().splitlines() if l.strip()]
    by = {}
    for r in probe:
        by.setdefault(r['rec'], []).append(r)
    settings = by['settings'][0]
    mem = [r for r in by['memory'] if r['is_draft'] == 1][0]
    turn = by['turn']
    facts = {
        '_doc': 'Verified SDK facts (Agent A). "sdk" = line in sdk/cpp/cambc.h or imports.h; "runtime" = value read from the '
                'engine through the SDK by archive/agents/A/probe/a_sdk_dump.cpp in one official match (engine 1.0.3, cambc 3.0.5, '
                'map 00ambush, --release); raw records in archive/agents/A/evidence/sdk_probe_facts.jsonl. Values the SDK reads at '
                'runtime (settings, designs, items) could differ on another engine build: read the constants at runtime.',
        'engine': {'cli': engine.cli_version(), 'engine_version_in_summaries': '1.0.3', 'probe_match': 'artifacts/tmp/A/probe/match'},
        'game_settings': {
            'sdk': L(r'^struct game_settings') + ' (struct game_settings), ' + L(r'^namespace constants') + ' (cambc::constants)',
            'runtime': {k: v for k, v in settings.items() if k != 'rec'},
            'notes': [
                f'ward_charges and the control-ward radii exist only in the raw settings record ({L(r"active_wards, ward_charges")}); cambc::constants '
                f'does not expose them and the SDK has no control-ward placement API (only ordinary place_ward, {L(r"bool place_ward\(vec2")}; '
                f'{L(r"struct control_ward_info", IMP)} control_ward_info is an ABI record without a wrapper).',
                f'tp_scroll_time is documented as retired/unused ({L(r"Retired teleport-scroll")}).',
                f'submit duration = max(minimum, base + ceil(gems * multiplier)) per the comments at {L(r"submit_gem_duration_multiplier =")}..{L(r"submit_gem_minimum_duration =")} '
                '(exact rounding beyond "rounded up" is not documented).',
            ],
        },
        'scoring_and_win': {
            'winning_gems': settings['winning_gems'], 'max_rounds': settings['max_rounds'],
            'sdk': [L(r'inline const std::uint32_t max_rounds') + ' max_rounds: "Round limit before the game resolves its winner using tiebreakers"',
                    L(r'inline const std::uint32_t winning_gems') + ' winning_gems: "Submitted gems required for a team to win"',
                    L(r'global_submitted_gems\(team side\)') + ' global_submitted_gems(team) (both teams readable)'],
            'tiebreak': 'NOT documented in the SDK. Observed: 01boss-battle original vs original ended 0-0 at round 2000 '
                        'with outcome teamB (tests/fixtures/teacher/reference_digests.json); the rule itself is unknown.',
            'summary_fields': {'match': ['engineBuildHash', 'engineVersion', 'finalInput', 'finalRoundPartial', 'finalSubstep',
                                         'height', 'width', 'mapHash', 'metricSemanticsVersion', 'outcome (teamA|teamB)',
                                         'roundsCompleted', 'roundsStarted', 'seed (per map)'],
                               'teams': ['team', 'submittedGems'],
                               'champions[].metrics': ['assists', 'championDamageDone', 'championDamageTaken', 'collectedGems',
                                                       'deaths', 'earnedGold', 'gems', 'gold', 'healingDone', 'healingReceived',
                                                       'kills', 'monsterDamageDone', 'monsterDamageTaken', 'saleRefunds',
                                                       'shieldingDone', 'spentGold', 'submittedGems'],
                               'champions[]': ['consumables', 'consumablesBought', 'id', 'items', 'itemsBought', 'name', 'team'],
                               'other_top_level': ['championTimelines', 'teamTimelines', 'heatmaps', 'events', 'roster',
                                                   'diagnostics.botFaults', 'formatVersion'],
                               'event_kinds': ['assist', 'botFault', 'buyConsumable', 'buyItem', 'campClear', 'death',
                                               'fuelExhausted', 'gemCollection', 'gemLoss', 'gemSubmission', 'itemCombination',
                                               'kill', 'resignation', 'sellItem', 'wardPlacement'],
                               'source': 'artifacts/tmp/A/probe/match/summary.json (cambc run --statistics --json)'},
        },
        'champions': {
            'sdk': [L(r'^enum class champion_type') + ' champion_type (13 physical)', L(r'^enum class champion_draft') + ' champion_draft (12 picks; cassi_and_issac is one pick)',
                    L(r'^enum class passive_type') + ' passive_type', L(r'champion_designs =') + ' champion_designs (available in draft)',
                    L(r'^class ability$') + ' ability (slot 0/1, cooldown(), is_ready(), valid_tiles(), use())',
                    L(r'^struct ability_properties') + ' ability_properties: max_cooldown, valid_targets, exclusive_with_movement',
                    L(r'^struct champion_stats', IMP) + ' champion_stats'],
            'runtime': [],
            'notes': [f'Every champion has exactly two ability slots ({L(r"std::array<ability, 2>\s+ability_slots")} std::array<ability,2>).',
                      f'cooldown() = remaining owner turn-end ticks, 0 = ready ({L(r"remaining owner turn-end ticks")}); max_cooldown is the configured value ({L(r"Configured ability cooldown in rounds")}).',
                      'ABI field max_charges is 0 for every ability (runtime); the public SDK exposes no charges, only the error code '
                      f'invalid_action_spell_cast_no_charges ({L(r"invalid_action_spell_cast_no_charges = ")}). Treat abilities as cooldown-only.',
                      f'Focus scales spell effects: damage_amount() = Focus-scaled, includes caster bonuses ({L(r"Query Focus-scaled damage")}); '
                      f'dash landing damage = caster Focus * modifier ({L(r"modifier: Landing damage multiplier")}).',
                      f'exclusive_with_movement: casting and normal movement are mutually exclusive in a round ({L(r"Casting and normal movement are mutually exclusive")}); errors '
                      f'invalid_action_spell_cast_already_moved / invalid_action_move_exclusive_spell_cast ({L(r"invalid_action_spell_cast_already_moved = ")}, {L(r"invalid_action_move_exclusive_spell_cast = ")}).',
                      f'One cast per turn: invalid_action_spell_cast_already_cast ({L(r"invalid_action_spell_cast_already_cast = ")}).',
                      f'Cassi and Issac: one draft pick, two champions; if either dies both die ({L(r"One pick that drafts both Cassi")}, {L(r"Ranged spellcaster half of the Cassi")}).'],
        },
        'camps': {'sdk': [L(r'^enum class camp_type') + ' camp_type (doc comments give health/strength/range)', L(r'^class camp_state') + ' camp_state dead/alive(awake)/asleep',
                          L(r'struct camp_group_alive') + ' camp_group_state alive / reward_available / respawning{timer}',
                          L(r'camp_group_state state\(\) const') + ' camp_group.state() needs vision of a member spawn tile',
                          L(r'inline std::vector<map::camp_group> camp_groups\(\)') + ' vision::camp_groups()', L(r'inline std::vector<camp_group> camp_groups\(\)') + ' map::camp_groups() (static, also in draft)'],
                  'runtime': [], 'capture_time': settings['capture_time'], 'camp_sleep_time': settings['camp_sleep_time'],
                  'notes': [f'Rewards are per camp group: gold_value()/gem_value() ({L(r"std::uint32_t gold_value\(\) const")}); a defeated group must be '
                            'captured (capture_time rounds) before the reward; then it respawns (max_respawn_timer).',
                            'Camp attack range from design (wolf 3, elk 4, monolith 5, golem 4; clusters 3 but strength 0).']},
        'basic_attack': {'sdk': [L(r'void attack\(const unit& target\)') + ' attack(unit) / attack(altar_lock)', L(r'virtual std::int32_t attack_range') + ' unit::attack_range (Chebyshev; melee = 1)',
                                 L(r'champion_state::can_attack\{') + ' champion_state::can_attack',
                                 L(r'invalid_action_attack_already_attacked = ') + ' invalid_action_attack_already_attacked (one basic attack per turn unless an attack_reset ability restores it)'],
                         'notes': ['Ranged basic attacks end movement in the original bot\'s experience (bot.cpp comments) - not documented in the SDK.',
                                   f'Altar locks are destroyed by basic attacks (altar_lock_hits = {settings["altar_lock_hits"]}, {L(r"inline const std::uint32_t altar_lock_hits")}).']},
        'movement': {'sdk': [L(r'bool move\(vec2 delta\)') + ' move(delta)', L(r'bool move_absolute\(vec2') + ' move_absolute', L(r'bool move_towards\(vec2 target\) const;') + ' move_towards (SDK BFS, ' + L(r'inline bool champion::move_towards') + ')',
                             L(r'^struct ability_dash') + ' ability_dash: range (diagonals count 1), radius, modifier, duration; legal dash path required'],
                     'runtime': {'base_move_speed_all_champions': sorted({c['base_move_speed'] for c in by['champion']}),
                                 'live_move_speed_turn1': sorted({t['move_speed'] for t in turn})},
                     'notes': [f'move returns false (without spending the move) for a newly revealed hidden obstruction; known invalid destinations throw (doc above {L(r"bool move\(vec2 delta\)")}).',
                               f'Blocked for move_towards: walls, holes, altars, enemy spawn region, visible units, teleport reservations ({L(r"Move to the reachable tile on a shortest path")}).',
                               f'One move per turn: invalid_action_move_already_moved ({L(r"invalid_action_move_already_moved = ")}).']},
        'wards': {'sdk': [L(r'bool place_ward\(vec2') + ' place_ward(tile)', L(r'ward_positions\(\) const') + ' ward_positions() (self)', L(r'std::int32_t ward_cooldown\(\) const') + ' ward_cooldown() (self)',
                          L(r'void ward_placement_tiles_into') + ' ward_placement_tiles (Chebyshev radius ward_placement_radius)', L(r'^class ward$') + ' ward snapshot (owner, team, remaining_time)',
                          L(r'inline std::vector<cambc::ward> wards\(\)') + ' vision::wards / ward_tiles / has_ward'],
                  'runtime': {k: settings[k] for k in ('active_wards', 'ward_charges', 'ward_cooldown', 'ward_lifetime',
                                                       'ward_vision_radius', 'ward_placement_radius', 'control_ward_vision_radius',
                                                       'control_ward_placement_radius')},
                  'notes': [f'active_wards = 1: one live ward per champion (shared active placement limit, {L(r"inline const std::uint32_t active_wards")}).',
                            f'ward_lifetime = -1: ordinary wards do not expire ({L(r"inline const std::int32_t ward_lifetime")}).',
                            f'Allied ward already on the tile: invalid_action_place_ward_ally_ward_present ({L(r"invalid_action_place_ward_ally_ward_present = ")}).',
                            'Control wards: settings only; no API in this SDK.']},
        'items_and_shop': {
            'sdk': [L(r'^class item_type') + ' item_type (42 items: 7 families x 3 stats x shard/emblem)', L(r'std::uint32_t cost\(\) const;') + ' item_type queries (cost, combine_count, result, points, passive, is_purchasable)',
                    L(r'bool can_buy\(item_type') + ' can_buy(item,count): shop allowed now, purchasable, gold >= cost*count',
                    L(r'bool can_buy\(consumable_type') + ' can_buy(consumable): shop allowed, gold, count < carry_limit', L(r'bool can_sell\(\) const') + ' can_sell()',
                    L(r'void buy\(item_type') + ' buy(item,count)', L(r'void buy\(consumable_type') + ' buy(consumable)', L(r'void sell\(item_type') + ' sell(item,count) (Tavi only, on spawn)',
                    L(r'invalid_action_buy_item_not_on_spawn = ') + ' invalid_action_buy_item_not_on_spawn: "Items can only be bought on spawn or while dead"',
                    L(r'remote_shop,') + ' passive remote_shop (Tavi): buy equipment away from spawn and sell it on spawn',
                    L(r'invalid_action_sell_not_tavi = ') + '/' + L(r'invalid_action_sell_not_on_spawn = ') + ' sell errors: not Tavi / not on spawn',
                    L(r'buff_restrictions::shop\{') + ' buff_restrictions::shop can forbid buying'],
            'runtime_items': [{'id': r['id'], 'name': r['name'], 'cost': r['cost'], 'purchasable': bool(r['purchasable']),
                               'stat_points': {'health': r['health'], 'strength': r['strength'], 'focus': r['focus']},
                               'passive': ITEM_PASSIVE.get(r['passive']), 'passive_magnitude': r['passive_magnitude'],
                               'combine_count': r['combine_count'], 'combines_into': r['result'] if r['combine_count'] else None}
                              for r in by['item']],
            'notes': ['Shards cost 30 and are purchasable; emblems (cost 150) are not purchasable: five shards of one family/stat '
                      'combine into the emblem (combine_count 5; summary event itemCombination).',
                      'Stat points are counts of the champion\'s growth (e.g. health 1 = one health_growth step), per the item comments '
                      f'"adds the champion\'s X growth" ({L(r"Monster shard: 30 gold, adds the champion")}).',
                      'Emblem passives (runtime magnitudes): monster +10% camp damage, durability -10% incoming damage, treasure +20% gold, '
                      'jungle -30% camp damage taken, home recall 3 turn ends instead of 5; power/bruiser emblems have no passive '
                      '(they count as extra stat shards).',
                      f'Inventory limit for items: only the error invalid_action_buy_item_inventory_full exists ({L(r"invalid_action_buy_item_inventory_full = ")}); the size is '
                      f'not exposed by the SDK. stats_overflow error also exists ({L(r"invalid_action_buy_item_stats_overflow = ")}).',
                      f'item cost = full value, refunded in full when Tavi sells ({L(r"Get the full value in gold")}).']},
        'consumables': {'sdk': [L(r'^struct consumable_info$') + ' consumable_type tp_crystal / altar_lock, consumable_info{cost, carry_limit}',
                                L(r'raw_consumable_ids\{') + ' raw ABI ids {0, 2} (raw id 1 = retired teleport scroll)', L(r'^class consumable$') + ' consumable::use(tile)'],
                        'runtime_raw': by['consumable_raw'],
                        'runtime': {'tp_crystal': {'cost': 10, 'carry_limit': 1, 'channel_rounds': settings['tp_crystal_time'],
                                                   'doc': 'channel three turn ends, then flash to a reserved tile within range 3 (' + L(r'Teleport crystal: channel') + ')'},
                                    'altar_lock': {'cost': 10, 'carry_limit': 1, 'hits_to_destroy': settings['altar_lock_hits'],
                                                   'doc': 'placed on an altar within 2 tiles; blocks enemy tributes until destroyed by basic attacks (' + L(r'Altar lock: placed on an altar') + ')'}}},
        'gems_tribute_altar_recall': {
            'sdk': [L(r'void submit_gems\(vec2') + ' submit_gems(altar): channel; range = submit_gems_range (Chebyshev)', L(r'void cancel_submit_gems') + ' cancel_submit_gems',
                    L(r'void recall\(\) const') + ' recall() channel to spawn', L(r'void cancel_recall') + ' cancel_recall', L(r'remaining_channel_time\(\) const') + ' remaining_channel_time',
                    L(r'champion_state::recalling\{') + ' champion_state recalling / submitting_gems / teleporting / *_started / *_cancelled',
                    L(r'invalid_action_submit_gems_altar_locked = ') + ' invalid_action_submit_gems_altar_locked', L(r'Prevents actions and interrupts channels') + ' stun prevents actions and interrupts channels',
                    L(r'inline const float spawn_healing') + ' spawn_healing (fraction of max health per round on own spawn)'],
            'runtime': {k: settings[k] for k in ('submit_gems_range', 'submit_gem_duration_multiplier', 'submit_gem_base_duration',
                                                 'submit_gem_minimum_duration', 'recall_time', 'respawn_time', 'spawn_healing',
                                                 'kill_gold', 'assist_gold', 'passive_gold')},
            'notes': ['Gem carriers lose gems on death (summary event gemLoss); the killer side may collect them (bot.cpp comments; '
                      'pickup mechanics are not documented in the SDK).',
                      'Passive gold = 0 and assist gold = 0 at runtime: gold comes from camps and kills (kill_gold 100).',
                      f'Marcella gains 2 gold per gem tributed; Prism gains 1.5 focus per carried gem ({L(r"marcella_tribute_gold_per_gem")}, {L(r"prism_focus_per_gem")}).']},
        'shared_and_draft_memory': {
            'sdk': [L(r'^class shared_memory_buffer') + ' shared_memory_buffer: bounds-checked, reads/writes always reach the host',
                    L(r'^class draft_memory_buffer') + ' draft_memory_buffer: snapshot captured at startup; assignment submits during the draft only; '
                                     'oversized input truncated, shorter input keeps the remaining bytes',
                    L(r'invalid_action_memory_draft_frozen = ') + ' invalid_action_memory_draft_frozen', L(r'shared_memory_capacity = ', IMP) + ' shared_memory_capacity'],
            'runtime': {'shared_memory_bytes': settings['shared_memory_bytes'], 'draft_memory_bytes': settings['draft_memory_bytes'],
                        'shared_memory_capacity_api': mem['shared_memory_capacity'], 'draft_memory_snapshot_size': mem['draft_memory_snapshot_size']},
            'notes': ['Shared memory is 8 bytes per team (whole team); the original uses all 64 bits (bot.h:21-28).',
                      'Draft memory is 1024 bytes, writable only during the draft, readable by champions (snapshot at guest start).',
                      'Each champion and the draft run as separate guests (probe: every champion guest printed its own records), so '
                      'process memory is per champion; only shared/draft memory crosses guests.']},
        'visibility': {
            'sdk': [L(r'inline std::vector<cambc::champion> champions\(team side\)') + ' cambc::champions(team): all handles incl. out of vision', L(r'bool is_alive\(\) const$') + ' champion::is_alive (works without vision)',
                    L(r'bool is_visible\(\) const override', nth=1) + ' is_visible', L(r'champion_type champion_name\(\) const') + ' team()/champion_name() readable without vision',
                    L(r'enum_map<item_type> item_count\(\) const') + ' item_count requires runtime (visible) champion', L(r'std::uint32_t gem_count\(\) const') + ' gem_count (visible)', L(r'std::uint32_t gold_count\(\) const') + ' gold_count self only',
                    L(r'inline bool in_vision') + ' vision::in_vision (includes own ward vision)', L(r'inline std::vector<cambc::champion> champions\(team side\)', nth=1) + ' vision::champions/camps/camp_groups',
                    L(r'api_not_in_vision = ') + ' api_not_in_vision error', L(r'camp_group_state state\(\) const') + ' camp group state needs a visible member tile',
                    L(r'void visible_tiles_from_into\(vec2 position, bitboard& out\) const') + ' visible_tiles_from (hypothetical vision)', L(r'^namespace vision') + ' vision occupancy masks',
                    L(r'inline const std::uint32_t tile_reveal_rounds') + ' tile_reveal_rounds (collision reveal)'],
            'notes': ['Observable about enemies: identity/type/team and alive state for all; position, health, strength, focus, '
                      'state flags, buffs, cooldowns (sdk_champion_cooldown is called on enemies by the original: bot.cpp:2874 (handle_enemies burst estimate)), '
                      'carried gems and items only while visible; gold never.',
                      'Enemy submitted gems are global (global_submitted_gems).',
                      'Enemy wards, teleport reservations and altar locks are observable only when visible.']},
        'fuel': {'sdk': [L(r'std::uint64_t fuel_remaining\(\)') + ' fuel_remaining(): first draft turn 10x, each champion first turn 2x',
                         L(r'define debug_block') + ' debug_block pauses fuel only in CAMBC_DEBUG builds; skipped in --release'],
                 'runtime': {'first_draft_turn_after_probe_setup': mem['fuel_remaining'],
                             'champion_turn1_after_one_record': sorted({t['fuel_remaining'] for t in turn if t['round'] == 1}),
                             'champion_turn_later_after_one_record': sorted({t['fuel_remaining'] for t in turn if t['round'] > 1})},
                 'notes': ['Measured: std::printf costs ~65 fuel per output character in this Wasm build (first probe: the 937,830-fuel '
                           'first draft turn exhausted after ~14 KB of output). Any stdout logging must be budgeted.',
                           'Fuel exhaustion is reported as summary events fuelExhausted; team-<x>.fuel in the replay bundle is a '
                           'per-turn fuel trace (used by tools/audit_equivalence.py).']},
        'map_and_symmetry': {'sdk': [L(r'^enum class symmetry') + ' symmetry horizontal/vertical/rotational180', L(r'inline vec2 reflect_horizontal\(vec2 p\)') + ' reflect/rotate helpers',
                                     L(r'inline const bitboard cached_walls') + ' walls/bushes/holes/altars/spawn_region (static)'],
                             'runtime_00ambush': {'w': mem['map_w'], 'h': mem['map_h'], 'symmetry': mem['symmetry'],
                                                  'camp_groups': len(by.get('camp_group', []))}},
        'draft': {'sdk': [L(r'std::uint32_t team_size\(\)') + ' draft::team_size', L(r'current_draft\(team side\)') + ' draft::current_draft(team) (enemy picks visible)',
                          L(r'inline void pick\(champion_draft') + ' draft::pick', L(r'draft_duplicate_champion = ') + ' draft_duplicate_champion', L(r'draft_already_picked = ') + ' draft_already_picked'],
                  'runtime': {'team_size_5v5': mem['draft_team_size'], 'allies_in_game_with_cassi_issac': 'up to team_size + 1 champions'}},
        'scheduling': {'sdk': [L(r'void set_priority') + ' set_priority (next round, persists)', L(r'prev_priority\(\) const') + ' prev_priority / priority']},
    }
    for c in by['champion']:
        facts['champions']['runtime'].append({
            'type': c['type'], 'name': c['name'], 'passive': PASSIVE.get(c['passive'], c['passive']),
            'attack': 'ranged' if c['attack_type'] == 1 else 'melee', 'attack_range': c['base_attack_range'],
            'vision_radius': c['vision_radius'], 'move_speed': c['base_move_speed'],
            'health': [c['base_health'], c['health_growth']], 'strength': [c['base_strength'], c['strength_growth']],
            'focus': [c['base_focus'], c['focus_growth']], 'camp_damage_multiplier': c['camp_damage_multiplier'],
            'abilities': [ability(a) for a in c['abilities']]})
    for c in by['camp']:
        facts['camps']['runtime'].append({'type': c['type'], 'name': c['name'], 'health': c['base_health'], 'strength': c['base_strength'],
                                         'attack_range': c['base_attack_range'], 'vision_radius': c['vision_radius'],
                                         'move_speed': c['base_move_speed']})
    engine.write_json(ROOT / 'archive/agents/A/sdk_facts.json', facts)
    print('wrote archive/agents/A/sdk_facts.json', len(facts['champions']['runtime']), 'champions', len(facts['items_and_shop']['runtime_items']), 'items')
    return 0


if __name__ == '__main__':
    sys.exit(main())
