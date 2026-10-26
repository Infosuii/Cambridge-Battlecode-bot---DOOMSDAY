"""Write E-owned action schemas; specification generation only, no training."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SPECS = {
    'move': (6, ['travel', 'combat_chase', 'retreat_escape', 'spacing_position'], 2.0,
        ['canonical_dx','canonical_dy','teacher_score_delta','spawn_distance','spawn_progress','nearest_visible_enemy_distance',
         'visible_enemies_near','visible_allies_near','visible_enemy_threat','self_health_fraction','carried_gems','in_bush',
         'in_hot_zone','on_ally_spawn','in_enemy_spawn_zone','attack_range','already_walked','already_cast','round',
         'altar_distance','target_group_distance','retreat_context','position_context','bounded_sector_belief'],
        [8,8,1024,64,64,64,8,8,500,1,50,1,1,1,1,8,1,1,2000,64,64,1,1,1]),
    'combat': (7, ['visible_target_intent','spell_or_keep','reserved_sequence','reserved'], 2.0,
        ['action_kind','spell_slot_plus_one','target_distance','target_health','target_health_fraction','target_carried_gems',
         'target_strength','target_focus','target_range','visible_enemies_near','visible_allies_near','self_attack_range',
         'self_health_fraction','target_submitting','target_recalling','already_walked','already_cast','striking_dash',
         'crowd_control','area_damage','round','damage_to_target_health','self_carried_fraction','reserved_23'],
        [1,2,8,500,1,50,500,500,8,8,8,8,1,1,1,1,1,1,1,1,2000,1,1,1]),
    'engage': (8, ['final_verdict','reserved_search','reserved','reserved_2'], 2.0,
        ['fight','run','keep','teacher_fight_value','teacher_run_value','teacher_margin','time_to_death','nearest_enemy_distance',
         'self_health_fraction','carried_gems','visible_enemies_near','visible_allies_near','self_strength','self_focus',
         'heading_home','melee','has_visible_target','round','already_cast','already_walked','reserved_20','reserved_21','reserved_22','reserved_23'],
        [1,1,1,1000,1000,100,20,20,1,50,8,8,500,500,1,1,1,2000,1,1,1,1,1,1]),
    'ward': (9, ['ahead','reveal','camp','reserved'], 2.0,
        ['canonical_dx','canonical_dy','teacher_score_delta','nearest_visible_enemy_distance','visible_enemies_near','keep_ward',
         'in_bush','tile_visible','in_hot_zone','self_health_fraction','carried_gems','heading_home','round','reveal_context',
         'camp_context','reserved_15','reserved_16','reserved_17','reserved_18','reserved_19','reserved_20','reserved_21','reserved_22','reserved_23'],
        [8,8,64,8,8,1,1,1,1,1,50,1,2000,1,1,1,1,1,1,1,1,1,1,1]),
    'ts_leaf': (12, ['fight_run_leaf'], 25.0,
        ['ally_health_delta','enemy_health_delta','ally_deaths','enemy_deaths','self_health_fraction','self_spawn_distance','self_gem_delta','run_plan'],
        [1000,1000,4,4,1,64,50,1]),
}
for name, (ident, contexts, bound, names, scales) in SPECS.items():
    spec = dict(name=name, id=ident, kind='value' if name == 'ts_leaf' else 'candidate', F=len(names), K_max=1 if name=='ts_leaf' else 16,
        features=[dict(name=n,scale=s,clip=[-1,1],description=('Reserved: runtime always emits zero.' if n.startswith('reserved') else n.replace('_',' '))) for n,s in zip(names,scales)],
        contexts=contexts, residual_bound=bound, teacher_margin=0.05,
        label_sources=['instrumented_engine_1.0.3_teacher_rollouts','later_on_policy_rollouts'],
        candidate_zero='already-computed teacher choice; legal under the deterministic generator',
        nonfinite='Preserved for runtime rejection; teacher fallback.',
        padding='Rows beyond K are ignored. Reserved features are zero.',
        status='untrained', synthetic_test_data_only=True)
    if name=='ts_leaf':
        spec['interpretation']='Direct bounded residual in teacher planning-value units, added to the completed teacher leaf evaluation. At most four calls/real turn; zero on all fallbacks/shadow.'
    p=ROOT/'schemas/heads'/f'{name}.json'; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
