"""Encoder property tests in Python (agent C): RawTurn struct round trip and layout, padding/permutation invariance,
empty and full rows, dead self, NaN/Inf guards, clipping. Synthetic data only."""
from __future__ import annotations

import copy
import math
import random
import struct
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_obs_synth as synth  # noqa: E402
from nfs import obs, schema_gen as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


class TestRawTurnStruct(unittest.TestCase):
    def test_size_and_offsets(self):
        self.assertEqual(obs._TURN.size, S.RAW_TURN_SIZE)
        # Offsets are contiguous 4-byte fields; row structs nest at their declared offsets.
        sizes = {'objective': S.RAW_OBJ_SIZE, 'ally': S.RAW_ALLY_SIZE, 'enemy': S.RAW_ENEMY_SIZE}
        for fields, total in ((S.RAW_OBJ_FIELDS, S.RAW_OBJ_SIZE), (S.RAW_ALLY_FIELDS, S.RAW_ALLY_SIZE),
                              (S.RAW_ENEMY_FIELDS, S.RAW_ENEMY_SIZE), (S.RAW_TURN_FIELDS, S.RAW_TURN_SIZE)):
            off = 0
            for name, code, count, o in fields:
                self.assertEqual(o, off, name)
                off += (sizes[code] if code in sizes else 4) * count
            self.assertEqual(off, total)

    def test_offsets_match_cpp_static_asserts(self):
        hdr = (ROOT / 'bot/src/nn_schema.h').read_text(encoding='utf-8')
        for name, code, count, off in S.RAW_TURN_FIELDS:
            self.assertIn(f'offsetof(T, {name}) == {off},', hdr)
        for name, code, count, off in S.RAW_ALLY_FIELDS:
            self.assertIn(f'offsetof(A, {name}) == {off},', hdr)
        nn_obs = (ROOT / 'bot/src/nn_obs.h').read_text(encoding='utf-8')
        self.assertIn('NNOBS_RAW_LAYOUT_CHECK(RawTurn, ObjRaw, AllyRaw, EnemyRaw)', nn_obs)

    def test_round_trip(self):
        rng = random.Random(11)
        for _ in range(200):
            raw = synth.hostile_bytes(rng)
            d = obs.unpack(raw)
            back = obs.pack(d)
            # NaN payloads may be canonicalised by the float round trip; compare as words with NaN folded.
            w1 = struct.unpack(f'<{S.RAW_TURN_SIZE // 4}I', raw)
            w2 = struct.unpack(f'<{S.RAW_TURN_SIZE // 4}I', back)
            for a, b in zip(w1, w2):
                if a != b:
                    fa, fb = struct.unpack('<f', struct.pack('<I', a))[0], struct.unpack('<f', struct.pack('<I', b))[0]
                    self.assertTrue(math.isnan(fa) and math.isnan(fb))
            self.assertEqual(obs.encode(raw).tobytes(), obs.encode(back).tobytes())
        r = synth.plausible(rng)
        self.assertEqual(obs.unpack(obs.pack(r)), r)
        self.assertTrue(obs.check_header(r))

    def test_wrong_size_rejected(self):
        with self.assertRaises(ValueError):
            obs.unpack(b'\0' * (S.RAW_TURN_SIZE - 4))


class TestEncodeProperties(unittest.TestCase):
    def test_padding_invariance_and_masks(self):
        rng = random.Random(12)
        for i in range(300):
            r = synth.plausible(rng)
            x = obs.encode(r)
            g = copy.deepcopy(r)
            for a in g['ally']:
                if not a['present']:
                    a.update(x=rng.getrandbits(31), hp=math.nan, known=1, visible=1, type=3, claim_code=5)
            for e in g['enemy']:
                if not e['present']:
                    e.update(max_hp=math.inf, known=1, visible=1, gems=99)
            self.assertEqual(x.tobytes(), obs.encode(g).tobytes())
            parts = obs.split(x)
            na = sum(a['present'] != 0 for a in r['ally'])
            ne = sum(e['present'] != 0 for e in r['enemy'])
            self.assertEqual(parts['ally_mask'].tolist(), [1.0] * na + [0.0] * (S.ALLY_ROWS - na))
            self.assertEqual(parts['enemy_mask'].tolist(), [1.0] * ne + [0.0] * (S.ENEMY_ROWS - ne))
            self.assertFalse(parts['ally'][na:].any())
            self.assertFalse(parts['enemy'][ne:].any())

    def test_row_permutation_invariance(self):
        rng = random.Random(13)
        for _ in range(300):
            r = synth.plausible(rng)
            p = copy.deepcopy(r)
            rng.shuffle(p['ally'])
            rng.shuffle(p['enemy'])
            self.assertEqual(obs.encode(r).tobytes(), obs.encode(p).tobytes())

    def test_row_order_visible_then_near(self):
        rng = random.Random(14)
        r = synth.plausible(rng)
        for e in r['enemy']:
            e.update(present=1, known=1, visible=0, alive=1)
        r['enemy'][4]['visible'] = 1
        x = obs.split(obs.encode(r))
        self.assertEqual(x['enemy'][0][obs.EN['visible']], 1.0)
        d = [x['enemy'][k][obs.EN['dist']] for k in range(1, S.ENEMY_ROWS)]
        self.assertEqual(d, sorted(d))

    def test_zero_and_max_entities(self):
        rng = random.Random(15)
        r = synth.plausible(rng)
        for a in r['ally']:
            a['present'] = 0
        for e in r['enemy']:
            e['present'] = 0
        x = obs.encode(r)
        self.assertFalse(x[S.SELF_GLOBAL_DIM:].any())
        for a in r['ally']:
            a.update(present=1)
        for e in r['enemy']:
            e.update(present=1)
        x = obs.split(obs.encode(r))
        self.assertTrue(np.all(x['ally_mask'] == 1) and np.all(x['enemy_mask'] == 1))

    def test_dead_self(self):
        rng = random.Random(16)
        r = synth.plausible(rng)
        r.update(alive=0, hp=123.0)
        x = obs.encode(r)
        for n in ('self.alive', 'self.hp_frac', 'self.hp_delta_turn'):
            self.assertEqual(x[obs.SG[n]], 0.0, n)
        for e in r['enemy']:
            e.update(present=1, known=1, visible=1, x=r['pos_x'], y=r['pos_y'])
        p = obs.split(obs.encode(r))
        self.assertFalse(p['enemy'][:, obs.EN['in_my_range']].any())

    def test_nan_inf_guard_and_clip(self):
        rng = random.Random(17)
        for _ in range(500):
            x = obs.encode(synth.hostile_bytes(rng))
            self.assertTrue(np.all(np.isfinite(x)))
            self.assertFalse(np.any(np.signbit(x) & (x == 0)))
            sg = x[:S.SELF_GLOBAL_DIM]
            self.assertTrue(np.all(sg >= obs.SG_LO) and np.all(sg <= obs.SG_HI))
        r = synth.plausible(rng)
        r.update(hp=math.nan, max_hp=0.0, gems=10 ** 9, strength=math.inf)
        x = obs.encode(r)
        self.assertEqual(x[obs.SG['self.hp_frac']], 0.0)
        self.assertEqual(x[obs.SG['self.gems']], 10.0)
        self.assertEqual(x[obs.SG['self.strength']], 0.0)  # +inf * 0.01 is non-finite -> 0 before clipping

    def test_features_are_informative(self):
        rng = random.Random(18)
        X = np.stack([obs.encode(synth.plausible(rng)) for _ in range(400)])
        names = obs.feature_names()
        constant = [names[k] for k in range(S.OBS_DIM) if np.all(X[:, k] == X[0, k]) and 'mask' not in names[k]]
        self.assertLess(len(constant), S.OBS_DIM // 20, constant)


if __name__ == '__main__':
    unittest.main()
