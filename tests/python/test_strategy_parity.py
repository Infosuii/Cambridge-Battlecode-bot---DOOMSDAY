"""Synthetic C++/Python parity, masks, ordering and bounds for every D builder (no training)."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import unittest

import numpy as np
from nfs.heads import strategy as S
from nfs.models.rt import act_np

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / 'artifacts/tmp/D2'


class StrategyParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        compiler = shutil.which('g++') or 'C:/msys64/ucrt64/bin/g++.exe'
        if not Path(compiler).exists():
            raise unittest.SkipTest('native g++ unavailable')
        cls.exe = SCRATCH / 'strategy_parity.exe'
        env = os.environ.copy()
        env['PATH'] = str(Path(compiler).parent) + os.pathsep + env.get('PATH', '')
        env['TMP'] = env['TEMP'] = str(SCRATCH)
        result = subprocess.run([compiler, '-std=c++20', '-O2', '-ffp-contract=off', '-I', str(ROOT / 'bot/src'),
                                 str(ROOT / 'tests/cpp/test_strategy_parity.cpp'), '-o', str(cls.exe)],
                                env=env, capture_output=True, timeout=60)
        if result.returncode:
            raise AssertionError(result.stderr.decode(errors='replace'))
        cls.env = env

    def compare(self, cases):
        packed = []
        for mode, inputs, expected in cases:
            raw = np.zeros(129, dtype='<f4')
            raw[0] = mode
            raw[1:1 + len(inputs)] = inputs
            packed.append(raw.tobytes())
        result = subprocess.run([str(self.exe)], input=b''.join(packed), capture_output=True, env=self.env, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        data, offset = result.stdout, 0
        for mode, inputs, expected in cases:
            K, F = struct.unpack_from('<II', data, offset)
            offset += 8
            self.assertEqual((K, F), (expected['K'], expected['F']))
            for key, dtype, count in [('legal', 'u1', K), ('id', '<u4', K), ('prior', '<f4', K), ('feat', '<f4', K * F)]:
                got = np.frombuffer(data, dtype=dtype, count=count, offset=offset)
                offset += got.nbytes
                want = np.asarray(expected[key]).reshape(-1)
                self.assertEqual(got.tobytes(), want.tobytes(), (mode, key, got, want))
        self.assertEqual(offset, len(data))

    def test_varied_bit_exact_synthetic_candidates(self):
        rng = np.random.default_rng(20261024)
        cases = []
        for i in range(200):
            common = np.asarray([rng.uniform(0, 2200), rng.uniform(0, 2000), rng.uniform(1, 2500), rng.uniform(0, 500),
                                 rng.uniform(0, 6000), rng.uniform(-2000, 2000), i % 6, 3 + i % 4, i % 2,
                                 i % 7, i % 9, i % 5, rng.uniform(-1, 1)], dtype=np.float32)
            legal = rng.integers(0, 2, 6)
            cases.append((0, np.r_[common, legal], S.build_strategy(common, legal)))
            teacher, target = i % 5, bool(i % 2)
            cases.append((1, np.r_[common, teacher, target], S.build_role(common, teacher, target)))
            K = i % 9
            rows = np.zeros((K, 13), dtype=np.float32)
            if K:
                rows[:, :2] = np.c_[np.arange(K) + 100, rng.integers(1, 7, K)]
                rows[:, 2:12] = rng.uniform(-100, 5000, (K, 10))
                rows[:, 12] = rng.integers(0, 2, K)
            cases.append((2, np.r_[common, K, rows.ravel()], S.build_objective(common, rows)))
            teacher, taken = i % 12, int(rng.integers(0, 4096))
            if i % 10:
                taken &= ~(1 << teacher)
            mapf, scores = rng.uniform(0, 8, 6).astype(np.float32), rng.uniform(-100, 100, 12).astype(np.float32)
            tail = [i % 6, (i + 1) % 6, i / 200, i % 2]
            cases.append((3, np.r_[teacher, mapf, scores, taken, tail], S.build_draft(mapf, scores, taken, teacher, *tail)))
        self.compare(cases)

    def test_schema_fields_and_widths(self):
        for name, K in [('draft_pick', 12), ('strategy', 6), ('objective', 8), ('role', 5)]:
            schema = json.loads((ROOT / 'schemas/heads' / f'{name}.json').read_text())
            self.assertEqual(schema['F'], 24)
            self.assertEqual(len(schema['features']), 24)
            self.assertEqual(schema['K_max'], K)
            self.assertEqual(schema['contexts'], ['default'])
            self.assertEqual(schema['status'], 'untrained')
        value = json.loads((ROOT / 'schemas/heads/value.json').read_text())
        self.assertEqual([x['name'] for x in value['outputs']], ['win_logit', 'margin', 'carry_risk'])
        self.assertEqual(value['outputs'][1]['unit'], 'submitted_gems_per_1000')

    def test_bounded_value_signal_bit_exact(self):
        rng = np.random.default_rng(11)
        cases = []
        for _ in range(200):
            values = rng.uniform(-4, 4, 3).astype(np.float32)
            signal = S.bounded_values(values, act_np)
            self.assertLessEqual(abs(signal), 1)
            expected = dict(K=1, F=1, id=np.asarray([0], dtype=np.uint32), legal=np.asarray([1], dtype=np.uint8),
                            prior=np.asarray([0], dtype=np.float32), feat=np.asarray([signal], dtype=np.float32))
            cases.append((4, values, expected))
        self.compare(cases)

    def test_teacher_masks_ties_empty_and_ordering(self):
        c = [100, 50, 100, 20, 100, -5, 0, 4, 1, 2, 1, 0, 0]
        strategy = S.build_strategy(c, [0] * 6)
        self.assertEqual(strategy['legal'].tolist(), [1, 0, 0, 0, 0, 0])
        role = S.build_role(c, 3, True)
        self.assertEqual(role['id'].tolist(), [3, 0, 1, 2, 4])
        for d in [strategy, role, S.build_draft([0] * 6, [0] * 12, 0, 7, 0, 0, .5, True)]:
            self.assertEqual(S.teacher_label(d), 0)
            self.assertEqual(np.argmax(np.where(d['legal'], d['prior'], -np.inf)), 0)
            self.assertTrue(np.isfinite(d['feat']).all())
        self.assertEqual(S.build_draft([0] * 6, [0] * 12, 1 << 2, 2, 0, 0, 0, False)['K'], 0)
        with self.assertRaises(ValueError):
            S.teacher_label(S.build_objective(c, []))

    def test_objective_alternative_permutation_and_illegal_mask(self):
        c = [100, 50, 100, 20, 100, -5, 0, 4, 1, 2, 1, 0, .2]
        rows = np.asarray([[20, 1, 30, 20, 1, 50, 30, 100, 0, 10, 5, 0, 1],
                           [21, 2, 60, 70, 2, 60, 60, 200, 0, 20, 50, 1, 0],
                           [22, 1, 30, 50, .5, 60, 30, 50, 10, 30, 20, 0, 1]], dtype=np.float32)
        a, b = S.build_objective(c, rows), S.build_objective(c, rows[[0, 2, 1]])
        self.assertEqual(a['legal'].tolist(), [1, 0, 1])
        np.testing.assert_array_equal(a['feat'][[0, 2, 1]], b['feat'])
        np.testing.assert_array_equal(a['prior'][[0, 2, 1]], b['prior'])
        np.testing.assert_array_equal(a['id'][[0, 2, 1]], b['id'])


if __name__ == '__main__':
    unittest.main()
