"""Checkpoint save/resume round trip: parameters, optimizers, RNG, persisted deadline, games ledger, pairing refusal."""
import random
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np
import torch

import _fakes as F
from nfs.train import checkpoint as C
from nfs.train.league import League
from nfs.train.value import Critic


def make():
    actor = F.FakePolicyNet(seed=1)
    critic = Critic(F.OBS_DIM)
    aopt = torch.optim.Adam(actor.parameters(), 1e-3)
    copt = torch.optim.Adam(critic.parameters(), 1e-3)
    sched = torch.optim.lr_scheduler.StepLR(aopt, 10, 0.5)
    return actor, critic, aopt, copt, sched


def train_step(actor, critic, aopt, copt, sched):
    x = torch.randn(8, F.OBS_DIM)
    loss = actor.values(actor.encode(x))['win_logit'].pow(2).mean() + critic(x, torch.zeros(8, dtype=torch.long)).pow(2).mean()
    aopt.zero_grad(); copt.zero_grad(); loss.backward(); aopt.step(); copt.step(); sched.step()


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = Path(self.tmp.name) / 'run'

    def tearDown(self):
        self.tmp.cleanup()

    def test_roundtrip_with_rng_and_optimizer(self):
        torch.manual_seed(0); np.random.seed(0); random.seed(0)
        a, c, ao, co, s = make()
        clock = C.RunClock.authorize(self.run, 30, 'r1')
        ledger = C.GamesLedger(self.run)
        ledger.account(self.run / 'games' / 'g1')
        for _ in range(3):
            train_step(a, c, ao, co, s)
        lg = League(seed=3)
        meta = C.save_checkpoint(self.run / 'latest.pt', actor=a, critic=c, actor_opt=ao, critic_opt=co, scheduler=s,
                                 league_state=lg.state_dict(), obs_schema_hash=11, action_schema_hash='h',
                                 provenance=dict(split='splits_v1', synthetic=True), ledger=ledger, clock=clock,
                                 counters=dict(iteration=3, games=1))
        expect = (random.random(), float(np.random.rand()), float(torch.rand(1)))
        train_step(a, c, ao, co, s)                             # continue the original run one step
        cont = {k: v.clone() for k, v in a.state_dict().items()}
        a2, c2, ao2, co2, s2 = make()
        st = C.resume(self.run, actor=a2, critic=c2, actor_opt=ao2, critic_opt=co2, scheduler=s2,
                      obs_schema_hash=11, action_schema_hash='h')
        self.assertEqual((random.random(), float(np.random.rand()), float(torch.rand(1))), expect)
        self.assertEqual(st['counters'], dict(iteration=3, games=1))
        self.assertEqual(st['meta']['pairing_id'], meta['pairing_id'])
        self.assertEqual(s2.state_dict()['last_epoch'], 3)
        self.assertEqual(League.from_state(st['league']).seed, 3)
        # the resumed run reproduces the original's next step exactly (same RNG draws, optimizer moments, schedule)
        train_step(a2, c2, ao2, co2, s2)
        for k, v in a2.state_dict().items():
            self.assertTrue(torch.equal(v, cont[k]), k)
        self.assertEqual(C.param_hash(make()[0]), C.param_hash(make()[0]))
        self.assertFalse(list(self.run.glob('*.tmp')))

    def test_deadline_persisted_not_reset(self):
        c1 = C.RunClock.authorize(self.run, 10, 'r1')
        time.sleep(0.05)
        c2 = C.RunClock.authorize(self.run, 600, 'r1')          # resume with a larger request: deadline unchanged
        self.assertEqual(c1.deadline_epoch, c2.deadline_epoch)
        self.assertEqual(C.RunClock.load(self.run).deadline_epoch, c1.deadline_epoch)
        with self.assertRaises(C.CheckpointError):
            C.RunClock.authorize(self.run, 10, 'other-run')
        a, c, ao, co, s = make()
        C.save_checkpoint(self.run / 'latest.pt', actor=a, critic=c, actor_opt=ao, critic_opt=co, clock=c1)
        st = C.resume(self.run, actor=make()[0], critic=Critic(F.OBS_DIM))
        self.assertEqual(st['clock'].deadline_epoch, c1.deadline_epoch)

    def test_ledger_never_recounts(self):
        C.RunClock.authorize(self.run, 10, 'r1')
        led = C.GamesLedger(self.run)
        self.assertTrue(led.account(self.run / 'g' / 'a'))
        self.assertFalse(led.account(self.run / 'g' / 'a'))
        self.assertFalse(led.account(str(self.run / 'g' / 'a').upper()))   # Windows paths: case-insensitive key
        led.save()
        led2 = C.GamesLedger(self.run)
        self.assertFalse(led2.account(self.run / 'g' / 'a'))
        self.assertTrue(led2.account(self.run / 'g' / 'b'))
        self.assertEqual(len(led2), 2)

    def test_actor_only_selection_refused_without_reset(self):
        C.RunClock.authorize(self.run, 10, 'r1')
        a, c, ao, co, s = make()
        C.save_checkpoint(self.run / 'latest.pt', actor=a, critic=c, actor_opt=ao, critic_opt=co)
        train_step(a, c, ao, co, s)
        C.save_checkpoint(self.run / 'best_actor.pt', actor=a)          # selected actor, no critic/optimizer
        a2, c2, ao2, co2, _ = make()
        with self.assertRaises(C.CheckpointError):
            C.resume(self.run, actor=a2, critic=c2, actor_opt=ao2, critic_opt=co2, actor_from=self.run / 'best_actor.pt')
        st = C.resume(self.run, actor=a2, critic=c2, actor_opt=ao2, critic_opt=co2,
                      actor_from=self.run / 'best_actor.pt', reset_critic_optimizer=True)
        self.assertTrue(st['reset_critic_optimizer'])
        self.assertEqual(C.param_hash(a2), C.param_hash(a))
        self.assertEqual(ao2.state_dict()['state'], {})                  # fresh optimizer, not the stale one

    def test_selected_full_pair_loads_its_own_critic(self):
        C.RunClock.authorize(self.run, 10, 'r1')
        a, c, ao, co, s = make()
        C.save_checkpoint(self.run / 'best.pt', actor=a, critic=c, actor_opt=ao, critic_opt=co)
        best_critic = C.param_hash(c)
        train_step(a, c, ao, co, s)
        C.save_checkpoint(self.run / 'latest.pt', actor=a, critic=c, actor_opt=ao, critic_opt=co)
        a2, c2, ao2, co2, _ = make()
        C.resume(self.run, actor=a2, critic=c2, actor_opt=ao2, critic_opt=co2, actor_from=self.run / 'best.pt')
        self.assertEqual(C.param_hash(c2), best_critic)                  # never the later (stale) critic

    def test_schema_mismatch_refused(self):
        C.RunClock.authorize(self.run, 10, 'r1')
        a, c, ao, co, s = make()
        C.save_checkpoint(self.run / 'latest.pt', actor=a, critic=c, actor_opt=ao, critic_opt=co, obs_schema_hash=1)
        with self.assertRaises(C.CheckpointError):
            C.resume(self.run, actor=make()[0], critic=Critic(F.OBS_DIM), obs_schema_hash=2)

    def test_corrupt_hash_detected(self):
        C.RunClock.authorize(self.run, 10, 'r1')
        a, c, ao, co, s = make()
        C.save_checkpoint(self.run / 'latest.pt', actor=a, critic=c, actor_opt=ao, critic_opt=co)
        d = C.load_checkpoint(self.run / 'latest.pt')
        d['meta']['actor_hash'] = '0' * 64
        torch.save(d, self.run / 'latest.pt')
        with self.assertRaises(C.CheckpointError):
            C.resume(self.run, actor=make()[0], critic=Critic(F.OBS_DIM))

    def test_unauthorized_run_has_no_clock(self):
        with self.assertRaises(C.CheckpointError):
            C.RunClock.load(self.run)


if __name__ == '__main__':
    unittest.main()
