import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('loss_audit',Path(__file__).resolve().parents[2]/'tools/dz_loss_audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


class LossAuditTests(unittest.TestCase):
    def test_native_loss_units_enemy_identity_and_cutoff(self):
        native=dict(events=[dict(kind='gemLoss',owner={'team':'teamA'},entries=[
            dict(value='35',target={'team':'teamB'},timestamp={'round':500}),
            dict(value='7',target={'kind':'camp'},timestamp={'round':501}),
            dict(value='4',target=None,timestamp={'round':20})]),
            dict(kind='gemCollection',owner={'team':'teamA'},entries=[dict(value='100')]),
            dict(kind='gemLoss',owner={'team':'teamB'},entries=[dict(value='99',timestamp={'round':1})])])
        self.assertEqual(audit.losses(native,'A'),dict(total=46,to_enemy=35,through_cutoff=39,
                                                   to_enemy_through_cutoff=35,events_30plus=1))

    def test_empty_loss_events_are_zero_but_negative_units_fail(self):
        self.assertEqual(audit.losses({'events':[]},'A')['total'],0)
        with self.assertRaises(ValueError):
            audit.losses(dict(events=[dict(kind='gemLoss',owner={'team':'teamA'},entries=[
                dict(value='-1',target=None,timestamp={'round':1})])]),'A')


if __name__=='__main__':unittest.main()
