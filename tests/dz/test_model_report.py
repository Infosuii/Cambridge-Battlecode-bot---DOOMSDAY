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


if __name__=='__main__':unittest.main()
