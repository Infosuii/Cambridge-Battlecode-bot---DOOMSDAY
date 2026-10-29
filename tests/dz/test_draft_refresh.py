import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('draft_refresh', Path(__file__).resolve().parents[2]/'tools/dz_draft_refresh.py')
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.baseline = {'development': 100, 'heldout': -9999}
        self.candidates = {v: {'development': 100} for v in range(8)}

    def select(self, incumbent=None, margin=100):
        return refresh.choose(self.baseline, self.candidates, incumbent or {}, {'development'}, margin)

    def test_global_prior_can_replace_an_incumbent_variant(self):
        self.candidates[0]['development'] = 250
        report = self.select({'development': 3})
        self.assertEqual(report['table'], {'development': 0})
        self.assertEqual(report['in_sample_gain_per_game'], 75)

    def test_noop_layout_gain_is_not_a_policy_change(self):
        self.candidates[3]['development'] = 500
        self.candidates[7]['development'] = 220
        report = self.select({'development': 3})
        self.assertEqual(report['table'], {'development': 7})
        self.assertIn('development', report['same_lineup_differences'])

    def test_ties_and_small_improvements_keep_incumbent(self):
        self.assertEqual(self.select(margin=0)['table'], {})
        self.candidates[7]['development'] = 199
        self.assertEqual(self.select()['table'], {})

    def test_missing_or_heldout_candidate_cells_rejected(self):
        self.candidates[7]['heldout'] = 100000
        with self.assertRaises(ValueError):
            self.select()
        del self.candidates[7]['heldout']
        del self.candidates[7]['development']
        with self.assertRaises(ValueError):
            self.select()

    def test_invalid_margin_and_incomplete_lineups_rejected(self):
        for margin in (-1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                self.select(margin=margin)
        del self.candidates[4]
        with self.assertRaises(ValueError):
            self.select()
