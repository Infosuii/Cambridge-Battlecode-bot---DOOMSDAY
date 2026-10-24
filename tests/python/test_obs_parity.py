"""C++ (bot/src/nn_obs.cpp, compiled natively) vs Python (nfs.obs) encoder parity, bit-exact (agent C).

Synthetic RawTurns only (labelled synthetic): plausible states on all three symmetries, both teams, zero and maximum
entities, dead self, and hostile byte patterns full of NaN/Inf/extremes. Real-engine fixtures are checked in
test_obs_fixtures.py.
"""
from __future__ import annotations

import random
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_obs_synth as synth  # noqa: E402
from nfs import obs, schema_gen as S  # noqa: E402


def _cases() -> list[bytes]:
    rng = random.Random(20261024)
    out = []
    for i in range(1500):
        r = synth.plausible(rng, sym=i % 3, abs_team=i % 2)
        if i % 10 == 0:  # zero entities
            for a in r['ally']:
                a['present'] = 0
            for e in r['enemy']:
                e['present'] = 0
        if i % 10 == 1:  # max entities, all visible
            for a in r['ally']:
                a.update(present=1, visible=1, known=1)
            for e in r['enemy']:
                e.update(present=1, visible=1, known=1)
        if i % 10 == 2:  # dead self
            r.update(alive=0, hp=0.0)
        if i % 10 == 3:  # extreme but finite values
            r.update(gems=2 ** 31 - 1, gold=-2 ** 31, max_hp=3.4e38, hp=-3.4e38, pos_x=2 ** 31 - 1, width=1, height=0)
        out.append(obs.pack(r))
    out += [synth.hostile_bytes(rng) for _ in range(1500)]
    return out


class TestObsParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe = synth.native_harness()

    def setUp(self):
        if self.exe is None:
            self.skipTest('no native g++ available')

    def test_native_info_matches_schema(self):
        out = synth.run_native(self.exe, 'info')
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        import json
        info = json.loads(out.stdout)
        self.assertEqual(info['obs_dim'], S.OBS_DIM)
        self.assertEqual(info['raw_size'], S.RAW_TURN_SIZE)
        self.assertEqual(info['hash'], S.OBS_SCHEMA_HASH)

    def test_native_selftest(self):
        out = synth.run_native(self.exe, 'selftest')
        self.assertEqual(out.returncode, 0, out.stdout[-3000:])
        self.assertIn('0 failures', out.stdout)

    def test_bit_exact_parity(self):
        cases = _cases()
        with tempfile.TemporaryDirectory() as td:
            fin, fout = Path(td) / 'in.bin', Path(td) / 'out.bin'
            fin.write_bytes(b''.join(cases))
            res = synth.run_native(self.exe, 'encode', str(fin), str(fout))
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            cpp = np.frombuffer(fout.read_bytes(), dtype='<f4').reshape(len(cases), S.OBS_DIM)
        mism = 0
        first = None
        for i, raw in enumerate(cases):
            py = obs.encode(raw)
            if py.tobytes() != cpp[i].tobytes():
                mism += 1
                if first is None:
                    bad = np.nonzero(py.view(np.uint32) != cpp[i].view(np.uint32))[0]
                    names = obs.feature_names()
                    first = (i, [(int(k), names[k], float(py[k]), float(cpp[i][k])) for k in bad[:6]])
            self.assertTrue(np.all(np.isfinite(py)))
        self.assertEqual(mism, 0, f'{mism}/{len(cases)} mismatching cases; first {first}')
        self.assertTrue(np.all(np.isfinite(cpp)))


if __name__ == '__main__':
    unittest.main()
