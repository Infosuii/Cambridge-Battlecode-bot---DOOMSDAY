"""Reward fixtures: banking vs losing a bag, potential-shaping telescoping, scale sanity, ablations."""
import json
import unittest
from pathlib import Path

import numpy as np

import _fakes as F  # noqa: F401
from nfs.train import rewards as R


def series(T, carried, submitted, deaths=None, outcome='tie', team=0.0, opp=0.0, gold=None, damage=None, obj=None):
    z = np.zeros(T + 1)
    return R.AgentSeries(submitted=np.asarray(submitted, float), carried=np.asarray(carried, float),
                         gold=z if gold is None else np.asarray(gold, float),
                         deaths=z if deaths is None else np.asarray(deaths, float),
                         damage=z if damage is None else np.asarray(damage, float),
                         objective=z if obj is None else np.asarray(obj, float),
                         outcome=outcome, final_team_gems=team, final_opponent_gems=opp)


def step(T, at, value, before=0.0):
    a = np.full(T + 1, before, float)
    a[at:] = value
    return a


class RewardTests(unittest.TestCase):
    T = 100

    def bank_and_win(self, cfg):
        carried = step(self.T, 20, 100); carried[40:] = 0           # collect 100 at r20, bank at r40
        return series(self.T, carried, step(self.T, 40, 100), outcome='win', team=100, opp=50)

    def collect_then_die(self, cfg):
        carried = step(self.T, 20, 100); carried[40:] = 0           # collect 100 at r20, die with bag at r40
        return series(self.T, carried, np.zeros(self.T + 1), deaths=step(self.T, 40, 1), outcome='loss', team=0, opp=50)

    def never_collect(self, cfg):
        return series(self.T, np.zeros(self.T + 1), np.zeros(self.T + 1), outcome='loss', team=0, opp=50)

    def test_bank_and_win_beats_collect_then_die(self):
        for cfg in (R.RewardConfig(), R.RewardConfig(ablate=('terminal',)), R.RewardConfig(carry_potential=5e-4),
                    R.RewardConfig(gamma=1.0)):
            good = R.episode_breakdown(self.bank_and_win(cfg), cfg)['total']
            bad = R.episode_breakdown(self.collect_then_die(cfg), cfg)['total']
            none = R.episode_breakdown(self.never_collect(cfg), cfg)['total']
            self.assertGreater(good, bad, cfg)
            self.assertLessEqual(bad, none + 1e-12, cfg)               # losing the bag is not better than not collecting

    def test_collecting_and_losing_bag_nets_zero_shaping(self):
        cfg = R.RewardConfig()
        b = R.episode_breakdown(self.collect_then_die(cfg), cfg)['components']
        self.assertAlmostEqual(b['carry_shaping'], 0.0, places=12)
        self.assertLess(b['death'], 0)
        # prefix return up to just after pickup is positive, but the full option return is not
        comps = R.per_round_components(self.collect_then_die(cfg), cfg)
        self.assertGreater(R.discounted_return(comps['carry_shaping'][:25], cfg.gamma), 0)
        self.assertAlmostEqual(R.discounted_return(comps['carry_shaping'], cfg.gamma), 0.0, places=12)

    def test_carry_until_end_earns_nothing(self):
        cfg = R.RewardConfig()
        s = series(self.T, step(self.T, 10, 200), np.zeros(self.T + 1))
        self.assertAlmostEqual(R.episode_breakdown(s, cfg)['components']['carry_shaping'], 0.0, places=12)

    def test_potential_shaping_telescopes_random(self):
        rng = np.random.default_rng(0)
        for gamma in (1.0, 0.999, 0.95):
            cfg = R.RewardConfig(gamma=gamma, carry_potential=4e-4)
            for _ in range(20):
                carried = rng.integers(0, 300, self.T + 1).astype(float)
                s = series(self.T, carried, np.zeros(self.T + 1))
                comps = R.per_round_components(s, cfg)
                total = R.discounted_return(comps['carry_shaping'], gamma)
                self.assertAlmostEqual(total, -cfg.carry_potential * carried[0], places=10)
                # SMDP intervals with variable gaps telescope too: sum_i gamma^{b_i} R_i == full discounted sum
                b = sorted(set([0] + rng.choice(np.arange(1, self.T), 7, replace=False).tolist()))
                ints = R.interval_rewards(comps, b, gamma)
                acc = sum(gamma ** x['start'] * x['components']['carry_shaping'] for x in ints)
                self.assertAlmostEqual(acc, total, places=10)
                self.assertEqual(sum(x['tau'] for x in ints), self.T)

    def test_interval_empty_gap(self):
        cfg = R.RewardConfig()
        comps = R.per_round_components(self.bank_and_win(cfg), cfg)
        ints = R.interval_rewards(comps, [0, 10, 10, 50], cfg.gamma)
        self.assertEqual(ints[1]['tau'], 0)
        self.assertEqual(ints[1]['reward'], 0.0)
        self.assertTrue(ints[-1]['terminal'])

    def test_terminal_and_tie(self):
        cfg = R.RewardConfig()
        self.assertAlmostEqual(R.terminal_reward('win', 500, 400, cfg), 1 + 0.5 * 0.1)
        self.assertAlmostEqual(R.terminal_reward('loss', 400, 500, cfg), -1 - 0.5 * 0.1)
        self.assertAlmostEqual(R.terminal_reward('tie', 300, 300, cfg), 0.0)
        self.assertAlmostEqual(R.terminal_reward('win', 5000, 0, cfg), 1.5)        # margin clipped
        self.assertEqual(R.terminal_reward('win', 1, 0, R.RewardConfig(ablate=('terminal',))), 0.0)

    def test_ablation_zeroes_component(self):
        s = series(self.T, step(self.T, 20, 50), step(self.T, 60, 50), deaths=step(self.T, 70, 1),
                   gold=np.arange(self.T + 1) * 10.0, damage=np.arange(self.T + 1) * 5.0, obj=step(self.T, 30, 2))
        for comp in R.COMPONENTS:
            b = R.episode_breakdown(s, R.RewardConfig(ablate=(comp,)))['components']
            self.assertEqual(b[comp], 0.0, comp)

    def test_config_validation(self):
        with self.assertRaises(ValueError):
            R.RewardConfig(carry_potential=1e-3, w_submitted=5e-4).validate()
        with self.assertRaises(ValueError):
            R.RewardConfig(ablate=('nonsense',)).validate()
        with self.assertRaises(ValueError):
            R.RewardConfig(gamma=1.5).validate()
        c = R.RewardConfig.from_dict(dict(R.RewardConfig().to_dict(), _note='x'))
        self.assertEqual(c, R.RewardConfig())

    def test_scale_sanity_synthetic_full_game(self):
        T = 2000
        cfg = R.RewardConfig(gamma=1.0)
        carried, submitted = np.zeros(T + 1), np.zeros(T + 1)
        for k in range(10):                                      # 10 trips of 50 gems, each banked
            carried[100 + 180 * k:160 + 180 * k] = 50
            submitted[160 + 180 * k:] += 50
        s = series(T, carried, submitted, deaths=step(T, 1500, 4), outcome='win', team=1000, opp=900,
                   gold=np.linspace(0, 3000, T + 1), damage=np.linspace(0, 5000, T + 1), obj=np.linspace(0, 20, T + 1))
        rep = R.scale_report(s, cfg)
        self.assertTrue(rep['ok'], rep)
        self.assertLess(rep['dense_to_win'], 1.0)
        self.assertGreater(rep['components']['deposit'], 0.1)    # banking is not negligible either

    def test_scale_on_real_engine_summary_fixture(self):
        """Read-only fixture: an existing official 1.0.3 match summary from the previous diagnosis (no new games)."""
        p = Path('C:/projects/cambridge battlecode/work/neural-gameplay/diagnosis-phase2/runs/campnet-off/m00-o0-A/summary.json')
        if not p.exists():
            self.skipTest('previous-experiment summary not present')
        d = json.loads(p.read_text(encoding='utf-8'))
        cfg = R.RewardConfig()
        for c in d['roster']['champions']:
            s = R.series_from_summary(d, c['team'], int(c['id']))
            self.assertEqual(len(s.submitted), int(d['match']['roundsStarted']) + 1)
            rep = R.scale_report(s, cfg)
            self.assertTrue(rep['ok'], (c['name'], rep))
            final = next(int(x['metrics']['submittedGems']) for x in d['champions'] if x['id'] == c['id'])
            self.assertEqual(s.submitted[-1], final)
            self.assertGreaterEqual(s.carried.min(), 0)


if __name__ == '__main__':
    unittest.main()
