"""Synthetic compact-observation parity and payload validation. No real engine capture is claimed."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

import numpy as np
from nfs.policy import observation as O

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / 'artifacts/tmp/v2_observation'


def synthetic_cases():
    rng = np.random.default_rng(20261024)
    scales = {name: np.asarray([f['scale'] for f in O.SCHEMA[name]], dtype=np.float32) for name in ('self', 'ally', 'enemy')}
    out = []
    for i in range(1000):
        self_raw = (rng.uniform(-5, 5, 40).astype(np.float32) * scales['self']).astype(np.float32)
        ally_raw = (rng.uniform(-5, 5, (5, 10)).astype(np.float32) * scales['ally']).astype(np.float32)
        enemy_raw = (rng.uniform(-5, 5, (6, 12)).astype(np.float32) * scales['enemy']).astype(np.float32)
        amask = rng.integers(0, 2, 5, dtype=np.uint8)
        emask = rng.integers(0, 2, 6, dtype=np.uint8)
        if i % 10 == 0:
            amask[:] = emask[:] = 0
            ally_raw[:] = np.nan
            enemy_raw[:] = np.inf  # masked padding does not become an input
        elif i % 10 == 1:
            amask[:] = emask[:] = 1
        elif i % 10 == 2:
            self_raw[:8] = np.asarray([0, -0., 3e38, -3e38, 1e-35, -1e-35, 1, -1], np.float32)
        elif i % 10 == 3:
            self_raw[20:24] = 0  # synthetic dead/action-unavailable self
        out.append((self_raw, ally_raw, amask, enemy_raw, emask))
    zero = np.zeros(40, np.float32), np.zeros((5, 10), np.float32), np.zeros(5, np.uint8), np.zeros((6, 12), np.float32), np.zeros(6, np.uint8)
    for location in ('self', 'ally', 'enemy'):
        for bad in (np.nan, np.inf, -np.inf):
            case = tuple(x.copy() for x in zero)
            if location == 'self': case[0][5] = bad
            elif location == 'ally': case[1][2, 4] = bad; case[2][2] = 1
            else: case[3][4, 3] = bad; case[4][4] = 1
            out.append(case)
    for location in (2, 4):
        for bad in (2, 255):
            case = tuple(x.copy() for x in zero)
            case[location][0] = bad
            out.append(case)
    return out


class PolicyObservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        compiler = shutil.which('g++') or 'C:/msys64/ucrt64/bin/g++.exe'
        if not Path(compiler).exists():
            raise unittest.SkipTest('native g++ unavailable')
        cls.exe = SCRATCH / 'observation.exe'
        cls.env = os.environ.copy()
        cls.env['PATH'] = str(Path(compiler).parent) + os.pathsep + cls.env.get('PATH', '')
        cls.env['TMP'] = cls.env['TEMP'] = str(SCRATCH)
        run = subprocess.run([compiler, '-std=c++20', '-O2', '-ffp-contract=off', '-I', str(ROOT / 'bot/src'),
                              str(ROOT / 'tests/cpp/test_policy_observation.cpp'), '-o', str(cls.exe)],
                             env=cls.env, capture_output=True, timeout=60)
        if run.returncode:
            raise AssertionError(run.stderr.decode(errors='replace'))

    def test_173_float_bit_exact_native_python_synthetic_parity(self):
        cases = synthetic_cases()
        payload = b''.join(self_raw.astype('<f4').tobytes() + ally_raw.astype('<f4').tobytes() + enemy_raw.astype('<f4').tobytes() +
                           amask.tobytes() + emask.tobytes() for self_raw, ally_raw, amask, enemy_raw, emask in cases)
        run = subprocess.run([str(self.exe)], input=payload, env=self.env, capture_output=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr.decode(errors='replace'))
        self.assertEqual(len(run.stdout), len(cases) * (1 + 4 * O.OBS_DIM))
        for i, case in enumerate(cases):
            offset = i * (1 + 4 * O.OBS_DIM)
            valid = run.stdout[offset]
            try:
                expected = O.encode(*case)
            except ValueError:
                self.assertEqual(valid, 0, f'synthetic invalid case{i}')
                continue
            self.assertEqual(valid, 1, f'synthetic valid case{i}')
            actual = np.frombuffer(run.stdout, dtype='<f4', count=O.OBS_DIM, offset=offset + 1)
            self.assertEqual(expected.dtype, np.float32)
            self.assertEqual(expected.shape, (173,))
            self.assertEqual(actual.tobytes(), expected.tobytes(), f'bit-exact mismatch in synthetic case{i}')
            self.assertTrue(np.isfinite(actual).all())
            self.assertTrue((np.abs(actual) <= 4).all())

    def test_encoded_payload_roundtrip_and_strict_rejections(self):
        raw = np.arange(40, dtype=np.float32), np.ones((5, 10), np.float32), np.asarray([1, 0, 1, 0, 0], np.uint8), np.ones((6, 12), np.float32), np.asarray([0, 1, 0, 0, 1, 0], np.uint8)
        encoded = O.encode(*raw)
        payload = encoded.astype('<f4').tobytes()
        self.assertEqual(O.encode_bytes(payload).tobytes(), payload)
        for data in (b'', payload[:-1], payload + b'\0', payload + b'\0' * 4):
            with self.assertRaises(ValueError): O.encode_bytes(data)
        invalid = []
        for index in (90, 94, 167, 172):
            for bad in (-1, .5, 2, 4):
                x = encoded.copy(); x[index] = bad; invalid.append(x)
        for index in (50, 59, 95, 106):  # masked ally1 and enemy0
            x = encoded.copy(); x[index] = .25; invalid.append(x)
        for index in (0, 40, 50, 95, 167):
            for bad in (np.nan, np.inf, -np.inf, 4.001, -4.001):
                x = encoded.copy(); x[index] = bad; invalid.append(x)
        for x in invalid:
            with self.assertRaises(ValueError): O.encode_bytes(x.astype('<f4').tobytes())

    def test_masked_raw_rows_are_zero_and_do_not_leak(self):
        self_raw = np.zeros(40, np.float32)
        a, e = np.full((5, 10), np.nan, np.float32), np.full((6, 12), np.inf, np.float32)
        x = O.encode(self_raw, a, np.zeros(5, np.uint8), e, np.zeros(6, np.uint8))
        self.assertEqual(x.tobytes(), np.zeros(173, np.float32).tobytes())
        a[:] = 1e30; e[:] = -1e30
        y = O.encode(self_raw, a, np.zeros(5, np.uint8), e, np.zeros(6, np.uint8))
        self.assertEqual(x.tobytes(), y.tobytes())

    def test_raw_shapes_match_fixed_cpp_contract(self):
        valid = [np.zeros(40, np.float32), np.zeros((5, 10), np.float32), np.zeros(5, np.uint8),
                 np.zeros((6, 12), np.float32), np.zeros(6, np.uint8)]
        invalid = {
            0: [(39,), (41,), (1, 40), (40, 1)],
            1: [(4, 10), (6, 10), (5, 9), (5, 11), (50,)],
            2: [(4,), (6,), (5, 1), (1, 5)],
            3: [(5, 12), (7, 12), (6, 11), (6, 13), (72,)],
            4: [(5,), (7,), (6, 1), (1, 6)],
        }
        for position, shapes in invalid.items():
            for shape in shapes:
                args = [x.copy() for x in valid]
                args[position] = np.zeros(shape, dtype=valid[position].dtype)
                with self.subTest(position=position, shape=shape):
                    with self.assertRaises(ValueError): O.encode(*args)

    def test_import_rejects_stored_schema_hash_tampering(self):
        # Run a copied module in a copied workspace hierarchy; do not mutate root-owned schema/module.
        isolated = SCRATCH / 'hash_validation'
        module = isolated / 'python/nfs/policy/observation.py'
        schema_path = isolated / 'schemas/policy_observation_v2.json'
        module.parent.mkdir(parents=True, exist_ok=True)
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'python/nfs/policy/observation.py', module)
        schema = json.loads((ROOT / 'schemas/policy_observation_v2.json').read_text(encoding='utf-8'))
        command = [sys.executable, '-c', 'import runpy,sys;runpy.run_path(sys.argv[1])', str(module)]
        schema_path.write_text(json.dumps(schema), encoding='utf-8')
        baseline = subprocess.run(command, cwd=str(isolated), env=self.env, capture_output=True, timeout=30)
        self.assertEqual(baseline.returncode, 0, baseline.stderr.decode(errors='replace'))
        schema['obs_schema_hash'] ^= 1
        schema_path.write_text(json.dumps(schema), encoding='utf-8')
        tampered = subprocess.run(command, cwd=str(isolated), env=self.env, capture_output=True, timeout=30)
        self.assertNotEqual(tampered.returncode, 0, 'corrupt stored schema hash was silently accepted at import')
        self.assertIn('schema', tampered.stderr.decode(errors='replace').lower())

    def test_schema_hash_dimensions_and_generator_reproducibility(self):
        schema = json.loads((ROOT / 'schemas/policy_observation_v2.json').read_text(encoding='utf-8'))
        unhashed = copy.deepcopy(schema)
        stored = unhashed.pop('obs_schema_hash')
        data = json.dumps(unhashed, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')
        h = 2166136261
        for byte in data: h = ((h ^ byte) * 16777619) & 0xFFFFFFFF
        self.assertEqual(stored, h)
        self.assertEqual(O.OBS_SCHEMA_HASH, h)
        run = subprocess.run([str(self.exe), 'info'], env=self.env, capture_output=True, timeout=30)
        self.assertEqual(run.returncode, 0)
        self.assertEqual(list(map(int, run.stdout.split())), [h, 173, 40, 5, 10, 6, 12])
        # Execute a copied generator in an isolated workspace subtree: never rewrite root-owned outputs.
        repro = SCRATCH / 'generator_repro'
        for directory in ('tools', 'schemas', 'bot/src'):
            (repro / directory).mkdir(parents=True, exist_ok=True)
        generator = repro / 'tools/gen_policy_observation.py'
        shutil.copyfile(ROOT / 'tools/gen_policy_observation.py', generator)
        output_paths = ['schemas/policy_observation_v2.json', 'bot/src/nn_policy_observation.h']
        first = None
        for _ in range(2):
            generated = subprocess.run([sys.executable, str(generator)], cwd=str(repro), env=self.env, capture_output=True, timeout=30)
            self.assertEqual(generated.returncode, 0, generated.stderr.decode(errors='replace'))
            current = {name: (repro / name).read_bytes() for name in output_paths}
            if first is not None:
                self.assertEqual(current, first, 'generator is not byte-reproducible')
            first = current
        for name, generated_bytes in first.items():
            self.assertEqual((ROOT / name).read_bytes(), generated_bytes, f'checked-in {name} differs from generator')


if __name__ == '__main__':
    unittest.main()
