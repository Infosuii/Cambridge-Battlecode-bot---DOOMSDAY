import copy
import math
import unittest
import torch
from rl_learner_1104.cl1 import CampPointer, GLOBAL_WIDTH, PREPROCESS_VERSION
from rl_learner_1104.model import Critic
from rl_learner_1104.on_policy import Trajectory, REWARD_SPEC, replay_logp, team_reward, update, validate
from rl_learner_1104.returns import gae


class OnPolicyTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(2)
        torch.manual_seed(1104)
        self.actor = CampPointer()
        self.critic = Critic(GLOBAL_WIDTH)
        n = 6
        x = torch.zeros(n, 448, dtype=torch.int16)
        x[:, 0] = torch.arange(n, dtype=torch.int16)
        x[:, 224] = 1; x[:, 240] = 1
        x[:, 225] = torch.arange(1, n+1, dtype=torch.int16)
        x[:, 241] = 15
        mask = torch.zeros(n, 13, dtype=torch.bool)
        mask[:, [0, 1, 12]] = True
        meta = dict(sampling='complete', layout=10, action_schema='target13-cl1-nofarm-v1',
                    preprocess=PREPROCESS_VERSION, actor_sha256='fixture-only', reward_spec=REWARD_SPEC,
                    temperature=1., incomplete=False, fuel_failed=False, log_cut=False,
                    policy_wasm_sha256='fixture-only', encoder_sha256='fixture-only',
                    engine_build_hash='fixture-only', map_sha256='fixture-only', episode_key='fixture-only', body_id=0)
        self.t = Trajectory(x, torch.cat((x[1:], x[-1:])), torch.tensor([0, 1, 12, 1, 0, 12]),
                            torch.tensor([0, 1, 12, 1, 0, 12]), mask, torch.zeros(n),
                            torch.tensor([1, 0, 0, 1, 0, 0], dtype=torch.bool),
                            torch.tensor([0., 0., 0., 0., 0., 1.]), [1]*n,
                            [False]*5+[True], [False]*n, [True]*5+[False], meta)
        with torch.no_grad():
            self.t.old_logp = replay_logp(self.actor, self.t)[0].detach()

    def test_complete_update_finite_and_changes_actor(self):
        before = copy.deepcopy(self.actor.state_dict())
        result = update(self.actor, self.critic, [self.t], 'fixture-only', epochs=2, chunk=2)
        self.assertEqual(result['rows'], 6)
        self.assertLess(result['max_initial_logp_error'], 1e-7)
        self.assertTrue(any(not torch.equal(v, self.actor.state_dict()[k]) for k, v in before.items()))
        self.assertTrue(all(math.isfinite(v) for e in result['history'] for v in e.values()))

    def test_stale_logp_rejected_before_mutation(self):
        before = copy.deepcopy(self.actor.state_dict())
        self.t.old_logp[0] -= .1
        with self.assertRaisesRegex(ValueError, 'logged policy'):
            update(self.actor, self.critic, [self.t], 'fixture-only')
        self.assertTrue(all(torch.equal(v, self.actor.state_dict()[k]) for k, v in before.items()))

    def test_teacher_and_failure_flags_rejected(self):
        for key, bad in [('sampling','teacher'), ('fuel_failed',True), ('incomplete',True),
                         ('log_cut',True), ('temperature',.5)]:
            old = self.t.metadata[key]; self.t.metadata[key] = bad
            with self.assertRaises(ValueError):
                validate(self.t, 'fixture-only')
            self.t.metadata[key] = old

    def test_censored_or_changed_actions_rejected(self):
        self.t.executed[0] = 1
        with self.assertRaisesRegex(ValueError, 'executor'):
            validate(self.t, 'fixture-only')
        self.t.executed[0] = 0
        self.t.next_raw[0, 0] = 99
        with self.assertRaisesRegex(ValueError, 'chronological'):
            validate(self.t, 'fixture-only')

    def test_truncation_requires_real_boundary(self):
        self.t.terminated[-1] = False; self.t.truncated[-1] = True
        with self.assertRaisesRegex(ValueError, 'bootstrap'):
            validate(self.t, 'fixture-only')
        self.t.bootstrap_valid[-1] = True
        validate(self.t, 'fixture-only')

    def test_zero_time_terminal_and_respawn(self):
        a, _ = gae([0., 1.], [0., 0.], [0., 999.], [2, 0], [False, True], [False, False], gamma=1., lam=1.)
        self.assertEqual(a, [1., 1.])
        self.t.elapsed[-1] = 0
        validate(self.t, 'fixture-only')
        # Reset after respawn clears recurrent state but is not a team terminal.
        self.assertTrue(self.t.reset[3]); self.assertFalse(self.t.terminated[3])

    def test_potential_telescopes_to_discounted_win(self):
        gamma = .9
        r1 = team_reward(0, 0, 20, 0, 100, 2, gamma=gamma)
        r2 = team_reward(20, 0, 100, 0, 100, 3, terminal=True, outcome=1, gamma=gamma)
        self.assertAlmostEqual(r1 + gamma**2 * r2, gamma**5)
        self.assertLess(abs(r1), .1)

    def test_missing_h0_and_duplicates_rejected(self):
        self.t.reset[0] = False
        with self.assertRaisesRegex(ValueError, 'hidden'):
            validate(self.t, 'fixture-only')
        self.t.reset[0] = True
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            update(self.actor, self.critic, [self.t, self.t], 'fixture-only')


if __name__ == '__main__':
    unittest.main()
