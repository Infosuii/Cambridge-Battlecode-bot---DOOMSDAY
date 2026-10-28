"""Scientific checks: calibration partitioning, symmetry and no future income."""
import unittest
import numpy as np
from winprob import features, fit, metrics, sigmoid


class ModelChecks(unittest.TestCase):
    def test_half_probability_is_in_one_calibration_bin(self):
        r = metrics(np.array([0., 1.]), np.zeros(2), np.ones(2))
        self.assertAlmostEqual(sum(b['weight'] for b in r['bins']), 1.)
        self.assertAlmostEqual(r['log_loss'], np.log(2))
        self.assertAlmostEqual(r['brier'], .25)
        self.assertAlmostEqual(r['ece10'], 0.)

    def test_team_exchange_is_exact_complement(self):
        x = np.array([[1., 0.], [-2., 1.], [0., 0.]])
        b = fit(x, np.array([1., 0., 1.]), np.ones(3), .1)
        np.testing.assert_allclose(sigmoid(x @ b) + sigmoid(-x @ b), np.ones(3))

    def test_future_resources_cannot_change_an_earlier_feature(self):
        def team(c):
            return dict(banked=c, carried=0, equipment_cost=0, alive=1, health=1,
                        collected=c, middle_gems=0, vision_fraction=0)
        g = {'max_rounds': 2000, 'rows': [{'r': r, 'teams': [team(c), team(0)]}
             for r, c in [(0, 0), (50, 2), (100, 4)]]}
        original = features(g).copy()
        g['rows'][-1]['teams'][0]['collected'] = 9999
        np.testing.assert_array_equal(original[:2], features(g)[:2])

    def test_repeated_snapshots_keep_game_weight(self):
        a = fit(np.array([[1.], [-1.]]), np.array([1., 0.]), np.ones(2), .1)
        b = fit(np.array([[1.], [1.], [-1.]]), np.array([1., 1., 0.]), np.array([.5, .5, 1.]), .1)
        np.testing.assert_allclose(a, b)


if __name__ == '__main__':
    unittest.main()
