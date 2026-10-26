"""Generate direct-policy v2 semantic schema and pure C++ constants. No model or training work."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def field(name, scale, lo, hi, description):
    return dict(name=name, scale=scale, clip=[lo, hi], description=description)


def F(name, scale=1, lo=0, hi=4, description=None):
    return field(name, scale, lo, hi, description or name.replace('_', ' '))


HEADS = [
    dict(id=1, name='strategy', options={'0':'farm','1':'bank','2':'defend','3':'contest','4':'regroup','5':'attack','6':'retreat'},
         action_id='Intent enum0..6. No teacher-chain option.',
         narrowing='At most the seven declared intents; legality is executor availability, with exact execution recheck. Never original priority order.',
         features=[F('intent',6,0,1),F('self_hp_fraction',1,0,1),F('carried_gems',100,0,8),F('gold',1000,0,8),
                   F('remaining_rounds',2000,0,1),F('goal_walk_distance',50),F('near_allies',6,0,1),F('near_enemies',6,0,1),
                   F('ally_minus_enemy_strength',100,-4,4),F('submitted_margin',1000,-4,4),F('goal_gems',100,0,8),F('goal_threat_damage',1000)]),
    dict(id=2, name='objective', options={}, action_id='Public static group id (uint32), independent of ranking.',
         narrowing='Enumerate reachable legal groups without teacher scores. If >16, split into four canonical spatial quadrants, take the nearest four per quadrant using static distance then id; fill empty quotas by round-robin quadrants. Report excluded teacher labels; never inject them.',
         features=[F('dx',16,-4,4),F('dy',16,-4,4),F('walk_distance',50),F('reward_gems',100,0,8),F('reward_gold',1000,0,8),
                   F('camp_health',5000),F('camp_strength',100,0,8),F('capture_rounds',100),F('respawn_wait',200),
                   F('other_ally_claims',6,0,1),F('visible_enemy_count',6,0,1),F('observation_age',100)]),
    dict(id=3, name='role', options={'0':'farmer','1':'carrier','2':'fighter','3':'escort','4':'scout'}, action_id='Role enum0..4.',
         narrowing='All five roles available unless a deterministic executor precondition excludes one. Commit with explicit option start/end; no repeated forced decisions.',
         features=[F('role',4,0,1),F('self_slot',5,0,1),F('self_hp_fraction',1,0,1),F('carried_gems',100,0,8),
                   F('gold',1000,0,8),F('attack_range',10,0,2),F('near_allies',6,0,1),F('near_enemies',6,0,1),
                   F('assignment_walk_distance',50),F('active_group_claims',6,0,1),F('submitted_margin',1000,-4,4),F('remaining_rounds',2000,0,1)]),
    dict(id=4, name='bank', options={'0':'continue','1':'travel_to_altar','2':'deposit_at_altar'},
         action_id='Continue=0; travel=1+2*altar_index; deposit=2+2*altar_index. Altar indices are public static order, not teacher rank.',
         narrowing='Continue plus direct deposit options and reachable altar destinations. If >16, keep deposit options first, then nearest altars with four-quadrant diversity; no original bank verdict or bank score.',
         features=[F('bank_action',2,0,1),F('altar_dx',16,-4,4),F('altar_dy',16,-4,4),F('walk_distance',50),
                   F('carried_gems',100,0,8),F('gems_still_needed',1000,-4,4),F('remaining_rounds',2000,0,1),F('self_hp_fraction',1,0,1),
                   F('visible_enemies',6,0,1),F('threat_damage',1000),F('deposit_channel_rounds',20),F('altar_enemy_lock_state',1,-1,1,'-1 unknown,0 unlocked,1 known enemy lock')]),
    dict(id=5, name='shop', options={'0':'save','1':'item_shard','2':'consumable'},
         action_id='Save=0; item=1+SDK item_type index; consumable=1000+raw ABI id. Retired/unavailable ids are never legal.',
         narrowing='Save plus affordable explicit legal purchases. If >16, reserve up to7 distinct item families/stat categories, up to2 consumables, then fill by canonical item id with round-robin families; no complete teacher build-plan option.',
         features=[F('purchase_kind',2,0,1),F('type_id',42,0,4),F('cost',1000,0,8),F('own_gold',1000,0,8),F('owned_count',5),
                   F('health_gain',1000),F('strength_gain',100),F('focus_gain',100),F('heal_amount',1000),F('damage_gain',100),
                   F('remaining_rounds',2000,0,1),F('capacity_remaining',5)]),
    dict(id=6, name='move', options={'0':'walk','1':'ability_slot0_mobility','2':'ability_slot1_mobility','3':'hold'},
         action_id='(kind<<30)|(canonical_y<<15)|canonical_x; kind0..3, canonical coordinates0..32767. Execution separately retains world coordinates.',
         narrowing='All8 legal adjacent steps and hold. If mobility/waypoints add >16 options, retain hold plus one per compass octant per action kind, round-robin kind/octant; shortest remaining static distance then canonical id breaks narrowing ties. This is geometric narrowing, not teacher route ranking.',
         features=[F('dx',8,-4,4),F('dy',8,-4,4),F('remaining_path_distance',50),F('goal_cheb_distance',50),
                   F('enemy_attackers',6,0,1),F('camp_attackers',6,0,1),F('terrain_cover',1,0,1),F('nearest_enemy_distance',16),
                   F('nearest_ally_distance',16),F('movement_kind',3,0,1),F('ability_cooldown_after_use',20),F('carried_gems',100,0,8)]),
    dict(id=7, name='combat', options={'0':'basic_attack','1':'ability_slot0','2':'ability_slot1','3':'hold'},
         action_id='(target_handle<<2)|kind; kind0..3, handle0..0x3FFFFFFF. Hold uses handle0,kind3. Reject overflowing handles instead of masking collisions.',
         narrowing='Exact SDK-legal attack/ability/target pairs, plus hold. If >16, round-robin action kinds and spatial octants; include channeling targets within each geometric bucket, then canonical handle order. No inherited target worth/TTK/teacher score.',
         features=[F('action_kind',3,0,1),F('target_hp',1000),F('target_max_hp',1000),F('target_gems',100,0,8),F('target_distance',16),
                   F('self_hp_fraction',1,0,1),F('self_strength',100,0,8),F('target_strength',100,0,8),F('direct_damage',1000),
                   F('cooldown_after_use',20),F('target_channel_rounds',20),F('affected_visible_enemies',6,0,1)]),
    dict(id=8, name='engage', options={'0':'fight','1':'disengage','2':'hold'}, action_id='Verdict enum0..2.',
         narrowing='All three decisions, subject only to narrowly declared deterministic emergency/executor constraints. No original fight/search verdict or prior.',
         features=[F('verdict',2,0,1),F('self_hp_fraction',1,0,1),F('target_hp_fraction',1,0,1),F('visible_ally_health',1000,0,8),
                   F('visible_enemy_health',1000,0,8),F('ally_damage_per_attack',100,0,8),F('enemy_damage_per_attack',100,0,8),
                   F('nearest_enemy_distance',16),F('escape_walk_distance',50),F('carried_gems',100,0,8),F('ready_spell_count',2,0,1),F('incoming_damage',1000)]),
]


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')


def fnv(data):
    h = 2166136261
    for byte in data:
        h = ((h ^ byte) * 16777619) & 0xFFFFFFFF
    return h


def base_schema():
    heads = []
    for head in HEADS:
        if len(head['features']) != 12:
            raise ValueError(head['name'])
        heads.append(dict(head, interpretation_version=2, F=12, K_max=16, contexts=['ordinary','combat','retreat','positioning']))
    return dict(name='nfs_direct_policy_actions', schema_version=2, interpretation_version=2, F=12, K_max=16,
                order='ascending_unsigned_action_id', duplicate_ids='reject_entire_decision',
                normalization='float32(raw * float32(1 / scale)), then clip; all nonfinite raw values reject before normalization, including masked rows',
                ties='lowest legal canonical id', masks='uint8 exactly0 or1; no mandatory legal index0',
                empty='explicit error; caller enters whole-bot teacher fallback',
                teacher='optional stable-id annotation only; absent or out of set=-1; never candidate input/order/prior',
                feature_sources='own/public/static-map/current-visible/legally-remembered-with-age only; no future targets or teacher preference scores',
                narrowing='Caller generates/narrows using each head rule BEFORE this pure builder; count>16 rejects instead of silently truncating',
                hash='FNV1a32 of canonical sorted-key ASCII JSON; per-head excludes own action_hash; combined excludes top action_schema_hash and every head action_hash', heads=heads)


def main():
    schema = base_schema()
    combined = fnv(canonical(schema))
    for head in schema['heads']:
        head['action_hash'] = fnv(canonical(head))
    schema['action_schema_hash'] = combined
    (ROOT / 'schemas/policy_v2.json').write_text(json.dumps(schema, indent=2) + '\n', encoding='utf-8')
    constants = []
    constants.append('// GENERATED from schemas/policy_v2.json by archive/agents/v2_candidates/generate_schema.py.')
    constants.append('inline constexpr std::uint32_t kActionSchemaHash = 0x%08Xu;' % combined)
    by_id = {h['id']:h for h in schema['heads']}
    constants.append('inline constexpr std::uint32_t kHeadActionHash[13] = {' + ','.join('0x%08Xu' % by_id[i]['action_hash'] if i in by_id else '0u' for i in range(13)) + '};')
    constants.append('inline constexpr FeatureSpec kFeatureSpec[9][kF] = {')
    constants.append('    {}, // no direct draft head; inherited draft remains separate')
    for hid in range(1,9):
        head = by_id[hid]
        values = ['{1.0f/%s.0f,%s.0f,%s.0f}' % (f['scale'], f['clip'][0], f['clip'][1]) for f in head['features']]
        constants.append('    {' + ','.join(values) + '}, // ' + head['name'])
    constants.append('};')
    path = ROOT / 'bot/src/nn_policy_candidates.h'
    text = path.read_text(encoding='utf-8')
    a, b = text.index('// BEGIN GENERATED\n'), text.index('// END GENERATED')
    text = text[:a] + '// BEGIN GENERATED\n' + '\n'.join(constants) + '\n' + text[b:]
    path.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    main()
