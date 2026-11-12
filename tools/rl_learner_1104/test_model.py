import unittest
import torch
from rl_learner_1104.model import Actor, Critic, joint_statistics, masked_distribution, ppo_loss


class ModelTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(1104)
        self.actor = Actor({'enemy': 4, 'camp': 3}, 5, 2, {'move': 9, 'bank': 2})
        self.entities = {'enemy': torch.randn(2, 3, 4), 'camp': torch.randn(2, 4, 3)}
        self.present = {'enemy': torch.ones(2, 3, dtype=torch.bool),
                        'camp': torch.ones(2, 4, dtype=torch.bool)}
        self.g, self.b = torch.randn(2, 5), torch.randn(2, 2)

    def run_actor(self, h=None, reset=None):
        return self.actor(self.entities, self.present, self.g, self.b,
                          self.actor.initial_state(2) if h is None else h,
                          torch.zeros(2, dtype=torch.bool) if reset is None else reset)

    def test_absent_entities_do_not_affect_policy(self):
        self.present['enemy'][:] = False
        first, _ = self.run_actor()
        self.entities['enemy'][:] = float('nan')
        second, _ = self.run_actor()
        for name in first:
            torch.testing.assert_close(first[name], second[name])
            self.assertTrue(torch.isfinite(second[name]).all())

    def test_memory_reset(self):
        first, _ = self.run_actor()
        reset, _ = self.run_actor(torch.randn(2, 16), torch.ones(2, dtype=torch.bool))
        for name in first:
            torch.testing.assert_close(first[name], reset[name])

    def test_illegal_action_probability_zero(self):
        d = masked_distribution(torch.zeros(1, 3), torch.tensor([[False, True, False]]))
        torch.testing.assert_close(d.probs, torch.tensor([[0., 1., 0.]]))
        with self.assertRaises(ValueError):
            masked_distribution(torch.zeros(1, 3), torch.zeros(1, 3, dtype=torch.bool))

    def test_inactive_heads_excluded(self):
        logits = {'move': torch.zeros(2, 3), 'cast': torch.zeros(2, 2)}
        masks = {'move': torch.ones(2, 3, dtype=torch.bool),
                 'cast': torch.tensor([[True, False], [False, False]])}
        actions = {'move': torch.tensor([0, 1]), 'cast': torch.tensor([0, -1])}
        active = {'move': torch.tensor([True, True]), 'cast': torch.tensor([True, False])}
        logp, _ = joint_statistics(logits, masks, actions, active)
        torch.testing.assert_close(logp, torch.full((2,), -torch.log(torch.tensor(3.)).item()))

    def test_gradients_and_privileged_separation(self):
        logits, _ = self.run_actor()
        critic = Critic(7)
        value = critic(torch.randn(2, 7))
        d = masked_distribution(logits['move'], torch.ones(2, 9, dtype=torch.bool))
        logp = d.log_prob(torch.tensor([0, 1]))
        loss = ppo_loss(logp, logp.detach(), torch.tensor([1., -1.]),
                        value, torch.tensor([1., 0.]), d.entropy())
        loss.backward()
        self.assertTrue(all(torch.isfinite(p.grad).all() for p in self.actor.parameters() if p.grad is not None))
        self.assertFalse(set(map(id, self.actor.parameters())) & set(map(id, critic.parameters())))


if __name__ == '__main__':
    unittest.main()
