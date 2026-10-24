"""Development-clone regressions: absent laptop-only evidence and immutable local reference identities."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'python'))
sys.path.insert(0, str(ROOT / 'tools'))
from nfs.evaluate import protocol as P
import verify_release


class TestPortableFrozenProtocol(unittest.TestCase):
    def test_missing_original_diagnosis_reproduces_frozen_bytes(self):
        with tempfile.TemporaryDirectory() as temp, \
                mock.patch.object(P, 'EVIDENCE', Path(temp) / 'absent-original-laptop'), \
                mock.patch.object(P, 'evidence_map_properties', side_effect=AssertionError('no original data')), \
                mock.patch.object(P, 'fuel_scenarios', side_effect=AssertionError('must not rerank incomplete cohort')):
            built, schedules = P.build()
        self.assertEqual(P._dump(built), P.PROTOCOL.read_text(encoding='utf-8'))
        for name, schedule in schedules.items():
            self.assertEqual(P._dump(schedule), (P.SCHEDULES / f'{name}.json').read_text(encoding='utf-8'))

    def test_frozen_properties_cannot_be_reused_after_partition_changes(self):
        training = P.load_schedule('map_partitions')['partitions']['training']
        with self.assertRaisesRegex(RuntimeError, 'changed training partition'):
            P.frozen_fuel_scenarios(training[:-1])

    def test_portable_fallback_rejects_tampered_schedule(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            shutil.copy2(P.PROTOCOL, temp / 'protocol.json')
            shutil.copy2(P.LOCK, temp / 'protocol.lock.json')
            shutil.copytree(P.SCHEDULES, temp / 'schedules')
            fuel = temp / 'schedules/fuel_profile.json'
            fuel.write_bytes(fuel.read_bytes() + b' ')
            with mock.patch.object(P, 'EVIDENCE', temp / 'absent-original-laptop'), \
                    mock.patch.object(P, 'PROTOCOL', temp / 'protocol.json'), \
                    mock.patch.object(P, 'LOCK', temp / 'protocol.lock.json'), \
                    mock.patch.object(P, 'SCHEDULES', temp / 'schedules'):
                with self.assertRaisesRegex(RuntimeError, 'fuel_profile does not match the lock'):
                    P.build()


class TestPortableReferenceVerification(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.builds = Path(self.temp.name)
        self.raw = b'\0asm\x01\0\0\0' + bytes([10, 1, 0])  # synthetic empty code section
        self.path = self.builds / 'original.wasm'
        self.path.write_bytes(self.raw)
        self.item = dict(wasm='Z:/absent/original-laptop/references/builds/original.wasm',
                         wasm_sha256=hashlib.sha256(self.raw).hexdigest(),
                         code_section_sha256=hashlib.sha256(b'\0').hexdigest())
        self.write_manifest()

    def tearDown(self):
        self.temp.cleanup()

    def write_manifest(self):
        (self.builds / 'manifest.json').write_text(json.dumps(dict(opponents={'original': self.item})))

    def test_local_reference_verified_without_historical_absolute_path(self):
        checks, info = verify_release.reference_checks(self.builds)
        self.assertTrue(checks[0]['passed'])
        self.assertEqual(Path(info['original']['path']), self.path.resolve())
        self.assertEqual(info['original']['wasm_sha256'], self.item['wasm_sha256'])
        self.assertEqual(info['original']['code_section_sha256'], self.item['code_section_sha256'])

    def test_missing_local_reference_reports_failure(self):
        self.path.unlink()
        checks, info = verify_release.reference_checks(self.builds)
        self.assertFalse(checks[0]['passed'])
        self.assertEqual(checks[0]['detail'], ['original'])
        self.assertIn('error', info['original'])

    def test_local_full_binary_mismatch_is_not_bypassed(self):
        self.path.write_bytes(self.raw + bytes([0, 1, 0]))  # valid extra custom section
        checks, info = verify_release.reference_checks(self.builds)
        self.assertFalse(checks[0]['passed'])
        self.assertNotEqual(info['original']['wasm_sha256'], self.item['wasm_sha256'])

    def test_local_code_identity_must_match_even_if_full_hash_matches(self):
        self.item['code_section_sha256'] = '0' * 64
        self.write_manifest()
        checks, _ = verify_release.reference_checks(self.builds)
        self.assertFalse(checks[0]['passed'])

    def test_malformed_local_wasm_reports_failure(self):
        self.path.write_bytes(b'\0asm\x01\0\0\0\x0a\x80')
        checks, info = verify_release.reference_checks(self.builds)
        self.assertFalse(checks[0]['passed'])
        self.assertIn('error', info['original'])


if __name__ == '__main__':
    unittest.main()
