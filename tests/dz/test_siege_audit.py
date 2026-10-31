import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('siege_audit',Path(__file__).resolve().parents[2]/'tools/dz_siege_audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

def event(round_number,name):
    return f'DZ_SIEGE round={round_number} body=1 event={name} group=0 member=0 phase=3 hp=500 target_hp=2000\n'

class AuditFailures(unittest.TestCase):
    def setUp(self):
        self.summary={'events':[{'kind':'death','owner':{'id':1},'entries':[{'timestamp':{'round':12}}]}]}
    def test_death_without_return_is_not_lost(self):
        issues,intervals=audit.withdrawal_deaths(self.summary,event(10,'escape')+event(11,'recover'),40)
        self.assertEqual(issues[0]['rounds'],[12]);self.assertTrue(intervals[0]['censored'])
    def test_later_select_does_not_erase_death(self):
        issues,_=audit.withdrawal_deaths(self.summary,event(10,'escape')+event(30,'select'),40)
        self.assertEqual(issues[0]['rounds'],[12])
    def test_finished_withdrawal_does_not_claim_later_farming_death(self):
        issues,intervals=audit.withdrawal_deaths(self.summary,event(10,'open')+event(11,'done'),40)
        self.assertEqual(issues,[]);self.assertEqual(intervals[0]['stop'],11)
    def test_return_closes_only_that_bodys_interval(self):
        text=event(10,'escape')+event(11,'return').replace('body=1','body=2')
        issues,_=audit.withdrawal_deaths(self.summary,text,40)
        self.assertEqual(issues[0]['rounds'],[12])

if __name__=='__main__':unittest.main()
