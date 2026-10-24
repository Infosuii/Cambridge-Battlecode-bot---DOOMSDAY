"""CLI refusals (no authorization flag / no time limit / gate missing) and league semantics. No games, no training."""
import contextlib
import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import torch

import _fakes as F
from nfs import cli
from nfs.train import checkpoint as C
from nfs.train import league as L


def run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli.main(argv)
    return code, buf.getvalue()


class CLITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_parameter_updating_commands_refuse_without_flag(self):
        for cmd in ('pretrain', 'train-value', 'rl'):
            rd = self.d / cmd
            code, out = run([cmd, '--run-dir', str(rd), '--time-limit-minutes', '5'])
            self.assertEqual(code, 2, cmd)
            self.assertIn('--i-authorize-training', out)
            code, out = run([cmd, '--run-dir', str(rd), '--i-authorize-training'])
            self.assertEqual(code, 2, cmd)
            self.assertIn('time-limit', out)
            code, out = run([cmd, '--run-dir', str(rd), '--i-authorize-training', '--time-limit-minutes', '-1'])
            self.assertEqual(code, 2, cmd)
            self.assertFalse((rd / 'clock.json').exists())

    def test_collect_refuses_without_flag(self):
        code, out = run(['collect', '--run-dir', str(self.d / 'c'), '--max-games', '2', '--time-limit-minutes', '1'])
        self.assertEqual(code, 2)
        self.assertIn('--i-authorize-collection', out)
        self.assertFalse((self.d / 'c').exists())

    def test_index_archives_sample_cap(self):
        code, out = run(['index-archives', '--sample-per-part', '195', '--consistency-checks', '10'])
        self.assertEqual(code, 2)
        self.assertIn('capped', out)

    def test_promote_refuses_without_gate(self):
        with mock.patch.dict(sys.modules, {'nfs.evaluate.gate': None}):
            code, out = run(['promote', '--candidate-results', 'a.json', '--baseline-results', 'b.json', '--model-name', 'm'])
        self.assertEqual(code, 2)
        self.assertIn('gate', out)

    def test_promote_uses_gate_verdict(self):
        verdicts = []

        def fake_eval(cand, base, inc=None, mode='final'):
            verdicts.append((cand, base, mode))
            return types.SimpleNamespace(as_dict=lambda: dict(passed=False, reasons=['original regressed']))
        fake = types.ModuleType('nfs.evaluate.gate'); fake.evaluate_files = fake_eval
        with mock.patch.dict(sys.modules, {'nfs.evaluate.gate': fake}), mock.patch.object(cli, 'MANIFESTS', self.d):
            code, out = run(['promote', '--candidate-results', 'a.json', '--baseline-results', 'b.json', '--model-name', 'm'])
        self.assertEqual(code, 1)
        self.assertEqual(verdicts, [('a.json', 'b.json', 'final')])
        self.assertEqual(len(list((self.d / 'promotions').glob('m-*.json'))), 1)

    def test_export_refuses_synthetic_checkpoint(self):
        C.RunClock.authorize(self.d / 'r', 1, 'r')
        C.save_checkpoint(self.d / 'r' / 'x.pt', actor=F.FakePolicyNet(), provenance=dict(synthetic=True),
                          status='pretrained_unvalidated')
        code, out = run(['export', '--checkpoint', str(self.d / 'r' / 'x.pt'), '--out', str(self.d / 'm')])
        self.assertEqual(code, 2)
        self.assertFalse((self.d / 'm').exists())

    def test_train_configs_parse(self):
        import json
        from nfs.train import collect, imitation, ppo, value
        from nfs.train.rewards import RewardConfig
        files = sorted((F.ROOT / 'configs' / 'train').glob('*.json'))
        self.assertGreaterEqual(len(files), 5)
        for p in files:
            d = json.loads(p.read_text(encoding='utf-8'))
            if 'ppo' in d:
                c = cli._dc(ppo.PPOConfig, d['ppo'])
                self.assertIsInstance(c.heads, tuple)
            if 'reward' in d:
                RewardConfig.from_dict(d['reward'])
            if 'collect' in d:
                cli._dc(collect.CollectConfig, d['collect'])
            if 'imitation' in d:
                cli._dc(imitation.ImitationConfig, d['imitation'])
            if 'value' in d:
                cli._dc(value.ValueConfig, d['value'])
            lg = cli._league_from_cfg(d)
            self.assertIn('original', [o.name for o in lg.opponents], p.name)
        first = json.loads((F.ROOT / 'configs/train/first_experiment.json').read_text(encoding='utf-8'))
        self.assertLessEqual(first['max_games'], 500)
        self.assertEqual(first['ppo']['heads'], ['objective'])


class CollectTests(unittest.TestCase):
    """Job planning, content-addressed folders and ledger accounting with a mocked engine (no games run)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.cand = self.d / 'cand.wasm'; self.cand.write_bytes(b'candidate')
        o = self.d / 'orig.wasm'; o.write_bytes(b'original')
        v = self.d / 'v47.wasm'; v.write_bytes(b'v47')
        self.lg = L.League(min_reference_share=0.5, seed=2)
        self.lg.add('original', 'reference', o); self.lg.add('v47', 'historical_release', v)
        from nfs.train import collect as co
        self.co = co
        self.maps = co.resolve_maps(['00eight', '00gem-fields'])

    def tearDown(self):
        self.tmp.cleanup()

    def fake_results(self, jobs, workers):
        from nfs.engine import MatchResult
        return [MatchResult(folder=j['folder'], map=Path(j['map_path']).stem, side=j['candidate_side'], win=1.0, gems=1,
                            opponent_gems=0, faults=0, fuel_exhausted=0, opponent_fuel_exhausted=0, deaths=0,
                            collected=0, gold=0, rounds=10, outcome='teamA', engine='1.0.3') for j in jobs]

    def test_plan_and_account_once(self):
        jobs = self.co.plan_jobs(self.cand, self.lg, self.maps, ('A', 'B'), 6, self.d / 'games', iteration=1)
        self.assertEqual(len(jobs), 6)
        for j in jobs:
            m = j['meta']
            self.assertEqual(len(m['determinism_key']), 3)
            self.assertIn(m['candidate_sha256'][:10], j['job']['folder'])
            a_sha = m['determinism_key'][0]
            self.assertEqual(a_sha, m['candidate_sha256'] if j['job']['candidate_side'] == 'A' else m['opponent_sha256'])
        cfg = self.co.CollectConfig(max_games=4, workers=2)
        led = C.GamesLedger(self.d / 'run')
        with mock.patch.object(self.co.engine, 'run_jobs', side_effect=self.fake_results) as rj:
            rep = self.co.run_collection(jobs, cfg, led)
            self.assertEqual(rep['run'], 4)                       # capped by max_games
            self.assertEqual(rep['newly_accounted'], 4)
            rep2 = self.co.run_collection(jobs[:4], cfg, led)     # cached folders are never re-counted
            self.assertEqual(rep2['newly_accounted'], 0)
            self.assertEqual(len(led), 4)
            self.assertTrue(all(j['log_limit'] >= 1 << 24 for j in rj.call_args_list[0][0][0]))

    def test_folder_reuse_with_other_game_refused(self):
        jobs = self.co.plan_jobs(self.cand, self.lg, self.maps, ('A',), 1, self.d / 'games', iteration=1)
        folder = Path(jobs[0]['job']['folder']); folder.mkdir(parents=True)
        (folder / 'job.json').write_text('{"candidate_sha256": "other"}', encoding='utf-8')
        with mock.patch.object(self.co.engine, 'run_jobs', side_effect=self.fake_results):
            with self.assertRaises(self.co.CollectError):
                self.co.run_collection(jobs, self.co.CollectConfig(max_games=1), C.GamesLedger(self.d / 'run'))


class LeagueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.files = {}
        for n in ('orig', 'v47', 'proxy', 'self1', 'self2', 'self3'):
            p = d / f'{n}.wasm'; p.write_bytes(n.encode() * 10); self.files[n] = p

    def tearDown(self):
        self.tmp.cleanup()

    def league(self):
        lg = L.League(min_reference_share=0.3, max_frozen_self=2, seed=1)
        lg.add('original', 'reference', self.files['orig'], 1.0)
        lg.add('v47', 'historical_release', self.files['v47'], 1.0)
        lg.add('proxy0', 'draft_proxy', self.files['proxy'], 5.0)
        return lg

    def test_reference_share_and_proxy_label(self):
        lg = self.league()
        for _ in range(5):
            s = lg.sample(10)
            self.assertGreaterEqual(sum(o.kind == 'reference' for o in s), 3)
        p = [o for o in lg.opponents if o.kind == 'draft_proxy'][0]
        self.assertTrue(p.is_proxy)
        self.assertIn('NOT a real top-team executable', p.label)

    def test_state_roundtrip_deterministic(self):
        lg = self.league()
        lg.sample(4)
        st = lg.state_dict()
        a = [o.name for o in lg.sample(8)]
        lg2 = L.League.from_state(st)
        self.assertEqual(a, [o.name for o in lg2.sample(8)])

    def test_frozen_self_cap_and_identity(self):
        lg = self.league()
        for n in ('self1', 'self2', 'self3'):
            lg.add(n, 'frozen_self', self.files[n], 0.5)
        self.assertEqual([o.name for o in lg.opponents if o.kind == 'frozen_self'], ['self2', 'self3'])
        lg.verify()
        self.files['v47'].write_bytes(b'changed')
        with self.assertRaises(ValueError):
            lg.verify()

    def test_anti_regression_per_opponent(self):
        base = dict(original=dict(wins=10, games=12), v47=dict(wins=4, games=12), proxy0=dict(wins=9, games=12))
        cand = dict(original=dict(wins=6, games=12), v47=dict(wins=7, games=12), proxy0=dict(wins=12, games=12))
        r = L.anti_regression(cand, base, ['original', 'v47'])
        self.assertGreater(r['pooled_candidate'], r['pooled_baseline'])     # the phase-2 failure mode
        self.assertFalse(r['ok'])
        self.assertFalse(r['per_opponent']['original']['ok'])

    def test_default_league_uses_reference_builds(self):
        lg = L.default_league()
        names = {o.name: o.kind for o in lg.opponents}
        self.assertEqual(names.get('original'), 'reference')
        self.assertTrue({'v47', 'first-hour', 'v50'} <= set(names))


if __name__ == '__main__':
    unittest.main()
