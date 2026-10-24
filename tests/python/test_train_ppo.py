"""PPO with runtime semantics on SYNTHETIC on-policy data: logit formula, C++-style logp parity, masks, options,
variable-gap GAE, stream separation, update metrics and authorization refusal. Not match training."""
import copy
import unittest

import numpy as np
import torch

import _fakes as F
from nfs.data import records_dataset as rd
from nfs.train import ppo
from nfs.train.auth import TrainingNotAuthorized
from nfs.train.value import Critic

HEADS = ('objective', 'move')


def np_reference_logits(model: F.FakePolicyNet, head, obs, feat, prior, legal):
    """Independent numpy implementation of FakePolicyNet + the runtime formula (stands in for the C++ kernel)."""
    W = {k: v.detach().double().numpy() for k, v in model.state_dict().items()}
    h = np.tanh(obs @ W['enc.weight'].T + W['enc.bias'])
    K, Fd = feat.shape
    f = np.pad(feat, ((0, 0), (0, F.F_MAX - Fd)))
    hh = np.repeat((h + W['head_emb.weight'][F.HEAD_ID[head]])[None, :], K, 0)
    x = np.concatenate([hh, f], 1)
    r = (np.tanh(x @ W['res.0.weight'].T + W['res.0.bias']) @ W['res.2.weight'].T + W['res.2.bias'])[:, 0]
    return ppo.runtime_logits_reference(prior.astype(np.float64), r, legal, model.R)


def real_cpp_twin_logits(model, head, obs, feat, prior, legal, context=0):
    """B's bit-exact numpy twin of the C++ kernels (nfs.models.reference) on the model's exported blob layout."""
    from nfs.models import layout, reference
    blob = np.concatenate([model.state_dict()[n].detach().cpu().numpy().astype(np.float32).ravel()
                           for n, _ in layout(model.cfg)])
    B = reference.Blob(model.cfg, blob)
    h = reference.encode(B, obs.astype(np.float32))
    return reference.candidate_logits(B, head, h, feat, legal, prior, context)


def log_softmax_np(z):
    m = np.max(z[np.isfinite(z)])
    lse = m + np.log(np.sum(np.exp(z[np.isfinite(z)] - m)))
    return np.where(np.isfinite(z), z - lse, -np.inf)


def onpolicy_stdout(model, rng, rounds, champs=(0, 1), real=False, extra=None):
    """Behaviour records as the training profile would log them: sampled choice + its log-probability."""
    lines = []
    for r in rounds:
        for c in champs:
            obs = rng.normal(size=model.obs_dim if hasattr(model, 'obs_dim') else F.OBS_DIM).astype(np.float32)
            lines.append(F.line(F.turn_payload(r, c, obs)))
            for head in HEADS:
                K, Fd = 5, F.head_F(head, model)
                feat = rng.normal(size=(K, Fd)).astype(np.float32)
                prior = np.sort(rng.normal(size=K).astype(np.float32))[::-1].copy()
                legal = np.array([1, 1, 1, 0, 1], np.uint8)
                if real:
                    z = real_cpp_twin_logits(model, head, obs, feat, prior, legal).astype(np.float64)
                else:
                    z = np_reference_logits(model, head, obs.astype(np.float64), feat.astype(np.float64), prior, legal)
                lp = log_softmax_np(z)
                p = np.exp(lp)
                chosen = int(rng.choice(K, p=p / p.sum()))
                kw = dict(extra(r, c, head) if extra else {})
                lines.append(F.line(F.decision_payload(r, c, F.HEAD_ID[head], prior, legal, feat, chosen,
                                                       float(lp[chosen]), logits=z.astype(np.float32), net=chosen, **kw)))
    return '\n'.join(lines)


def shard_for(model, real, seed=0, n_matches=2, extra=None):
    rng = np.random.default_rng(seed)
    shards = []
    for m in range(n_matches):
        n = 61
        series = {('teamA', 0): dict(submittedGems=[0] * 30 + [40] * 31, gems=[0] * 10 + [40] * 20 + [0] * 31,
                                     earnedGold=list(range(n)), deaths=[0] * n, championDamageDone=[0] * n),
                  ('teamA', 1): dict(submittedGems=[0] * n, gems=[0] * 20 + [25] * 20 + [0] * 21,
                                     earnedGold=list(range(n)), deaths=[0] * 40 + [1] * 21, championDamageDone=[0] * n)}
        s = F.make_summary(outcome='teamA' if m % 2 == 0 else 'teamB', rounds=60, gems=(40, 30), series=series)
        src = rd.MatchSource(match_id=f'local:syn{m}', side='A', summary=s,
                             stdout=onpolicy_stdout(model, rng, (3, 9, 20, 21, 35, 50), real=real, extra=extra))
        shards.append(rd.convert_match(src, encode=F.fake_encode, obs_dim=F.OBS_DIM if not real else None,
                                       synthetic=True, match_index=m))
    return rd.concat(shards)


class PPOTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(0)
        self.model, self.obs_dim, self.real = F.policy_net()
        if self.real:
            from nfs.models import init_untrained
            init_untrained(self.model, seed=5, zero_residual=False)   # synthetic weights with non-zero residuals
        if not hasattr(self.model, 'obs_dim'):
            self.model.obs_dim = self.obs_dim
        self.critic = Critic(self.obs_dim)

    def test_runtime_logit_formula(self):
        m = F.FakePolicyNet()
        h = m.encode(torch.randn(3, F.OBS_DIM))
        feat = torch.randn(3, 4, 6)
        legal = torch.tensor([[1, 1, 0, 1]] * 3).bool()
        prior = torch.randn(3, 4)
        z = m.head_logits('move', h, feat, legal, prior)
        ref = ppo.runtime_logits_reference(prior, m.residual('move', h, feat), legal, m.R)
        torch.testing.assert_close(z, ref)
        self.assertTrue(torch.isinf(z[:, 2]).all())
        self.assertTrue(((z - prior).abs()[legal] <= m.R + 1e-6).all())    # bounded residual
        # zero residual -> deployed argmax is the teacher; ties break to the lowest index
        zr = ppo.runtime_logits_reference(np.array([1.0, 1.0, 0.5]), np.zeros(3), np.array([1, 1, 1]), 2.0)
        self.assertEqual(int(np.argmax(zr)), 0)

    def test_cpp_style_logp_parity(self):
        shard = shard_for(self.model, self.real)
        b = ppo.make_batch(shard, self.critic, ppo.PPOConfig(), torch.device('cpu'))
        err = ppo.parity_check(self.model, b, ppo.head_names(), 1e-4)
        self.assertLess(err, 1e-4)
        self.assertTrue((b.logit_b.abs().sum(1) > 0).any())          # logged C++ logits were checked too
        bad = copy.deepcopy(b)
        bad.logp_b = bad.logp_b - 0.05
        with self.assertRaises(ppo.PolicyParityError):
            ppo.parity_check(self.model, bad, ppo.head_names(), 2e-3)
        bad = copy.deepcopy(b)
        bad.logit_b[:, 0] += 0.01                                     # same logp, different logged logits
        with self.assertRaises(ppo.PolicyParityError):
            ppo.parity_check(self.model, bad, ppo.head_names(), 2e-3)

    def test_parity_detects_other_policy(self):
        other = F.FakePolicyNet(seed=7)
        other.obs_dim = F.OBS_DIM
        shard = shard_for(other, False)
        with self.assertRaises(ppo.PolicyParityError):
            ppo.ppo_update(F.FakePolicyNet(seed=1), Critic(F.OBS_DIM), *self.opts(F.FakePolicyNet(seed=1)), shard,
                           ppo.PPOConfig(device='cpu'), authorized=True, time_limit_minutes=1)

    def opts(self, model, critic=None):
        return torch.optim.Adam(model.parameters(), 1e-3), torch.optim.Adam((critic or self.critic).parameters(), 1e-3)

    def test_ratio_mask_excludes_non_policy_rows(self):
        def extra(r, c, head):
            if r == 9:
                return dict(reason=3)                 # fallback / budget
            if r == 20:
                return dict(mode=1)                   # shadow: teacher executed
            if r == 21:
                return dict(sampled=0)                # deterministic argmax
            if r == 35:
                return dict(reason=200)               # forced commitment step (hypothetical code; none in nn_head.h)
            return {}
        model = F.FakePolicyNet(); model.obs_dim = F.OBS_DIM
        shard = shard_for(model, False, extra=extra)
        cfg = ppo.PPOConfig(forced_reasons=(200,), budget_reasons=(3,))
        mask, st = ppo.ratio_mask_np(shard, cfg)
        rounds = shard.meta['round']
        self.assertTrue(set(np.unique(rounds[mask])) <= {3, 50})
        self.assertGreater(mask.sum(), 0)
        n = len(shard)
        self.assertAlmostEqual(st['budget_skip_rate'], (rounds == 9).sum() / n)
        self.assertAlmostEqual(st['shadow_rate'], (rounds == 20).sum() / n)
        self.assertAlmostEqual(st['forced_rate'], (rounds == 35).sum() / n)
        self.assertAlmostEqual(st['fallback_rate'], ((rounds == 9) | (rounds == 35)).sum() / n)
        # option mode merges forced steps into the preceding option; exclude_forced keeps them as value rows
        b_opt = ppo.make_batch(shard, Critic(F.OBS_DIM), cfg, torch.device('cpu'))
        cfg_ex = ppo.PPOConfig(forced_reasons=(200,), commitment_mode='exclude_forced')
        b_ex = ppo.make_batch(shard, Critic(F.OBS_DIM), cfg_ex, torch.device('cpu'))
        self.assertGreater(b_opt.stats['merged_forced_steps'], 0)
        self.assertEqual(int(b_ex.value_mask.sum()), n)
        self.assertEqual(int(b_opt.value_mask.sum()), n - int((rounds == 35).sum()))
        self.assertFalse(b_ex.ratio_mask[torch.as_tensor(rounds == 35)].any())

    def test_merge_forced_discounting(self):
        g = 0.99
        rows = [dict(reward=1.0, tau=5, done=0, reason=0), dict(reward=2.0, tau=10, done=0, reason=7),
                dict(reward=3.0, tau=5, done=1, reason=0)]
        out = ppo.merge_forced(rows, g, {7})
        self.assertEqual(len(out), 2)
        self.assertAlmostEqual(out[0]['reward'], 1.0 + g ** 5 * 2.0)
        self.assertEqual(out[0]['tau'], 15)
        # the merged option's return equals the unmerged one
        full = 1.0 + g ** 5 * (2.0 + g ** 10 * 3.0)
        self.assertAlmostEqual(out[0]['reward'] + g ** out[0]['tau'] * out[1]['reward'], full)

    def test_gae_variable_gaps(self):
        g, lam = 0.99, 0.9
        r, v, tau, done = [1.0, 0.0, 2.0], [0.5, 0.2, 0.1], [3, 7, 4], [0, 0, 1]
        adv, ret = ppo.gae(r, v, tau, done, g, lam)
        d2 = 2.0 - 0.1
        d1 = 0.0 + g ** 7 * 0.1 - 0.2
        d0 = 1.0 + g ** 3 * 0.2 - 0.5
        a2 = d2; a1 = d1 + g ** 7 * lam * a2; a0 = d0 + g ** 3 * lam * a1
        np.testing.assert_allclose(adv, [a0, a1, a2])
        adv1, ret1 = ppo.gae(r, v, tau, done, g, 1.0)                  # lambda=1 -> Monte-Carlo SMDP return
        mc0 = 1.0 + g ** 3 * (0.0 + g ** 7 * 2.0)
        self.assertAlmostEqual(ret1[0], mc0)

    def test_streams_are_separate(self):
        model = F.FakePolicyNet(); model.obs_dim = F.OBS_DIM
        shard = shard_for(model, False)
        streams = ppo.streams_from_shard(shard, ppo.PPOConfig())
        keys = {(int(shard.meta['match_index'][s[0]]), int(shard.meta['champion'][s[0]]), int(shard.inputs['head'][s[0]]))
                for s in streams}
        self.assertEqual(len(keys), len(streams))
        self.assertEqual(len(streams), 2 * 2 * 2)                     # matches x champions x heads
        cfg = ppo.PPOConfig()
        critic = Critic(F.OBS_DIM)
        a0, _, _, _ = ppo.compute_advantages(shard, critic, cfg, 'cpu')
        s0, s1 = streams[0], streams[1]
        mod = copy.deepcopy(shard)
        mod.targets['reward'][s1] += 10.0
        a1, _, _, _ = ppo.compute_advantages(mod, critic, cfg, 'cpu')
        np.testing.assert_allclose(a0[s0], a1[s0])
        self.assertFalse(np.allclose(a0[s1], a1[s1]))

    def test_ppo_update_synthetic(self):
        model = self.model
        shard = shard_for(model, self.real, seed=3, n_matches=4)
        critic = Critic(shard.inputs['obs'].shape[1])
        before = copy.deepcopy(model.state_dict())
        aopt, copt = self.opts(model, critic)
        cfg = ppo.PPOConfig(epochs=3, minibatch=16, device='cpu', target_kl=10.0)
        with self.assertRaises(TrainingNotAuthorized):
            ppo.ppo_update(model, critic, aopt, copt, shard, cfg, authorized=False, time_limit_minutes=1)
        with self.assertRaises(TrainingNotAuthorized):
            ppo.ppo_update(model, critic, aopt, copt, shard, cfg, authorized=True, time_limit_minutes=None)
        m = ppo.ppo_update(model, critic, aopt, copt, shard, cfg, authorized=True, time_limit_minutes=1)
        for k in ('approx_kl', 'clip_frac', 'entropy', 'grad_norm', 'explained_variance_after', 'critic_mae',
                  'reward_components', 'action_distribution', 'invalid_action_rate', 'fallback_rate',
                  'budget_skip_rate', 'parity_max_abs_logp_error'):
            self.assertIn(k, m)
        self.assertGreater(m['minibatches'], 0)
        self.assertTrue(any(not torch.equal(before[k], v) for k, v in model.state_dict().items()))
        self.assertEqual(set(m['action_distribution']), set(HEADS))

    def test_kl_early_stop(self):
        model = F.FakePolicyNet(); model.obs_dim = F.OBS_DIM
        shard = shard_for(model, False, seed=4, n_matches=4)
        critic = Critic(F.OBS_DIM)
        aopt = torch.optim.SGD(model.parameters(), lr=5.0)
        copt = torch.optim.Adam(critic.parameters(), 1e-3)
        m = ppo.ppo_update(model, critic, aopt, copt, shard, ppo.PPOConfig(epochs=10, minibatch=8, target_kl=1e-6,
                                                                              max_grad_norm=100.0, device='cpu'),
                           authorized=True, time_limit_minutes=1)
        self.assertTrue(m['early_stop_kl'])
        self.assertLess(m['epochs_run'], 10)


if __name__ == '__main__':
    unittest.main()
