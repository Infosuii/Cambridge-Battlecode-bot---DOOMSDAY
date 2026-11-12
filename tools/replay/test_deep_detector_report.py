"""Small statistical edge cases for the detector report, independent of live data."""
import unittest
from deep_detector_report import aggregate, cluster_interval, wilson


class ReportCases(unittest.TestCase):
    def test_missing_denominator_is_unknown(self):
        self.assertIsNone(wilson(0, 0))

    def test_single_game_is_not_certainty(self):
        self.assertGreater(wilson(0, 1)[1], .7)
        self.assertLess(wilson(1, 1)[0], .3)

    def test_one_cluster_has_no_bootstrap_interval(self):
        rows = [{'won': False, 'map': 'one', 'actors': []}, {'won': True, 'map': 'one', 'actors': []}]
        result = cluster_interval(rows, 'D7', 'map', 123)
        self.assertIsNone(result['interval95'])
        self.assertEqual(result['clusters_with_both_outcomes'], 1)

    def test_multiple_champions_are_one_game_occurrence(self):
        actor = {'denominators': {'complete_turns': 10}, 'detectors': {'D7': {'events': [{'turns': 0}]}}}
        result = aggregate([{'actors': [actor, actor]}], 'D7')
        self.assertEqual(result['n'], 1)
        self.assertEqual(result['flagged'], 1)
        self.assertEqual(result['events'], 2)

    def test_overlapping_subtypes_have_union_exposure(self):
        actor = {'denominators': {'alive_complete_turns': 20}, 'detectors': {'D6': {'events': [
            {'subtype': 'empty', 'start': 1, 'end': 10, 'turns': 10},
            {'subtype': 'blocked', 'start': 6, 'end': 15, 'turns': 10}]}}}
        result = aggregate([{'actors': [actor]}], 'D6')
        self.assertEqual(result['flagged_champion_turns'], 15)
        self.assertEqual(result['eligible_champion_turns'], 20)

    def test_event_rates_pool_exposure_and_exclude_censored_attempts(self):
        first = {'denominators': {'bank_attempts': 4}, 'descriptors': {'bank_attempts_censored': 2},
                 'detectors': {'D8': {'events': [{'turns': 0}]}}}
        second = {'denominators': {'bank_attempts': 100}, 'descriptors': {'bank_attempts_censored': 0},
                  'detectors': {'D8': {'events': [{'turns': 0}] * 9}}}
        result = aggregate([{'actors': [first, second]}], 'D8')
        self.assertEqual(result['event_numerator'], 10)
        self.assertEqual(result['event_denominator'], 102)
        self.assertAlmostEqual(result['event_rate'], 10/102)


if __name__ == '__main__':
    unittest.main()
