"""verify_release on synthetic good/bad ZIPs (labelled synthetic; no rebuild), config/registry/flag audits."""
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'python'))
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nfs.evaluate import release as R  # noqa: E402
import verify_release  # noqa: E402
from test_eval_wasm import synthetic  # noqa: E402

HEADS = 'draft_pick, strategy, objective, role, bank, shop, move, combat, engage, ward, belief, value, ts_leaf, count'


def config(profile='release', training='false', telemetry='false', selftest='false', credit='false', strip=0,
           nn_training=0, modes='{}', any_head='false'):
    return f'''#pragma once
#define NN_ANY_HEAD 0
#define NN_STRIP_LAB {strip}
#define NN_TRAINING {nn_training}
#define NN_TELEMETRY 0
namespace nncfg {{
enum class Mode : int {{ off = 0, shadow = 1, active = 2 }};
enum class H : int {{ {HEADS} }};
inline constexpr Mode kMode[static_cast<int>(H::count)] = {modes};
inline constexpr bool kAnyHead = {any_head};
inline constexpr bool kTraining = {training};
inline constexpr bool kTelemetry = {telemetry};
inline constexpr bool kFuelCredit = {credit};
inline constexpr bool kSelfTest = {selftest};
inline constexpr bool kStripLab = {'true' if strip else 'false'};
inline constexpr unsigned kSeed = 0;
inline constexpr const char* kProfile = "{profile}";
}}
'''


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.src = self.d / 'bot' / 'src'
        self.src.mkdir(parents=True)
        (self.src / 'main.cpp').write_bytes(b'int main(){}\n')
        (self.src / 'bot.h').write_bytes(b'#pragma once\n')
        (self.src / 'nn_config.h').write_text(config(), encoding='utf-8', newline='\n')
        self.wasm = self.d / 'bot.wasm'
        self.wasm.write_bytes(synthetic(exports=(('memory', 2), ('_start', 0)), data=(b'abcd', b'efgh')))
        self.models = self.d / 'models'
        self.models.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def make_zip(self, members: dict[str, bytes] | None = None, name='bot.zip') -> Path:
        p = self.d / name
        if members is None:
            members = {f'src/{f.name}': f.read_bytes() for f in sorted(self.src.iterdir())}
        with zipfile.ZipFile(p, 'w', zipfile.ZIP_DEFLATED) as z:
            for n, b in members.items():
                z.writestr(n, b)
        return p

    def failed(self, checks):
        return {c['name'] for c in checks if not c['passed']}

    def verify(self, zp, wasm=None):
        return verify_release.verify(zp, wasm or self.wasm, self.src, self.models, rebuild=False,
                                     scan_paths=[self.d / 'scripts'])


class TestZip(Fixture):
    def test_good_zip_passes_everything_but_skipped_rebuild(self):
        doc = self.verify(self.make_zip())
        self.assertEqual(self.failed(doc['checks']), {'independent_rebuild_matches'})  # rebuild skipped in unit test

    def test_path_traversal(self):
        m = {f'src/{f.name}': f.read_bytes() for f in self.src.iterdir()}
        m['src/../evil.cpp'] = b'x'
        f = self.failed(R.check_zip(self.make_zip(m), self.src))
        self.assertIn('zip_no_path_traversal', f)
        self.assertIn('zip_members_flat_src_cpp_h', f)
        with self.assertRaises(ValueError):
            R.safe_extract(self.make_zip(m, 'b.zip'), self.d / 'out')

    def test_nested_and_foreign_members(self):
        # (a raw backslash member is normalised to '/' by Python's zipfile on Windows, so it is not built here;
        # MEMBER_RE and check 'zip_no_path_traversal' reject a raw backslash name)
        for extra in ('src/sub/x.cpp', 'src/notes.txt', 'main.cpp', '/src/a.cpp', 'src/x.hpp'):
            m = {f'src/{f.name}': f.read_bytes() for f in self.src.iterdir()}
            m[extra] = b'x'
            self.assertIn('zip_members_flat_src_cpp_h', self.failed(R.check_zip(self.make_zip(m), self.src)), extra)

    def test_content_mismatch_and_missing_file(self):
        m = {f'src/{f.name}': f.read_bytes() for f in self.src.iterdir()}
        m['src/main.cpp'] = b'int main(){return 1;}\n'
        self.assertIn('zip_bytes_equal_source_tree', self.failed(R.check_zip(self.make_zip(m), self.src)))
        del m['src/main.cpp']
        f = self.failed(R.check_zip(self.make_zip(m, 'c.zip'), self.src))
        self.assertIn('zip_members_equal_source_files', f)

    def test_source_tree_with_foreign_file(self):
        (self.src / 'README.txt').write_text('x')
        self.assertIn('source_tree_flat_cpp_h_only', self.failed(R.check_zip(self.make_zip(), self.src)))

    def test_duplicates(self):
        p = self.d / 'dup.zip'
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with zipfile.ZipFile(p, 'w') as z:
                for f in self.src.iterdir():
                    z.writestr(f'src/{f.name}', f.read_bytes())
                z.writestr('src/main.cpp', b'int main(){}\n')
        self.assertIn('zip_no_duplicates', self.failed(R.check_zip(p, self.src)))


class TestConfigAndWasm(Fixture):
    def test_non_release_profile_fails(self):
        (self.src / 'nn_config.h').write_text(config(profile='teacher_exact'), encoding='utf-8', newline='\n')
        self.assertIn('config_profile_release', self.failed(self.verify(self.make_zip())['checks']))

    def test_training_and_telemetry_flags_fail(self):
        for kw, chk in ((dict(training='true'), 'config_kTraining_false'), (dict(telemetry='true'), 'config_kTelemetry_false'),
                        (dict(selftest='true'), 'config_kSelfTest_false'), (dict(nn_training=1), 'config_NN_TRAINING_0'),
                        (dict(credit='true'), 'config_kFuelCredit_false')):
            cfg = R.parse_nn_config(config(**kw))
            self.assertIn(chk, self.failed(R.check_config(cfg)), kw)

    def test_shadow_head_in_release_fails(self):
        cfg = R.parse_nn_config(config(modes='{ Mode::off, Mode::shadow }', any_head='true'))
        self.assertEqual(cfg['head_modes']['strategy'], 'shadow')
        self.assertEqual(cfg['head_modes']['ts_leaf'], 'off')
        self.assertIn('config_no_shadow_heads_in_release', self.failed(R.check_config(cfg)))

    def test_current_lead_stub_parses(self):
        p = ROOT / 'bot/src/nn_config.h'
        if p.exists():
            cfg = R.parse_nn_config(p.read_text(encoding='utf-8'))
            self.assertTrue(cfg['modes_parsed'])
            self.assertEqual(len(cfg['heads']), 13)

    def test_nft1_string_in_wasm_fails(self):
        bad = self.d / 'bad.wasm'
        bad.write_bytes(synthetic(exports=(('memory', 2),), data=(b'NFT1 %d', b'x')))
        self.assertIn('wasm_no_NFT1_string', self.failed(self.verify(self.make_zip(), bad)['checks']))

    def test_lab_exports_fail_only_when_strip_selected(self):
        lab = self.d / 'lab.wasm'
        lab.write_bytes(synthetic(exports=(('memory', 2), ('lab_cn_log', 0)), data=(b'abcd', b'efgh')))
        self.assertNotIn('wasm_no_lab_exports', self.failed(self.verify(self.make_zip(), lab)['checks']))
        (self.src / 'nn_config.h').write_text(config(strip=1), encoding='utf-8', newline='\n')
        self.assertIn('wasm_no_lab_exports', self.failed(self.verify(self.make_zip(name='s.zip'), lab)['checks']))


class TestRegistryAndScripts(Fixture):
    def write_model(self, name, head, status, active=False):
        (self.models / name).mkdir()
        (self.models / name / 'manifest.json').write_text(json.dumps(dict(name=name, head=head, status=status,
                                                                          checksum='0x1')))
        reg = self.models / 'registry.json'
        items = json.loads(reg.read_text())['models'] if reg.exists() else []
        items.append(dict(name=name, head=head, status=status, active=active))
        reg.write_text(json.dumps(dict(models=items)))

    def test_untrained_model_active_fails(self):
        self.write_model('strategy_v1', 'strategy', 'untrained', active=True)
        f = self.failed(R.check_registry(self.models, {'strategy': 'off'})[0])
        self.assertIn('registry_strategy_v1_not_active_while_untrained', f)

    def test_active_head_needs_validated_model(self):
        self.write_model('move_v1', 'move', 'teacher_initialized')
        f = self.failed(R.check_registry(self.models, {'move': 'active'})[0])
        self.assertIn('registry_active_head_move_has_validated_model', f)
        self.assertIn('registry_move_v1_head_move_active_with_teacher_initialized_model', f)

    def test_inactive_untrained_and_validated_active_pass(self):
        self.write_model('draft_net_original', 'draft_pick', 'trained')
        self.write_model('bank_v1', 'bank', 'untrained')
        self.write_model('move_v2', 'move', 'validated', active=True)
        checks, info = R.check_registry(self.models, {'move': 'active', 'bank': 'off'})
        self.assertFalse(self.failed(checks))
        self.assertEqual(len(info['models']), 3)
        self.assertTrue(all(m['files_sha256'] for m in info['models']))

    def test_agent_b_layout_selection_and_checksum(self):
        import numpy as np
        w = np.arange(6, dtype='<f4')
        for name, status in (('fs_dev', 'untrained'), ('fs_ok', 'validated')):
            (self.models / name).mkdir()
            (self.models / name / 'weights.f32').write_bytes(w.tobytes())
            (self.models / name / 'manifest.json').write_text(json.dumps(dict(
                name=name, head='all', status=status, checksum=f'0x{R.fnv1a64(w.tobytes()):016x}')))
        reg = dict(models={'fs_dev': dict(path='models/fs_dev', status='untrained'),
                           'fs_ok': dict(path='models/fs_ok', status='validated')},
                   release_selection={'bank': 'fs_dev'})
        (self.models / 'registry.json').write_text(json.dumps(reg))
        cfg = R.parse_nn_config(config(modes='{ Mode::off,  // draft_pick\n Mode::active, // strategy (fs_dev)\n }',
                                       any_head='true'))
        self.assertEqual(cfg['head_models'], {'strategy': 'fs_dev'})
        self.assertEqual(cfg['head_modes']['strategy'], 'active')
        checks, info = R.check_registry(self.models, cfg['head_modes'], cfg['head_models'])
        f = self.failed(checks)
        self.assertIn('release_selection_bank_fs_dev_validated', f)
        self.assertIn('registry_active_head_strategy_has_validated_model', f)
        self.assertNotIn('registry_fs_dev_weights_checksum', f)
        # corrupt the weights -> independent checksum catches it
        (self.models / 'fs_ok' / 'weights.f32').write_bytes(np.ones(6, dtype='<f4').tobytes())
        self.assertIn('registry_fs_ok_weights_checksum', self.failed(R.check_registry(self.models, {})[0]))

    def test_fnv1a64_known_vectors(self):
        self.assertEqual(R.fnv1a64(b''), 0xCBF29CE484222325)
        self.assertEqual(R.fnv1a64(b'a'), 0xAF63DC4C8601EC8C)

    def test_real_workspace_registry_audit(self):
        if not (ROOT / 'models/registry.json').exists():
            self.skipTest('no registry yet')
        checks, info = R.check_registry(ROOT / 'models', {})
        self.assertFalse(self.failed(checks), checks)

    def test_fuel_flag_use_detected_prose_tolerated(self):
        s = self.d / 'scripts'
        s.mkdir()
        flag = '--' + 'fuel'
        (s / 'ok.py').write_text(f'# never pass {flag} to the engine\n')
        self.assertFalse(self.failed(R.scan_for_fuel_flag([s])))
        (s / 'bad.py').write_text(f"args = ['run', '{flag}', '200000']\n")
        self.assertIn('no_fuel_override_in_scripts', self.failed(R.scan_for_fuel_flag([s])))
        (s / 'bad.py').write_text(f'cmd = "cambc run a b {flag}=200000"\n')
        self.assertIn('no_fuel_override_in_scripts', self.failed(R.scan_for_fuel_flag([s])))

    def test_workspace_eval_scripts_clean(self):
        self.assertFalse(self.failed(R.scan_for_fuel_flag([ROOT / 'tools', ROOT / 'python'])))


if __name__ == '__main__':
    unittest.main()
