"""Imitation and value training on tiny SYNTHETIC batches: loss decreases, grouped validation guards, early stopping,
per-head ablation, authorization refusal. No match data; nothing is written to models/."""
import unittest

import numpy as np
import torch

import _fakes as F
from nfs.data import records_dataset as rd
from nfs.train import imitation as I
from nfs.train import value as V
from nfs.train.auth import TrainingNotAuthorized

HEADS = ('objective', 'move')


def labelled_shard(model, obs_dim, n, seed, partition, match_prefix):
    """Teacher label = argmax of legal feature 0 (a learnable synthetic 'other teacher'); outcome = sign(obs[0])."""
    rng = np.random.default_rng(seed)
    K = 5
    inp = dict(obs=rng.normal(size=(n, obs_dim)).astype(np.float32), obs_valid=np.ones(n, np.uint8),
               feat=np.zeros((n, rd.K_MAX, rd.F_MAX), np.float32), legal=np.zeros((n, rd.K_MAX), bool),
               prior=np.zeros((n, rd.K_MAX), np.float32), K=np.full(n, K, np.int16), F=np.zeros(n, np.int16),
               head=np.zeros(n, np.int16), context=np.zeros(n, np.uint8))
    tg = {k: np.zeros(n, np.float32) for k in rd.TARGET_FIELDS}
    tg['teacher'] = np.zeros(n, np.int16); tg['chosen'] = np.zeros(n, np.int16); tg['done'] = np.zeros(n, np.uint8)
    for i in range(n):
        head = HEADS[i % 2]
        Fd = F.head_F(head, model)
        inp['head'][i], inp['F'][i] = F.HEAD_ID[head], Fd
        inp['feat'][i, :K, :Fd] = rng.normal(size=(K, Fd))
        inp['legal'][i, :K] = True
        inp['legal'][i, rng.integers(1, K)] = False
        f0 = np.where(inp['legal'][i, :K], inp['feat'][i, :K, 0], -np.inf)
        tg['teacher'][i] = int(np.argmax(f0))
        tg['outcome'][i] = float(inp['obs'][i, 0] > 0)
        tg['margin'][i] = 0.3 * inp['obs'][i, 1]
    meta = dict(match_index=np.arange(n, dtype=np.int32), side=np.full(n, 65, np.uint8), champion=np.zeros(n, np.uint32),
                round=np.zeros(n, np.int32), seq=np.arange(n, dtype=np.int32), reason=np.zeros(n, np.uint8),
                mode=np.full(n, 2, np.uint8), sampled=np.ones(n, np.uint8), stream=np.arange(n, dtype=np.int32),
                schema_hash=np.zeros(n, np.uint32), cand_id=np.zeros((n, rd.K_MAX), np.uint32),
                champion_mapped=np.ones(n, np.uint8))
    return rd.Shard(inp, tg, meta, dict(partition=partition, synthetic=True,
                                        matches=[f'{match_prefix}{i}' for i in range(n)]))


class TrainImitationValueTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(0)
        self.model, self.obs_dim, self.real = F.policy_net()
        if self.real:
            from nfs.models import init_untrained
            init_untrained(self.model, seed=3, zero_residual=False)
        self.tr = labelled_shard(self.model, self.obs_dim, 256, 1, 'train', 'tr')
        self.va = labelled_shard(self.model, self.obs_dim, 128, 2, 'validation', 'va')

    def test_refuses_without_authorization(self):
        for kw in (dict(authorized=False, time_limit_minutes=5), dict(authorized=True, time_limit_minutes=None),
                   dict(authorized=True, time_limit_minutes=0), dict(authorized=True, time_limit_minutes=5000)):
            with self.assertRaises(TrainingNotAuthorized):
                I.pretrain(self.model, self.tr, self.va, I.ImitationConfig(device='cpu'), **kw)
            with self.assertRaises(TrainingNotAuthorized):
                V.train_value(self.model, self.tr, self.va, V.ValueConfig(device='cpu'), **kw)

    def test_imitation_loss_decreases_synthetic(self):
        cfg = I.ImitationConfig(device='cpu', max_epochs=25, lr=1e-2, batch_size=64, patience=30, value_weight=0.0)
        rep = I.pretrain(self.model, self.tr, self.va, cfg, authorized=True, time_limit_minutes=2)
        self.assertLess(rep['early_stopping']['best'], rep['initial_val_objective'] - 0.05, rep['history'][-1])
        self.assertEqual(set(rep['history'][-1]['per_head']), set(HEADS))

    def test_head_ablation(self):
        cfg = I.ImitationConfig(device='cpu', max_epochs=1, head_weights={'move': 0.0}, value_weight=0.0)
        rep = I.pretrain(self.model, self.tr, self.va, cfg, authorized=True, time_limit_minutes=1)
        self.assertEqual(set(rep['history'][0]['per_head']), {'objective'})

    def test_grouped_validation_guards(self):
        leak = labelled_shard(self.model, self.obs_dim, 32, 3, 'validation', 'tr')       # shares match ids
        with self.assertRaises(ValueError):
            I.pretrain(self.model, self.tr, leak, I.ImitationConfig(device='cpu'), authorized=True, time_limit_minutes=1)
        final = labelled_shard(self.model, self.obs_dim, 32, 4, 'final_eval', 'fe')
        with self.assertRaises(ValueError):
            V.train_value(self.model, final, self.va, V.ValueConfig(device='cpu'), authorized=True, time_limit_minutes=1)

    def test_value_loss_decreases_and_early_stops(self):
        cfg = V.ValueConfig(device='cpu', max_epochs=40, lr=1e-2, batch_size=64, patience=3)
        with torch.no_grad():
            x = torch.as_tensor(self.va.inputs['obs'])
            before, _ = V.value_loss(self.model, x, torch.as_tensor(self.va.targets['outcome']),
                                     torch.as_tensor(self.va.targets['margin']), cfg)
        rep = V.train_value(self.model, self.tr, self.va, cfg, authorized=True, time_limit_minutes=2)
        self.assertLess(rep['early_stopping']['best'], float(before))
        self.assertLessEqual(len(rep['history']), cfg.max_epochs)

    def test_draft_outcome_observational(self):
        rng = np.random.default_rng(0)
        rows, assign = [], {}
        for i in range(300):
            a = rng.choice(12, 3, replace=False).tolist(); b = rng.choice(12, 3, replace=False).tolist()
            rows.append(dict(match_id=f'd{i}', label_scope='draft_observational', picks={'teamA': a, 'teamB': b},
                             first_pick='teamA', outcome='teamA' if (0 in a) or rng.random() < 0.3 else 'teamB'))
            assign[f'd{i}'] = 'train' if i < 200 else 'validation' if i < 260 else 'final_eval'
        rep = V.train_draft_outcome(rows, assign, V.ValueConfig(device='cpu', max_epochs=30, lr=1e-2),
                                    authorized=True, time_limit_minutes=1)
        self.assertTrue(rep['confounded'])
        self.assertEqual(rep['val_rows'], 120)
        self.assertLess(rep['early_stopping']['best'], rep['history'][0]['val_bce'] + 1e-9)


if __name__ == '__main__':
    unittest.main()
