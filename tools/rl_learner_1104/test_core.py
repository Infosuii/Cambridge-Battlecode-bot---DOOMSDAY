import unittest
from rl_learner_1104.returns import gae


class ReturnsTests(unittest.TestCase):
    def test_terminal_no_bootstrap(self):
        a, r = gae([1.0], [0.2], [999], [3], [True], [False])
        self.assertAlmostEqual(a[0], 0.8)
        self.assertAlmostEqual(r[0], 1.0)

    def test_truncation_bootstraps_but_stops_recurrence(self):
        a, _ = gae([1, 100], [0, 0], [2, 0], [2, 1],
                   [False, True], [True, False], gamma=0.5, lam=1)
        self.assertEqual(a, [1.5, 100])

    def test_round_duration(self):
        a, _ = gae([0, 4], [0, 0], [0, 0], [2, 1],
                   [False, True], [False, False], gamma=0.5, lam=1)
        self.assertEqual(a, [1, 4])

    def test_respawn_keeps_team_return(self):
        a, _ = gae([0, 1], [0, 0], [0, 0], [1, 1],
                   [False, True], [False, False], gamma=1, lam=1)
        self.assertEqual(a, [1, 1])

    def test_invalid_duration(self):
        with self.assertRaises(ValueError):
            gae([0], [0], [0], [0], [False], [False])


if __name__ == '__main__':
    unittest.main()
