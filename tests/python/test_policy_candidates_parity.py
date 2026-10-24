"""Synthetic direct-policy candidate checks. No match data, model fitting or engine games."""
from __future__ import annotations

import copy
import os
from pathlib import Path
import shutil
import struct
import subprocess
import unittest

import numpy as np
from nfs.policy import candidates as C

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / 'artifacts/tmp/v2_candidates'


class PolicyCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        compiler = shutil.which('g++') or 'C:/msys64/ucrt64/bin/g++.exe'
        if not Path(compiler).exists():
            raise unittest.SkipTest('native g++ unavailable')
        cls.exe = SCRATCH / 'candidates.exe'
        cls.env = os.environ.copy()
        cls.env['PATH'] = str(Path(compiler).parent) + os.pathsep + cls.env.get('PATH', '')
        cls.env['TMP'] = cls.env['TEMP'] = str(SCRATCH)
        run = subprocess.run([compiler, '-std=c++20', '-O2', '-ffp-contract=off', '-I', str(ROOT / 'bot/src'),
                              str(ROOT / 'tests/cpp/test_policy_candidates_native.cpp'), str(ROOT / 'bot/src/nn_policy_candidates.cpp'),
                              '-o', str(cls.exe)], env=cls.env, capture_output=True, timeout=60)
        if run.returncode:
            raise AssertionError(run.stderr.decode(errors='replace'))

    def compare(self, cases):
        chunks = []
        for head, rows, context, teacher in cases:
            chunks.append(struct.pack('<iiiq', head, len(rows), context, teacher))
            for row in rows:
                chunks.append(struct.pack('<IB12f', row.id, int(row.legal), *row.raw))
        run = subprocess.run([str(self.exe)], input=b''.join(chunks), env=self.env, capture_output=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr.decode(errors='replace'))
        buf, offset = run.stdout, 0
        for head, rows, context, teacher in cases:
            error, d = C.try_build(head, rows, context)
            got_error, K, F, label, tie = struct.unpack_from('<iiiii', buf, offset)
            offset += 20
            self.assertEqual((got_error, K, F), (int(error), d.K, C.F))
            self.assertEqual(label, C.teacher_index(d, teacher))
            self.assertEqual(tie, next((k for k, legal in enumerate(d.legal) if legal), -1))
            for expected, dtype, count in [(d.id, '<u4', K), (d.legal, 'u1', K), (d.feat, '<f4', K * F)]:
                actual = np.frombuffer(buf, dtype=dtype, count=count, offset=offset)
                offset += actual.nbytes
                self.assertEqual(actual.tobytes(), expected.reshape(-1).tobytes(), (head, error, dtype, actual, expected))
        self.assertEqual(offset, len(buf))

    def test_all_heads_diverse_bit_exact_synthetic_parity(self):
        rng = np.random.default_rng(20261024)
        cases = []
        for head in range(1, 9):
            for case in range(180):
                K = 1 + case % 16
                ids = rng.choice(100000, K, replace=False).astype(int)
                legal = rng.integers(0, 2, K)
                legal[-1] = 1  # candidate0 need not be legal or a teacher
                raw = rng.uniform(-10000, 10000, (K, 12)).astype(np.float32)
                if case % 10 == 0:
                    raw[0] = np.asarray([0, -0., 1, -1, 1e-30, -1e-30, 3e38, -3e38, .5, -.5, 2, -2], dtype=np.float32)
                rows = [C.Candidate(int(ids[k]), int(legal[k]), raw[k]) for k in range(K)]
                teacher = int(ids[case % K]) if case % 3 else -1
                cases.append((head, rows, case % 4, teacher))
        self.compare(cases)

    def test_error_cases_have_no_implicit_teacher_choice(self):
        row = C.Candidate(9, 1, [0.] * 12)
        illegal = C.Candidate(8, 0, [0.] * 12)
        cases = [(0, [row], 0, -1), (12, [row], 0, -1), (1, [], 0, -1), (1, [row] * 17, 0, -1),
                 (1, [row, row], 0, -1), (1, [illegal], 0, -1), (1, [row], 4, -1),
                 (1, [C.Candidate(9, 2, [0.] * 12)], 0, -1)]
        for bad in (float('nan'), float('inf'), -float('inf')):
            for mask in (0, 1):
                raw = [0.] * 12
                raw[4] = bad
                cases.append((1, [row, C.Candidate(10, mask, raw)], 0, -1))
        self.compare(cases)
        for head, rows, context, _ in cases:
            with self.assertRaises(C.CandidateBuildError):
                C.build(head, rows, context)

    def test_permutation_consistency_and_teacher_is_only_annotation(self):
        rows = [C.Candidate(91, 1, [3.] * 12), C.Candidate(2, 0, [1.] * 12), C.Candidate(30, 1, [2.] * 12)]
        for head in C.HEAD_NAMES:
            a, b = C.build(head, rows), C.build(head, rows[::-1])
            self.assertEqual(a.id.tolist(), [2, 30, 91])
            self.assertEqual(a.legal.tolist(), [0, 1, 1])
            self.assertEqual(a.feat.tobytes(), b.feat.tobytes())
            before = a.feat.tobytes(), a.id.tobytes(), a.legal.tobytes()
            self.assertEqual(C.teacher_index(a), -1)
            self.assertEqual(C.teacher_index(a, 999), -1)
            self.assertEqual(C.teacher_index(a, 2), -1)
            self.assertEqual(C.teacher_index(a, 91), 2)
            self.assertEqual(before, (a.feat.tobytes(), a.id.tobytes(), a.legal.tobytes()))

    def test_semantic_hashes_and_native_constants(self):
        run = subprocess.run([str(self.exe), 'info'], env=self.env, capture_output=True, timeout=30)
        self.assertEqual(run.returncode, 0)
        values = list(map(int, run.stdout.split()))
        self.assertEqual(values[0], C.ACTION_SCHEMA_HASH)
        self.assertEqual(values[1:], [C.ACTION_HASH_BY_ID.get(i, 0) for i in range(13)])
        self.assertEqual(C.SCHEMA['action_schema_hash'], C.schema_hash())
        for name in C.HEAD_NAMES:
            head = C.head_spec(name)
            self.assertEqual(head['action_hash'], C.head_action_hash(name))
            head['features'][0]['description'] += ' changed meaning'
            self.assertNotEqual(head['action_hash'], C.head_action_hash(head))
            self.assertEqual(len(head['features']), 12)
            self.assertFalse(any('teacher' in f['name'] or 'prior' in f['name'] for f in head['features']))
        changed = copy.deepcopy(C.SCHEMA)
        changed['interpretation_version'] = 1
        self.assertNotEqual(C.ACTION_SCHEMA_HASH, C.schema_hash(changed))

    def test_composite_ids_are_injective_and_reject_overflow(self):
        moves = [C.move_id(kind, x, y) for kind in range(4) for x in (0, 1, 100, 32767) for y in (0, 1, 100, 32767)]
        attacks = [C.combat_id(kind, h) for kind in range(4) for h in (0, 1, 100, 0x3FFFFFFF)]
        self.assertEqual(len(set(moves)), 64)
        self.assertEqual(len(set(attacks)), 16)
        native = subprocess.run([str(self.exe), 'ids'], env=self.env, capture_output=True, timeout=30)
        self.assertEqual(native.returncode, 0, native.stderr.decode(errors='replace'))
        self.assertEqual(np.frombuffer(native.stdout, dtype='<u4').tolist(), moves + attacks)
        self.assertEqual(C.move_id(3, 32767, 32767), 0xFFFFFFFF)
        self.assertEqual(C.combat_id(3, 0x3FFFFFFF), 0xFFFFFFFF)
        for args in [(4, 0, 0), (0, -1, 0), (0, 0, 32768)]:
            with self.assertRaises(ValueError): C.move_id(*args)
        for args in [(4, 0), (0, -1), (0, 0x40000000)]:
            with self.assertRaises(ValueError): C.combat_id(*args)
        for bad in (-1, 0x100000000):
            with self.assertRaises(ValueError): C.build('strategy', [C.Candidate(bad, 1, [0] * 12)])


if __name__ == '__main__':
    unittest.main()
