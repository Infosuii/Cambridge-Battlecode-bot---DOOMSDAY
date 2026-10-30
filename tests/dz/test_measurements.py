"""Regression checks for interpretation of native evidence, independent of a bot."""
import importlib.util
import json
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location('dz_runner', Path(__file__).resolve().parents[2]/'tools/dz.py')
dz = importlib.util.module_from_spec(spec); spec.loader.exec_module(dz)

class Measurements(unittest.TestCase):
    def test_duel_fixture_rejects_missing_or_mismatched_outcomes(self):
        names=['duel_outcome','duel_elapsed','duel_hp','duel_basics','duel_casts','duel_isolated']
        text='\n'.join(f'CT_CHECK name={n} pass=1' for n in names)+'\nCT_DUEL_QUOTE sample=0 heart=1 other=0 round=10 status=1 rounds=20\nCT_DUEL_RESULT sample=0 won=0 rounds=20'
        self.assertTrue(dz.diagnostic_checks(text,'duel')['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('won=0','won=1'),'duel')['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('CT_CHECK name=duel_hp pass=1',''),'duel')['passed'])
        self.assertFalse(dz.diagnostic_checks(text+'\nCT_CHECK name=duel_hp pass=0','duel')['passed'])

    def test_shield_fixture_requires_complete_matched_successful_checks(self):
        names=['shield_outcome','shield_elapsed','shield_hp','shield_basics','shield_casts','shield_isolated']
        text='\n'.join(f'CT_CHECK name={n} pass=1' for n in names)+'\nCT_SHIELD_QUOTE sample=0 heart=1 existing=0 round=10 status=0 rounds=40\nCT_SHIELD_RESULT sample=0 cleared=1 rounds=40'
        self.assertTrue(dz.diagnostic_checks(text,'shield')['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('CT_CHECK name=shield_hp pass=1',''),'shield')['passed'])
        self.assertFalse(dz.diagnostic_checks(text+'\nCT_CHECK name=shield_hp pass=0','shield')['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('cleared=1','cleared=0'),'shield')['passed'])
        self.assertFalse(dz.diagnostic_checks(text+'\nCT_SHIELD_RESULT sample=0 cleared=1 ','shield')['passed'])

    def test_cumulative_error_counters_catch_dropped_error_lines(self):
        text='DZ_COUNTS round=100 slot=0 actions=2 modules=1 stale=0\nDZ_COUNTS round=200 slot=0 actions=2 modules=1 stale=0\nDZ_COUNTS round=200 slot=1 actions=1 modules=0 stale=0'
        self.assertEqual(dz.caught_errors(text),(3,1))
        self.assertEqual(dz.caught_errors('DZ_ACTION_ERROR x\nDZ_ACTION_ERROR x\nDZ_COUNTS round=100 slot=0 actions=0 modules=0 stale=0'),(2,0))
    def test_objective_fixture_requires_its_exact_model_checks(self):
        names=['tribute_passive_setup','tribute_financed','tribute_bag_prepared','tribute_baseline_timer','tribute_cancel_retains_bag','tribute_item_created','tribute_same_bag','tribute_completed','tribute_live_duration','tribute_passive_effect']
        text='\n'.join(f'CT_CHECK name={n} pass=1' for n in names)+'\nCT12_BASE bag=70 timer=7\nCT12_ITEM active=1 magnitude=0.330000013\nCT12_RESULT bag=70 base_timer=7 initial_timer=5 elapsed=5 banked_delta=70 gold_delta=0 active=1 magnitude=0.330000013'
        self.assertTrue(dz.diagnostic_checks(text,'tribute-passive')['passed'])
        self.assertFalse(dz.diagnostic_checks(text,'objective-tribute')['passed'])
        math='\nCT_MATH enabled=1\nCT_CHECK name=math_tribute_delay pass=1'
        self.assertTrue(dz.diagnostic_checks(text+math,'objective-tribute')['passed'])
        self.assertFalse(dz.diagnostic_checks(text+math+'\nCT_CHECK name=math_tribute_delay pass=0','objective-tribute')['passed'])
        self.assertFalse(dz.diagnostic_checks(text+math+math,'objective-tribute')['passed'])
    def test_group_visibility_requires_dead_member_and_hidden_capturer_evidence(self):
        text='\n'.join(f'CT_CHECK name={n} pass=1' for n in ['single_spawn_setup','single_spawn_position','visible_camp_full_health'])+'\nCT10_QUERY name=visible_camp_health accepted=1 value=120 code=0\nCT10_QUERY name=hidden_camp_health accepted=0 value=0 code=97\n'
        text+='\n'.join(f'CT10_SAMPLE round={r} spawns=1 live=1 group=1 capture=0 timer=5 actor_visible=0' for r in range(1,7))+'\n'
        text+='\n'.join(f'CT10_SAMPLE round={r} spawns=1 live=0 group=1 capture=0 timer=5 actor_visible=0' for r in range(7,13))+'\nCT10_SAMPLE round=13 spawns=1 live=0 group=2 capture=3 timer=2 actor_visible=0\nCT10_SAMPLE round=14 spawns=1 live=0 group=3 capture=0 timer=5 actor_visible=0'
        opponent='CT_CHECK name=single_spawn_actor_receipt pass=1\nCT10_ORDER seen_member_first=1'
        self.assertTrue(dz.diagnostic_checks(text,'group-visibility-first',opponent)['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('live=0 group=1','live=1 group=1'),'group-visibility-first',opponent)['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('capture=3 timer=2 actor_visible=0','capture=3 timer=2 actor_visible=1'),'group-visibility-first',opponent)['passed'])
        self.assertFalse(dz.diagnostic_checks(text,'group-visibility-first','')['passed'])
    def test_draft_suspension_requires_a_new_round_and_all_intended_picks(self):
        text='CT_DRAFT_BURN prefix=0 round=0\nCT_DRAFT_RESUME prefix=1 round=1 original_round=0\n'+'\n'.join(f'CT_DRAFT_CHOICE prefix={i} pick={p}' for i,p in enumerate([11,2,6]))+'\n'+'\n'.join(f'CT_DRAFT_PLAY body={i} type={t} picks=3' for i,t in enumerate([12,2,7]))
        self.assertTrue(dz.diagnostic_checks(text,'draft-stale')['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('prefix=1 pick=2','prefix=1 pick=0'),'draft-stale')['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('round=1 original_round=0','round=0 original_round=0'),'draft-stale')['passed'])
        second=text.replace('BURN prefix=0 round=0','BURN prefix=1 round=1').replace('RESUME prefix=1 round=1 original_round=0','RESUME prefix=2 round=2 original_round=1')
        self.assertTrue(dz.diagnostic_checks(second,'draft-stale')['passed'])
    def test_tribute_rounds_base_timer_before_applying_reduction(self):
        names=['tribute_passive_setup','tribute_financed','tribute_bag_prepared','tribute_baseline_timer','tribute_cancel_retains_bag','tribute_item_created','tribute_same_bag','tribute_completed','tribute_live_duration','tribute_passive_effect']
        def transcript(bag,base,live,active=1):
            mag='0.330000013' if active else '0'
            return '\n'.join(f'CT_CHECK name={n} pass=1' for n in names)+f'\nCT12_BASE bag={bag} timer={base}\nCT12_ITEM active={active} magnitude={mag}\nCT12_RESULT bag={bag} base_timer={base} initial_timer={live} elapsed={live} banked_delta={bag} gold_delta=0 active={active} magnitude={mag}'
        for bag,base,live in [(7,1,1),(14,2,2),(21,3,3),(35,4,3),(98,10,7)]:
            self.assertTrue(dz.diagnostic_checks(transcript(bag,base,live),'tribute-passive')['passed'])
            self.assertTrue(dz.diagnostic_checks(transcript(bag,base,base,0),'tribute-passive')['passed'])
        self.assertFalse(dz.diagnostic_checks(transcript(14,2,1),'tribute-passive')['passed'])
        self.assertFalse(dz.diagnostic_checks(transcript(98,10,7).replace('gold_delta=0','gold_delta=1'),'tribute-passive')['passed'])
        self.assertFalse(dz.diagnostic_checks(transcript(98,10,7)+'\nCT12_OBSERVATION_ONLY effect_not_asserted=1','tribute-passive')['passed'])
    def test_capture_timer_requires_initialization_phase_and_complete_progress(self):
        rows=[('baseline_gold',0,0,0,240,240,240),('gem_7_floor',7,7,7,0,0,0),('gem_14_floor',14,14,14,0,0,0),('gold_cluster_bonus',0,0,0,20,20,20),('wolf_reward_unchanged',4,4,4,40,40,40)]
        text='CT13_ACTOR vesper=0 bonus_gold_percent=0\nCT13_ITEM prospector=0\nCT_CAP_ITEM active=1 timer=3\n'+'\n'.join('CT13_REWARD label=%s base_gems=%d actual_gems=%d expected_gems=%d base_gold=%d actual_gold=%d expected_gold=%d'%r for r in rows)+'\n'+'\n'.join(f'CT_CHECK name={n} pass=1' for n in [r[0] for r in rows]+['item_created','prospector_setup'])
        for i,row in enumerate(rows):
            label=row[0];entered=20*i+10;timer=5 if i==0 else 3
            text+=f'\nCT_CAP_ENTER label={label} round={entered} all_dead=1 onsite=1\nCT_CAP_RESULT label={label} entered={entered} captured={entered+timer+1} elapsed={timer+1} configured={timer}'
            text+=f'\nCT_CAP_STEP label={label} round={entered} timer=5 state=4'
            text+='\n'+'\n'.join(f'CT_CAP_STEP label={label} round={entered+j+1} timer={timer-j} state=1' for j in range(timer))
        self.assertTrue(dz.diagnostic_checks(text,'capture-time')['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('elapsed=4','elapsed=3'),'capture-time')['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('timer=2 state=1','timer=3 state=1'),'capture-time')['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('CT_CAP_ENTER','missing'),'capture-time')['passed'])
    def test_camp_modifiers_need_real_samples_and_multiplicative_reductions(self):
        names=['modifier_setup','modifier_gold_captured','modifier_items_created','modifier_feasible','modifier_hit_damage','modifier_phase_damage','modifier_attack_count','modifier_elapsed','modifier_total_damage','modifier_isolated_fixed_stats']
        checks='\n'.join(f'CT_CHECK name={n} pass=1' for n in names)
        text=checks+'\nCT_MOD_SETUP monster=0 jungle=0 durability=0 strength=70 camp_hp=1350 camp_strength=20 hit=70 incoming=20 predicted=20\n'+'\n'.join(f'CT_MOD_PHASE round={r} delta=20' for r in range(11,30))+'\nCT_MOD_RESULT attacks=20 elapsed=19 hp_lost=380 expected_damage=380'
        self.assertTrue(dz.diagnostic_checks(text,'camp-mods')['passed'])
        self.assertFalse(dz.diagnostic_checks(checks,'camp-mods')['passed'])
        combined=text.replace('jungle=0 durability=0','jungle=1 durability=1').replace('incoming=20','incoming=12.6').replace('delta=20','delta=12.6').replace('hp_lost=380 expected_damage=380','hp_lost=239.4 expected_damage=239.4')
        self.assertTrue(dz.diagnostic_checks(combined,'camp-mods')['passed'])
        self.assertFalse(dz.diagnostic_checks(combined.replace('12.6','12'),'camp-mods')['passed'])
    def test_vesper_reward_order_moves_the_carried_gold_unit(self):
        data=[('baseline_gold',0,0,0,240,319,319),('gem_7_floor',7,7,7,0,0,0),('gem_14_floor',14,14,14,0,0,0),('gold_cluster_bonus',0,0,0,20,26,26),('wolf_reward_unchanged',4,4,4,40,54,54)]
        def transcript(rows):
            return 'CT13_ACTOR vesper=1 bonus_gold_percent=33\nCT13_ITEM prospector=0\n'+'\n'.join('CT13_REWARD label=%s base_gems=%d actual_gems=%d expected_gems=%d base_gold=%d actual_gold=%d expected_gold=%d'%r for r in rows)+'\n'+'\n'.join(f'CT_CHECK name={n} pass=1' for n in [r[0] for r in rows]+['item_created','prospector_setup'])
        self.assertTrue(dz.diagnostic_checks(transcript(data),'prospector')['passed'])
        self.assertFalse(dz.diagnostic_checks(transcript(data).replace('actual_gold=54 expected_gold=54','actual_gold=53 expected_gold=53'),'prospector')['passed'])
        reverse=data[:3]+[('wolf_reward_unchanged',4,4,4,40,53,53),('gold_cluster_bonus',0,0,0,20,27,27)]
        self.assertTrue(dz.diagnostic_checks(transcript(reverse),'prospector')['passed'])
    def test_prospector_gold_and_gems_are_checked_independently_of_printed_pass_flags(self):
        data=[('baseline_gold',0,0,0,240,240,240),('gem_7_floor',7,8,8,0,0,0),('gem_14_floor',14,17,17,0,0,0),('gold_cluster_bonus',0,0,0,20,25,25),('wolf_reward_unchanged',4,4,4,40,40,40)]
        text='CT13_ACTOR vesper=0 bonus_gold_percent=0\nCT13_ITEM prospector=1\n'+'\n'.join('CT13_REWARD label=%s base_gems=%d actual_gems=%d expected_gems=%d base_gold=%d actual_gold=%d expected_gold=%d'%r for r in data)
        text+='\n'+'\n'.join(f'CT_CHECK name={n} pass=1' for n in [r[0] for r in data]+['item_created','prospector_setup'])
        self.assertTrue(dz.diagnostic_checks(text,'prospector')['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('actual_gold=25','actual_gold=20'),'prospector')['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('prospector=1','prospector=0'),'prospector')['passed'])
    def test_missed_pick_gate_accepts_completed_roster_without_inventing_later_draft_turns(self):
        text='CT20_SKIP turn=0 picks=3 before=0\n'+'\n'.join(f'CT20_PLAY body={i} type={i} picks=3 word=c000000000000000' for i in range(3))
        self.assertTrue(dz.diagnostic_checks(text,'draft-miss')['passed'])
        self.assertFalse(dz.diagnostic_checks(text+'\nCT20_AFTER_SKIP count=1','draft-miss')['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('type=2','type=1'),'draft-miss')['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('picks=3','picks=4'),'draft-miss')['passed'])
        second='CT20_PICK turn=0 before=0 after=0 choice=3\nCT20_SKIP turn=1 picks=3 before=1\n'+'\n'.join(f'CT20_PLAY body={i} type={t} picks=3 word=c001000100000003' for i,t in enumerate([3,4,1,2]))
        self.assertTrue(dz.diagnostic_checks(second,'draft-miss')['passed'])
        self.assertFalse(dz.diagnostic_checks(second.replace('after=0','after=1'),'draft-miss')['passed'])
    def test_linked_diagnostic_requires_both_directions_of_lifecycle(self):
        names=['linked_roster','linked_both_dead','linked_both_return','linked_partner_parked']
        text='\n'.join(f'CT_CHECK name={name} pass=1' for name in names)
        self.assertTrue(dz.diagnostic_checks(text,'linked')['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('name=linked_both_return','name=missing'),'linked')['passed'])
    def test_low_fuel_requires_real_movement_and_continuation(self):
        text='CT_LOW_FUEL_FORCE round=50 slot=0 target=5000\nDZ_LOW_FUEL round=50 slot=0 entry=4800 remaining=3000 moved=1 cleared=1 before=10 after=9\nDZ_COUNTS round=300 slot=0 actions=0 modules=0 stale=0'
        self.assertTrue(dz.diagnostic_checks(text,'low-fuel')['passed'])
        for a,b in [('moved=1','moved=0'),('entry=4800','entry=5001'),('after=9','after=10'),('stale=0','stale=1')]:
            self.assertFalse(dz.diagnostic_checks(text.replace(a,b),'low-fuel')['passed'])
    def test_clear_gate_requires_a_real_started_and_completed_experiment(self):
        text='\n'.join(f'CT_CHECK name={name} pass=1' for name in ('clear_outcome','clear_attack_count','clear_elapsed','clear_damage','clear_hit_damage','clear_isolated'))
        self.assertFalse(dz.diagnostic_checks(text,'clear')['passed'])
        valid=text+'\nCT_CLEAR_START ranged=0 round=10 members=1 hp=1000 camp_hp=1350 hit=70 incoming=20 predicted=20 survives=1\nCT_CLEAR_RESULT outcome=kill attacks=20 predicted=20 elapsed=19 moves=0'
        self.assertTrue(dz.diagnostic_checks(valid,'clear')['passed'])
        self.assertFalse(dz.diagnostic_checks(valid+'\nCT_CHECK name=clear_damage pass=0','clear')['passed'])
    def test_extracted_lifecycle_payload_is_not_a_second_match(self):
        self.assertEqual(dz.native_replay(['lifecycle.repl26a','candidate-vs-opponent.repl26a']), 'candidate-vs-opponent.repl26a')
        with self.assertRaises(ValueError): dz.native_replay(['lifecycle.repl26a'])
        with self.assertRaises(ValueError): dz.native_replay(['first.repl26a','second.repl26a','lifecycle.repl26a'])
    def test_kernel_diagnostic_cannot_pass_without_its_observations(self):
        self.assertFalse(dz.diagnostic_checks('','kernel')['passed'])
    def test_contest_gate_requires_capture_progress_before_enemy_entry(self):
        text='\n'.join(f'CT_CHECK name={name} pass=1' for name in ('contest_resets_capture_timer','contest_preserves_unclaimed_gems','full_reward_after_enemy_leaves','capture_progress_resumed'))
        self.assertFalse(dz.diagnostic_checks(text,'contest')['passed'])
        self.assertTrue(dz.diagnostic_checks(text,'contest','CT_CONTEST_PROGRESS round=21 timer=4 max=5 enemy_capturing=1')['passed'])
        self.assertFalse(dz.diagnostic_checks(text,'contest','CT_CONTEST_PROGRESS round=21 timer=5 max=5 enemy_capturing=1')['passed'])
    def test_visibility_gate_requires_hidden_private_reads_to_be_denied(self):
        names=['visible_alive','visible_gems','visible_items','visible_cooldown0','visible_cooldown1','hidden_alive']
        text='\n'.join(f'CT_QUERY name={name} accepted=1 value={int(name.endswith("alive"))} code=0' for name in names)
        text+='\n'+'\n'.join(f'CT_QUERY name={name} accepted=0 value=0 code=97' for name in ('hidden_gems','hidden_items','hidden_cooldown'))
        self.assertTrue(dz.diagnostic_checks(text,'visibility')['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('name=hidden_gems accepted=0 value=0 code=97','name=hidden_gems accepted=1 value=0 code=0'),'visibility')['passed'])
    def test_later_success_cannot_erase_an_earlier_failed_assertion(self):
        names=['split_primary_low_handle_remainder','split_partner_share','occupied_spawn_delays_respawn','vacated_spawn_respawns']
        valid='\n'.join(f'CT_CHECK name={name} pass=1' for name in names)
        self.assertTrue(dz.diagnostic_checks(valid,'capture')['passed'])
        self.assertFalse(dz.diagnostic_checks('CT_CHECK name=split_partner_share pass=0\n'+valid,'capture')['passed'])
    def test_targeting_requires_swaps_and_handle_sensitive_ties(self):
        def transcript(a,b,wrong_tie=False):
            lines=[f'CT11_HANDLES a={a} b={b}',f'CT11_SECOND_ATTACKER body={b} round=19']
            for phase,start,dist in ((2,1,(1,2)),(4,10,(2,1)),(6,20,(1,1))):
                a_hit=phase==2 or (phase==6 and (a<b)^wrong_tie)
                for r in range(start,start+5):
                    lines.append(f'CT11_TARGET phase={phase} round={r} da={60 if a_hit else 0} db={0 if a_hit else 60} ia=60 ib=60 dista={dist[0]} distb={dist[1]}')
            return '\n'.join(lines)
        self.assertTrue(dz.diagnostic_checks(transcript(0,1),'targeting')['passed'])
        self.assertTrue(dz.diagnostic_checks(transcript(1,0),'targeting')['passed'])
        self.assertFalse(dz.diagnostic_checks(transcript(0,1,True),'targeting')['passed'])
        self.assertFalse(dz.diagnostic_checks(transcript(0,1).replace('CT11_SECOND_ATTACKER','absent'),'targeting')['passed'])
    def test_module_quarantine_and_stale_diagnostics_are_distinct(self):
        errors='\n'.join(f'DZ_MODULE_ERROR round={n} body=0 module=memory failures={n} disabled={int(n==3)}' for n in (1,2,3))
        text=errors+'\nDZ_COUNTS round=100 slot=0 actions=0 modules=3 stale=0'
        self.assertTrue(dz.diagnostic_checks(text,'module-failure')['passed'])
        self.assertFalse(dz.diagnostic_checks(text+'\nDZ_MODULE_ERROR unclassified','module-failure')['passed'])
        self.assertTrue(dz.diagnostic_checks('DZ_COUNTS round=100 slot=0 actions=0 modules=0 stale=1','module-stale')['passed'])
        self.assertFalse(dz.diagnostic_checks('DZ_COUNTS round=100 slot=0 actions=0 modules=1 stale=0','module-stale')['passed'])
    def test_fingerprint_rejects_missing_changed_and_duplicate_fields(self):
        reference=json.loads((dz.ROOT/'research/dz/ENGINE_FINGERPRINT.json').read_text())
        lines=[f'CT27_FIELD {key} '+value.replace(':',' ') for key,value in reference['fields'].items()]
        complete='\nCT27_COMPLETE schema=1\n'
        self.assertTrue(dz.diagnostic_checks('\n'.join(lines)+complete,'fingerprint')['passed'])
        self.assertFalse(dz.diagnostic_checks('\n'.join(lines[1:])+complete,'fingerprint')['passed'])
        changed=lines.copy(); changed[0]=changed[0][:-1]+('0' if changed[0][-1]!='0' else '1')
        self.assertFalse(dz.diagnostic_checks('\n'.join(changed)+complete,'fingerprint')['passed'])
        self.assertFalse(dz.diagnostic_checks('\n'.join(lines+[lines[0]])+complete,'fingerprint')['passed'])
    def test_rle_boundaries_and_no_extrapolation(self):
        runs = [{'duration':2,'value':'0'},{'duration':3,'value':'7'}]
        self.assertEqual([dz.sample_at(runs,n) for n in range(6)], [0,0,7,7,7,None])
        with self.assertRaises(ValueError): dz.sample_at([{'duration':0,'value':1}],0)
    def test_noop_probe_must_fail(self):
        text='\n'.join(f'CT11 round={r} hp=1000 delta=0 active=0 incoming=0 target_awake=0 target_strength=0 target_in_range=0' for r in range(20))
        self.assertFalse(dz.diagnostic_checks(text,'camps')['passed'])
    def test_team_owner_is_a_string_and_early_end_is_explicit(self):
        summary=dict(match=dict(roundsStarted=120),
            championTimelines=[dict(metric='collectedGems',owner=dict(team='teamA'),runs=[dict(duration=121,value='7')]),
                               dict(metric='collectedGems',owner=dict(team='teamB'),runs=[dict(duration=121,value='99')])],
            teamTimelines=[dict(metric='submittedGems',owner='teamA',runs=[dict(duration=121,value='5')])])
        got=dz.checkpoints(summary,'A')
        self.assertEqual(got['100']['collected'],7)
        self.assertEqual(got['100']['banked'],5)
        self.assertIsNone(got['100']['gold'])
        self.assertEqual(got['250']['round'],120)
        self.assertTrue(got['250']['ended_before_checkpoint'])
    def test_repeated_per_round_damage_establishes_cadence(self):
        text='\n'.join(f'CT11 round={r} hp={1000-60*r} delta=60 active=3 incoming=60 target_awake=1 target_strength=60 target_in_range=1' for r in range(1,9))
        self.assertTrue(dz.diagnostic_checks(text,'camps')['passed'])
        self.assertFalse(dz.diagnostic_checks(text.replace('target_in_range=1','target_in_range=0'),'camps')['passed'])
    def test_half_rate_does_not_pass_full_rate_assertion(self):
        text='\n'.join(f'CT11 round={r} hp=500 delta={60 if r%2 else 0} active=1 incoming=60 target_awake=1 target_strength=60 target_in_range=1' for r in range(1,15))
        self.assertFalse(dz.diagnostic_checks(text,'camps')['passed'])

if __name__=='__main__': unittest.main()
