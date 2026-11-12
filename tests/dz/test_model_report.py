import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('model_report',Path(__file__).resolve().parents[2]/'tools/dz_model_report.py')
report=importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


def episode():
    return dict(quote=dict(contact=1,status=0,state=1,attacks=4,members=2,seen=10,round=10,
                           loss=20,new=1,field=1,dist=1,range=1,clock=3,clock_status=0),
                outcome='cleared',own_basic_attacks=4,other_damage_events=0,unknown_damage_events=0,
                own_nonbasic_damage_events=0,memory_hp_difference=0,other_hp_loss=0,target_camp_hp_loss=20,
                arrival_round=10,clear_round=13,champion_type=2,reset_actions=['10:4'])


class ModelReportTests(unittest.TestCase):
    def test_missing_observations_cannot_pass(self):
        r=report.errors([],unit='HP')
        self.assertEqual(r['n'],0)
        self.assertIsNone(r['aggregate_signed_bias'])
        self.assertIsNone(r['median_absolute_relative_error'])
        self.assertEqual(r['unit'],'HP')

    def test_censored_and_assisted_stay_out_of_solo_metrics(self):
        good=episode();dead=copy.deepcopy(good);dead['outcome']='death'
        helped=copy.deepcopy(good);helped['other_damage_events']=1
        r=report.summarize([good,dead,helped])
        self.assertEqual(r['outcomes']['death'],1)
        self.assertEqual(r['contact_predictions'],3)
        self.assertEqual(r['all_contact_clear']['n'],2)
        self.assertEqual(r['solo_basic_clear']['n'],1)
        self.assertEqual(r['solo_basic_clear']['median_absolute_relative_error'],.125)
        self.assertEqual(r['solo_target_damage']['unit'],'HP')

    def test_unissued_clock_is_not_a_zero_error_prediction(self):
        old=episode();del old['quote']['clock'];del old['quote']['clock_status']
        r=report.summarize([old])
        self.assertEqual(r['solo_clock_clear']['n'],0)
        self.assertIsNone(r['solo_clock_clear']['aggregate_signed_bias'])

    def test_splash_kit_cannot_validate_constant_basic_clock(self):
        r=episode();r['champion_type']=10
        s=report.summarize([r])
        self.assertEqual(s['solo_clock_clear']['n'],1)
        self.assertEqual(s['constant_kit_clock_clear']['n'],0)

    def test_arrival_accounts_for_this_turns_movement(self):
        r=episode();r['quote'].update(contact=0,dist=2)
        s=report.summarize([r])
        self.assertEqual(s['cached_field_arrival']['median_absolute_error'],0)

    def test_unshared_damage_requires_observed_spatial_context(self):
        old=episode();isolated=episode()
        isolated.update(bystander_context_known=True,potential_tank_bystanders=[],target_camp_other_hp_loss=0)
        bystander=copy.deepcopy(isolated);bystander['potential_tank_bystanders']=[7]
        tank=copy.deepcopy(isolated);tank['target_camp_other_hp_loss']=10
        s=report.summarize([old,isolated,bystander,tank])
        self.assertEqual(s['solo_target_damage']['n'],4)
        self.assertEqual(s['damage_context_known'],3)
        self.assertEqual(s['damage_potential_bystanders'],1)
        self.assertEqual(s['damage_observed_other_tanking'],1)
        self.assertEqual(s['solo_unshared_target_damage']['n'],1)

    def test_mixed_splash_requires_full_identity_and_stationary_unshared_context(self):
        good=episode();good.update(champion_type=10,healing=0,bystander_context_known=True,
            potential_tank_bystanders=[],target_camp_other_hp_loss=0,member_hp_hash_matches=True,
            native_static_positions=True,own_movement_events=0,camp_movement_events=0,
            native_damaging_live_members=1,shield_target_matches=True,shield_actions=['11:9'])
        good['quote'].update(shield_mode=1,shield_status=0,shield_live=2,shield_rounds=4,
                             shield_loss=20,shield_casts=1,enemies=0)
        invalid=[]
        for key,value in [('member_hp_hash_matches',False),('native_static_positions',False),
                          ('own_movement_events',1),('camp_movement_events',1),
                          ('native_damaging_live_members',2),('shield_target_matches',False)]:
            r=copy.deepcopy(good);r[key]=value;invalid.append(r)
        s=report.summarize([good,*invalid])
        self.assertEqual(s['varg_mixed_splash_time']['n'],1)
        self.assertEqual(s['varg_mixed_splash_shield_damage']['aggregate_signed_bias'],0)
        self.assertEqual(s['mixed_shield_casts'],dict(predicted=1,observed=1))
        self.assertEqual(s['varg_single_live_shield_time']['n'],0)
        del good['member_hp_hash_matches']
        self.assertIsNone(report.summarize([good])['varg_mixed_splash_time']['aggregate_signed_bias'])

    def test_heart_requires_issued_passive_forecast_and_stationary_identity(self):
        good=episode();good.update(champion_type=12,healing=0,bystander_context_known=True,
            potential_tank_bystanders=[],target_camp_other_hp_loss=0,member_hp_hash_matches=True,
            native_static_positions=True,own_movement_events=0,camp_movement_events=0,
            native_damaging_live_members=1,native_initial_live_members=1,shield_target_matches=True,
            shield_member_matches=True,shield_actions=['11:9'])
        good['quote'].update(shield_mode=2,missing_health_bonus=.5,shield_status=0,shield_live=1,
                             shield_rounds=4,shield_loss=20,shield_casts=1)
        missing=copy.deepcopy(good);del missing['quote']['missing_health_bonus']
        moved=copy.deepcopy(good);moved['own_movement_events']=1
        wrong=copy.deepcopy(good);wrong['member_hp_hash_matches']=False
        s=report.summarize([good,missing,moved,wrong])
        self.assertEqual(s['heart_single_live_shield_time']['n'],1)
        self.assertEqual(s['heart_single_live_shield_damage']['aggregate_signed_bias'],0)
        self.assertEqual(s['heart_shield_casts'],dict(predicted=1,observed=1))
        self.assertEqual(s['varg_single_live_shield_time']['n'],0)

    def test_shield_model_requires_same_single_live_member_and_no_healing(self):
        good=episode();good.update(champion_type=10,healing=0,bystander_context_known=True,
                                  potential_tank_bystanders=[],target_camp_other_hp_loss=0,
                                  native_initial_live_members=1,shield_member_matches=True,shield_actions=['11:9'])
        good['quote'].update(shield_status=0,shield_live=1,shield_rounds=4,shield_loss=20,shield_casts=1)
        wrong=copy.deepcopy(good);wrong['shield_member_matches']=False
        healed=copy.deepcopy(good);healed['healing']=1
        unfinished=copy.deepcopy(good);unfinished['quote']['shield_status']=2
        r=report.summarize([good,wrong,healed,unfinished])
        self.assertEqual(r['varg_single_live_shield_damage']['n'],1)
        self.assertEqual(r['varg_single_live_shield_damage']['aggregate_signed_bias'],0)
        self.assertEqual(r['shield_casts'],dict(predicted=1,observed=1))
        good['quote']['shield_sample']=1
        late=report.summarize([good])
        self.assertEqual(late['contact_predictions'],0)
        self.assertEqual(late['solo_basic_clear']['n'],0)
        self.assertEqual(late['varg_single_live_shield_damage']['n'],1)
        self.assertEqual(late['late_shield_contact_predictions'],1)


if __name__=='__main__':unittest.main()
