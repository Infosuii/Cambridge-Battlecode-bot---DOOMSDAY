"""Regression checks for interpretation of native evidence, independent of a bot."""
import importlib.util
import json
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location('dz_runner', Path(__file__).resolve().parents[2]/'tools/dz.py')
dz = importlib.util.module_from_spec(spec); spec.loader.exec_module(dz)

class Measurements(unittest.TestCase):
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
