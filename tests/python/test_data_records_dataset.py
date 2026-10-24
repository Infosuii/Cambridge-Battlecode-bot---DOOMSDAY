"""NFS1 records -> shards: decoding, input/target separation, outcome leakage (synthetic records only)."""
import tempfile
import unittest
from pathlib import Path

import numpy as np

import _fakes as F
from nfs.data import records_dataset as rd
from nfs.train.rewards import RewardConfig


def synthetic_stdout(rng, rounds=(5, 12, 30, 31), champs=(0, 1), heads=('objective', 'move'), reason=0, sampled=1):
    lines = ['some ordinary bot output']
    for r in rounds:
        for c in champs:
            obs = rng.normal(size=F.OBS_DIM).astype(np.float32)
            lines.append(F.line(F.turn_payload(r, c, obs)))
            for h in heads:
                K, Fd = 4, F.head_F(h)
                feat = rng.normal(size=(K, Fd)).astype(np.float32)
                prior = np.array([1.0, 0.5, 0.0, -1.0], np.float32)
                legal = np.array([1, 1, 0, 1], np.uint8)
                lines.append(F.line(F.decision_payload(r, c, F.HEAD_ID[h], prior, legal, feat, chosen=1, logp=-0.7,
                                                       reason=reason, sampled=sampled)))
    lines.append('NFS1 !!!not-base64!!!')
    return '\n'.join(lines)


def source(stdout, outcome='teamA', engine='1.0.3', mid='local:x'):
    n = 41
    series = {('teamA', 0): dict(submittedGems=[0] * 20 + [50] * 21, gems=[0] * 10 + [50] * 10 + [0] * 21,
                                 earnedGold=list(range(n)), deaths=[0] * n, championDamageDone=[0] * n),
              ('teamA', 1): dict(submittedGems=[0] * n, gems=[0] * 15 + [30] * 10 + [0] * 16,
                                 earnedGold=list(range(n)), deaths=[0] * 25 + [1] * 16, championDamageDone=[0] * n)}
    s = F.make_summary(engine=engine, outcome=outcome, rounds=40, gems=(50, 20), series=series)
    return rd.MatchSource(match_id=mid, side='A', summary=s, stdout=stdout)


class RecordsDatasetTests(unittest.TestCase):
    def convert(self, src, **kw):
        return rd.convert_match(src, encode=F.fake_encode, obs_dim=F.OBS_DIM, synthetic=True, **kw)

    def test_reference_decoder_roundtrip(self):
        rng = np.random.default_rng(0)
        feat = rng.normal(size=(3, 5)).astype(np.float32)
        p = F.decision_payload(7, 2, 6, [0.5, 0.1, -0.2], [1, 0, 1], feat, chosen=2, logp=-1.25, mode=2, reason=0,
                               context=3, sampled=1, ids=[10, 11, 12])
        r = rd.reference_decode_payload(p)
        self.assertEqual((r['round'], r['champion'], r['head'], r['K'], r['F'], r['chosen'], r['context']), (7, 2, 6, 3, 5, 2, 3))
        np.testing.assert_array_equal(r['feat'], feat)
        np.testing.assert_array_equal(r['id'], [10, 11, 12])
        self.assertAlmostEqual(r['logp'], -1.25)
        p2 = F.decision_payload(7, 2, 6, [0.5, 0.1, -0.2], [1, 0, 1], feat, chosen=2, logp=-1.25,
                                logits=[0.7, -np.inf, 0.1], net=2, action_hash=99, call=4)
        r2 = rd.reference_decode_payload(p2)
        self.assertEqual((r2['net'], r2['action_hash'], r2['call']), (2, 99, 4))
        self.assertTrue(np.isneginf(r2['logit'][1]))
        t = rd.reference_decode_payload(F.turn_payload(3, 1, np.arange(4, dtype=np.float32)))
        np.testing.assert_array_equal(F.fake_encode(t['payload']), np.arange(4))
        with self.assertRaises(rd.DatasetError):
            rd.reference_decode_payload(F.turn_payload(3, 1, np.arange(4, dtype=np.float32))[:-3])
        with self.assertRaises(rd.DatasetError):
            rd.reference_decode_payload(p[:30])

    def test_active_decoder_parses_contract_records(self):
        """Uses B's nfs.records when importable (decoder()), else the reference decoder."""
        dec, name = rd.decoder()
        rng = np.random.default_rng(1)
        recs = dec(synthetic_stdout(rng))
        kinds = [r.get('kind') for r in recs]
        self.assertEqual(kinds.count(rd.KIND_DECISION), 16, name)
        self.assertEqual(kinds.count(rd.KIND_TURN), 8, name)

    def test_shard_shapes_and_counts(self):
        sh = self.convert(source(synthetic_stdout(np.random.default_rng(2))))
        self.assertEqual(len(sh), 16)
        self.assertEqual(sh.inputs['feat'].shape, (16, rd.K_MAX, rd.F_MAX))
        self.assertEqual(sh.inputs['obs'].shape, (16, F.OBS_DIM))
        self.assertTrue((sh.inputs['obs_valid'] == 1).all())
        self.assertFalse(sh.inputs['legal'][:, 2].any())
        self.assertEqual(sh.manifest['counts']['undecodable'], 1)
        self.assertEqual(sh.manifest['counts']['streams'], 4)
        self.assertTrue(sh.manifest['synthetic'])
        self.assertEqual(sh.manifest['champion_mapping'], 'identity')

    def test_no_outcome_or_future_in_inputs(self):
        rng_a, rng_b = np.random.default_rng(3), np.random.default_rng(3)
        win = self.convert(source(synthetic_stdout(rng_a), outcome='teamA'))
        loss = self.convert(source(synthetic_stdout(rng_b), outcome='teamB'))
        for k in rd.INPUT_FIELDS:
            np.testing.assert_array_equal(win.inputs[k], loss.inputs[k], err_msg=k)
        self.assertFalse(np.array_equal(win.targets['outcome'], loss.targets['outcome']))
        self.assertFalse(np.array_equal(win.targets['return_mc'], loss.targets['return_mc']))
        for k in win.inputs:
            self.assertFalse(any(t in k for t in rd.FORBIDDEN_INPUT_TOKENS), k)
        self.assertFalse(set(win.inputs) & set(win.targets))

    def test_shard_rejects_leaky_inputs(self):
        sh = self.convert(source(synthetic_stdout(np.random.default_rng(4))))
        bad = dict(sh.inputs, outcome=sh.targets['outcome'])
        with self.assertRaises(rd.DatasetError):
            rd.Shard(bad, sh.targets, sh.meta)
        with self.assertRaises(rd.DatasetError):
            rd.Shard(dict(sh.inputs, final_gems=sh.targets['margin']), sh.targets, sh.meta)

    def test_save_load_roundtrip(self):
        sh = self.convert(source(synthetic_stdout(np.random.default_rng(5))))
        with tempfile.TemporaryDirectory() as td:
            p = sh.save(Path(td) / 's.npz')
            back = rd.Shard.load(p)
            for g in ('inputs', 'targets', 'meta'):
                for k, v in getattr(sh, g).items():
                    np.testing.assert_array_equal(v, getattr(back, g)[k])
            self.assertEqual(back.manifest['schema'], rd.SCHEMA)
            self.assertIn('sha256', back.manifest)

    def test_refuses_non_103_summary(self):
        with self.assertRaises(rd.DatasetError):
            self.convert(source(synthetic_stdout(np.random.default_rng(6)), engine='1.0.2'))

    def test_schema_hash_check(self):
        with self.assertRaises(rd.DatasetError):
            self.convert(source(synthetic_stdout(np.random.default_rng(7))), expected_obs_schema=1)

    def test_returns_match_rewards(self):
        cfg = RewardConfig()
        sh = self.convert(source(synthetic_stdout(np.random.default_rng(8))), reward_cfg=cfg)
        m, t = sh.meta, sh.targets
        for s in np.unique(m['stream']):
            idx = np.flatnonzero(m['stream'] == s)
            idx = idx[np.argsort(m['round'][idx])]
            g = 0.0
            for i in reversed(idx):
                g = t['reward'][i] + cfg.gamma ** t['tau'][i] * (0 if t['done'][i] else g)
                self.assertAlmostEqual(g, t['return_mc'][i], places=4)
            self.assertEqual(t['done'][idx[-1]], 1)
        comps = sum(t['r_' + c] for c in ('terminal', 'deposit', 'carry_shaping', 'economy', 'death', 'damage', 'objective'))
        np.testing.assert_allclose(comps, t['reward'], atol=1e-5)

    def test_build_dataset_partitions_and_dedupe(self):
        with tempfile.TemporaryDirectory() as td:
            s1 = source(synthetic_stdout(np.random.default_rng(9)), mid='local:a')
            s2 = source(synthetic_stdout(np.random.default_rng(10)), mid='local:b')
            dup = source(synthetic_stdout(np.random.default_rng(9)), mid='local:a')
            man = rd.build_dataset([s1, s2, dup], td, name='syn', partition_of=lambda s: 'train' if s.match_id == 'local:a' else 'validation',
                                   encode=F.fake_encode, obs_dim=F.OBS_DIM, synthetic=True)
            self.assertEqual(man['accounting']['independent_matches'], 2)
            self.assertEqual(set(man['files']), {'train', 'validation'})
            self.assertTrue(any(s.get('skipped') for s in man['sources']))
            tr = rd.Shard.load(Path(td) / man['files']['train']['file'])
            self.assertEqual(tr.manifest['partition'], 'train')


if __name__ == '__main__':
    unittest.main()
