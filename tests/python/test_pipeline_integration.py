"""Synthetic installation and cache-integrity integration; no games and no training."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from nfs import engine, export
from nfs import cli
from nfs.models import build_model, init_untrained, load_config
from nfs.models.config import head_action_hash
from nfs import obs, records
from nfs.data import records_dataset as rd
from nfs.registry import current_head_hashes
import numpy as np
import _fakes as F

spec = importlib.util.spec_from_file_location('nfs_install_test', engine.ROOT / 'tools/install_models.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class SyntheticPipelineIntegration(unittest.TestCase):
    def test_same_dimension_semantic_drift_changes_schema_and_is_rejected(self):
        shop = json.loads((engine.ROOT/'schemas/heads/shop.json').read_text())
        legacy = dict(shop, version=1, semantics='legacy first-purchase preview')
        self.assertNotEqual(head_action_hash(shop), head_action_hash(legacy))
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d/'schemas/heads').mkdir(parents=True)
            (d/'schemas/heads.json').write_bytes((engine.ROOT/'schemas/heads.json').read_bytes())
            spec = json.loads((engine.ROOT/'schemas/heads/move.json').read_text())
            p = d/'schemas/heads/move.json'; p.write_text(json.dumps(spec))
            with mock.patch.object(rd, 'ROOT', d):
                before = rd.action_schema_hash()
                spec['features'][0]['scale'] *= 2
                p.write_text(json.dumps(spec))
                self.assertNotEqual(rd.action_schema_hash(), before)
        src = rd.MatchSource('synthetic-schema-test', 'A', {'match': {'engineVersion': '1.0.3'}}, '')
        rec = dict(kind=1, champion=0, round=5, head=6, schema_hash=obs.OBS_SCHEMA_HASH, action_hash=0)
        with self.assertRaisesRegex(rd.DatasetError, 'action schema'):
            rd.convert_match(src, decode=lambda _: [rec])

    def test_rl_quality_rejection_precedes_any_optimizer_update(self):
        # Drive the real CLI orchestrator with synthetic collection/conversion and a forbidden-update spy.
        from nfs.train import ppo, collect
        from test_train_imitation_value import labelled_shard
        model = cli._build_model(engine.ROOT / 'configs/model/fs_v1.json')
        shard = labelled_shard(model, model.obs_dim, 2, 123, 'train', 'synthetic-')
        shard.inputs['legal'][:] = False
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            with mock.patch.object(cli, '_export_for_training', return_value=d/'synthetic.wasm'), \
                    mock.patch.object(collect, 'plan_jobs', return_value=[]), \
                    mock.patch.object(collect, 'run_collection', return_value=dict(faults=0, results=[
                        dict(folder=str(d/'game'), side='A', faults=0)])), \
                    mock.patch.object(rd.MatchSource, 'from_folder', return_value=object()), \
                    mock.patch.object(rd, 'convert_match', return_value=shard), \
                    mock.patch.object(ppo, 'ppo_update') as update:
                with self.assertRaisesRegex(RuntimeError, 'before parameter updates'):
                    cli.main(['rl', '--run-dir', str(d/'run'), '--model-config',
                              str(engine.ROOT/'configs/model/fs_v1.json'), '--i-authorize-training',
                              '--time-limit-minutes', '5'])
                update.assert_not_called()
                stop = json.loads((d/'run/stopped.json').read_text())
                self.assertIn('invalid_action_rate', stop['violations'])

    def test_value_cli_persists_synthetic_checkpoint(self):
        from nfs.train import value, checkpoint
        from test_train_imitation_value import labelled_shard
        model = cli._build_model(engine.ROOT / 'configs/model/fs_v1.json')
        shard = labelled_shard(model, model.obs_dim, 2, 321, 'train', 'synthetic-')
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            with mock.patch.object(rd.Shard, 'load', return_value=shard), \
                    mock.patch.object(value, 'train_value', return_value={'synthetic': True}) as fit:
                cli.main(['train-value', '--run-dir', str(d/'run'), '--model-config',
                          str(engine.ROOT/'configs/model/fs_v1.json'), '--train', 'synthetic-train',
                          '--validation', 'synthetic-validation', '--i-authorize-training',
                          '--time-limit-minutes', '5'])
                fit.assert_called_once()
            saved = checkpoint.load_checkpoint(d/'run/value.pt')
            self.assertTrue(saved['meta']['provenance']['synthetic'])
            self.assertEqual(saved['meta']['provenance']['stage'], 'team_value')

    def test_canonical_record_and_observation_adapters_connect(self):
        raw = obs.empty_raw(); raw.update(round=5, width=32, height=32, max_hp=100, hp=70)
        head = 6; hashes = current_head_hashes()
        rec = dict(kind='decision', schema_hash=obs.OBS_SCHEMA_HASH, round=5, champion=0, head=head,
                   K=2, F=24, teacher=0, chosen=0, mode='active', reason='ok', context=0, sampled=True,
                   logp=-0.5, prior=[0, -0.25], legal=[True, True], id=[4, 8], feat=np.zeros((2,24)),
                   action_hash=hashes['move'], call=0, net=0, logit=[0, -0.25])
        text = records.encode_line(dict(kind='turn', schema_hash=obs.OBS_SCHEMA_HASH, round=5,
                                        champion=0, raw=obs.pack(raw))) + '\n' + records.encode_line(rec)
        decode, name = rd.decoder(); encoded, dim, encname = rd.obs_encoder()
        self.assertEqual(name, 'nfs.records.decode_stdout')
        self.assertEqual(encname, 'nfs.obs.encode_bytes')
        self.assertEqual(dim, obs.OBS_DIM)
        parsed = decode(text)
        self.assertEqual(parsed[1]['mode'], 2)
        self.assertEqual(parsed[1]['reason'], 0)
        np.testing.assert_array_equal(encoded(parsed[0]['payload']), obs.encode(raw))

    def test_cli_starts_with_seeded_features_and_zero_residual(self):
        model = cli._build_model(engine.ROOT / 'configs/model/fs_v1.json')
        self.assertGreater(int(model.enc['g1_w'].count_nonzero()), 0)
        self.assertGreater(int(model.heads['objective']['wf'].count_nonzero()), 0)
        self.assertEqual(int(model.heads['objective']['w2'].count_nonzero()), 0)

    def test_unregistered_export_installs_without_mutating_registry(self):
        before = (engine.ROOT / 'models/registry.json').read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            model = init_untrained(build_model(load_config('fs_v1')), 123, zero_residual=True)
            export.export_model(model, 'synthetic_external', d / 'model', status='untrained',
                                provenance={'source': 'synthetic integration test', 'synthetic': True})
            src = engine.make_bot_dir(engine.ROOT / 'bot/src', d / 'bot') / 'src'
            result = installer.install('training', src, model=str(d / 'model'), quiet=True)
            self.assertEqual(result['models'], ['synthetic_external'])
            self.assertTrue(all(h['mode'] == 'active' for h in result['heads'].values()))
            self.assertTrue((src / 'nn_weights_synthetic_external.h').exists())
            with self.assertRaises(SystemExit):
                installer.install('release', src, model=str(d / 'model'), quiet=True)
            data = bytearray((d / 'model/weights.f32').read_bytes())
            data[-1] ^= 1
            (d / 'model/weights.f32').write_bytes(data)
            with self.assertRaisesRegex(SystemExit, 'checksum'):
                installer.install('training', src, model=str(d / 'model'), quiet=True)
        self.assertEqual(before, (engine.ROOT / 'models/registry.json').read_bytes())

    def test_match_cache_refuses_changed_inputs_and_unidentified_legacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            a, b, m = d / 'a.wasm', d / 'b.wasm', d / 'm.map26a'
            a.write_bytes(b'synthetic-a'); b.write_bytes(b'synthetic-b'); m.write_bytes(b'synthetic-map')
            folder = d / 'game'

            def fake_run(*args, **kwargs):
                (folder / 'summary.json').write_text('{}', encoding='utf-8')
                return 'synthetic'

            with mock.patch.object(engine, '_run', side_effect=fake_run) as run, \
                    mock.patch.object(engine, 'parse_summary', return_value='synthetic-result'):
                self.assertEqual(engine.run_match(a, b, m, folder), 'synthetic-result')
                self.assertEqual(engine.run_match(a, b, m, folder), 'synthetic-result')
                self.assertEqual(run.call_count, 1)
                a.write_bytes(b'different')
                with self.assertRaisesRegex(ValueError, 'identity differs'):
                    engine.run_match(a, b, m, folder)
                (folder / 'engine_identity.json').unlink()
                with self.assertRaisesRegex(ValueError, 'legacy summary'):
                    engine.run_match(a, b, m, folder)

    def test_build_time_worker_cap(self):
        real = engine.cf.ThreadPoolExecutor
        with mock.patch.object(engine.cf, 'ThreadPoolExecutor', wraps=real) as pool:
            self.assertEqual(engine.run_jobs([], 100), [])
            pool.assert_called_once_with(max_workers=4)


if __name__ == '__main__':
    unittest.main()
