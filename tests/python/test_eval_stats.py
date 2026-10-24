"""Known-answer tests for nfs.evaluate.stats (synthetic data only; labelled synthetic)."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'python'))
from nfs.evaluate import stats  # noqa: E402


def rows(opp, per_map, sides=('A', 'B'), gems=(100, 50)):
    """per_map: map -> tuple of wins per side (synthetic)."""
    out = []
    for m, wins in per_map.items():
        for s, w in zip(sides, wins):
            out.append(dict(opponent=opp, map=m, side=s, win=w, gems=gems[0] if w == 1 else gems[1],
                            opponent_gems=gems[1] if w == 1 else gems[0], faults=0, fuel_exhausted=0))
    return out


class TestWilson(unittest.TestCase):
    def test_zero_of_ten(self):
        lo, hi = stats.wilson(0, 10)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.2775, places=4)  # z^2/(n+z^2) = 3.8415/13.8415

    def test_half(self):
        lo, hi = stats.wilson(6, 12)
        self.assertAlmostEqual(lo + hi, 1.0, places=12)  # symmetric about 0.5
        self.assertAlmostEqual(lo, 0.2538, places=4)

    def test_empty(self):
        self.assertTrue(all(math.isnan(x) for x in stats.wilson(0, 0)))


class TestBootstrap(unittest.TestCase):
    def test_constant_clusters_give_degenerate_interval(self):
        per = {'o': {f'm{i}': 0.25 for i in range(10)}}
        iv = stats.joint_map_bootstrap(per, n_boot=2000)['o']
        self.assertEqual((iv.point, iv.lo95, iv.hi95, iv.lb_one_sided), (0.25, 0.25, 0.25, 0.25))

    def test_exact_distribution_two_clusters(self):
        dist = stats.exact_bootstrap_distribution([0.0, 1.0])
        self.assertAlmostEqual(dist[0.0], 0.25)
        self.assertAlmostEqual(dist[0.5], 0.5)
        self.assertAlmostEqual(dist[1.0], 0.25)
        iv = stats.joint_map_bootstrap({'o': {'a': 0.0, 'b': 1.0}}, n_boot=40000, seed=1)['o']
        self.assertEqual((iv.lo95, iv.hi95), (0.0, 1.0))
        self.assertEqual(iv.lb_one_sided, 0.0)  # P(mean=0)=0.25 >= 0.05

    def test_monte_carlo_matches_exact_quantiles(self):
        vals = [0.0, 0.0, 0.5, 1.0, -0.5]
        dist = stats.exact_bootstrap_distribution(vals)
        self.assertAlmostEqual(sum(dist.values()), 1.0, places=12)
        self.assertAlmostEqual(dist[min(dist)], (1 / 5) ** 5)  # every draw is the -0.5 cluster
        iv = stats.joint_map_bootstrap({'o': {f'm{i}': v for i, v in enumerate(vals)}}, n_boot=60000, seed=7)['o']
        for q, got in ((0.05, iv.lb_one_sided), (0.025, iv.lo95), (0.975, iv.hi95)):
            exact = stats.exact_quantile(dist, q)
            self.assertLessEqual(abs(got - exact), 0.1 + 1e-9, (q, got, exact))  # one grid step (0.1)

    def test_bootstrap_se_known(self):
        # 12 clusters alternating 0/1: mean 0.5, plug-in SE = sqrt(0.25/12) = 0.1443
        per = {'o': {f'm{i:02d}': float(i % 2) for i in range(12)}}
        import numpy as np
        rng = np.random.default_rng(3)
        mat = np.array(list(per['o'].values()))
        boots = mat[rng.integers(0, 12, (40000, 12))].mean(1)
        self.assertAlmostEqual(float(boots.std()), math.sqrt(0.25 / 12), places=2)
        iv = stats.joint_map_bootstrap(per, n_boot=40000)['o']
        self.assertAlmostEqual(iv.point, 0.5)
        self.assertAlmostEqual(iv.lo95, 0.5 - 1.96 * 0.1443, delta=0.06)

    def test_joint_resampling_preserves_cross_opponent_dependence(self):
        # two opponents perfectly anti-correlated per map: pooled mean is constant 0 in every replicate
        per = {'x': {f'm{i}': float(i % 2) for i in range(8)}, 'y': {f'm{i}': -float(i % 2) for i in range(8)}}
        iv = stats.joint_map_bootstrap(per, n_boot=5000)
        self.assertEqual((iv['__pooled__'].lo95, iv['__pooled__'].hi95), (0.0, 0.0))
        self.assertLess(iv['x'].lo95, iv['x'].hi95)

    def test_series_must_share_maps(self):
        with self.assertRaises(ValueError):
            stats.joint_map_bootstrap({'x': {'a': 1.0}, 'y': {'b': 1.0}})


class TestPaired(unittest.TestCase):
    def test_paired_differences_and_cluster_means(self):
        cand = rows('original', {'m1': (1, 1), 'm2': (1, 0)})
        base = rows('original', {'m1': (1, 0), 'm2': (1, 0)})
        d = stats.paired_differences(cand, base)
        per = stats.per_map_means(d, 'd_win')
        self.assertEqual(per, {'original': {'m1': 0.5, 'm2': 0.0}})
        tab = stats.paired_table(cand, base, n_boot=2000)
        self.assertAlmostEqual(tab['win']['original']['point'], 0.25)
        self.assertEqual(tab['win']['original']['n_map_clusters'], 2)

    def test_mismatched_cells_raise(self):
        with self.assertRaises(ValueError):
            stats.paired_differences(rows('o', {'m1': (1, 1)}), rows('o', {'m2': (1, 1)}))

    def test_opponent_table(self):
        t = stats.opponent_table(rows('v47', {'m1': (1, 0), 'm2': (0.5, 0)}))
        self.assertEqual(t['v47']['games'], 4)
        self.assertEqual(t['v47']['wins'], 1.5)
        self.assertEqual(t['v47']['by_side']['A']['wins'], 1.5)


if __name__ == '__main__':
    unittest.main()
