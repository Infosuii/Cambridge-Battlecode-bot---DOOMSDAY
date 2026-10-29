"""Regression checks for interpretation of native evidence, independent of a bot."""
import importlib.util
import json
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location('dz_runner', Path(__file__).resolve().parents[2]/'tools/dz.py')
dz = importlib.util.module_from_spec(spec); spec.loader.exec_module(dz)

class Measurements(unittest.TestCase):
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
        text='\n'.join(f'CT11 round={r} hp=1000 delta=0 active=0 incoming=0' for r in range(20))
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
        text='\n'.join(f'CT11 round={r} hp={1000-60*r} delta=60 active=3 incoming=60' for r in range(1,9))
        self.assertTrue(dz.diagnostic_checks(text,'camps')['passed'])
    def test_half_rate_does_not_pass_full_rate_assertion(self):
        text='\n'.join(f'CT11 round={r} hp=500 delta={60 if r%2 else 0} active=1 incoming=60' for r in range(1,15))
        self.assertFalse(dz.diagnostic_checks(text,'camps')['passed'])

if __name__=='__main__': unittest.main()
