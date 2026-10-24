"""Schema / generator tests (agent C): checked-in generated files match tools/gen_schema.py, hash and dims agree."""
from __future__ import annotations

import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _gen():
    spec = importlib.util.spec_from_file_location('gen_schema', ROOT / 'tools' / 'gen_schema.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestObsSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gen = _gen()
        cls.schema = json.loads((ROOT / 'schemas' / 'observation.json').read_text(encoding='utf-8'))

    def test_checked_in_files_match_generator(self):
        h, py = self.gen.generate()
        self.assertEqual((ROOT / 'bot/src/nn_schema.h').read_text(encoding='utf-8'), h,
                         'bot/src/nn_schema.h is stale: run tools/gen_schema.py')
        self.assertEqual((ROOT / 'python/nfs/schema_gen.py').read_text(encoding='utf-8'), py,
                         'python/nfs/schema_gen.py is stale: run tools/gen_schema.py')
        self.assertEqual(self.gen.main(['--check']), 0)

    def test_generator_deterministic(self):
        a = self.gen.generate()
        b = self.gen.generate(json.loads((ROOT / 'schemas' / 'observation.json').read_text(encoding='utf-8')))
        self.assertEqual(a, b)

    def test_hash_is_fnv_of_canonical_json(self):
        from nfs import schema_gen as S
        canon = json.dumps(self.schema, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')
        h = 0x811C9DC5
        for b in canon:
            h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
        self.assertEqual(h, S.OBS_SCHEMA_HASH)
        hdr = (ROOT / 'bot/src/nn_schema.h').read_text(encoding='utf-8')
        self.assertIn(f'kObsSchemaHash = 0x{h:08X}u', hdr)
        # Any semantic edit changes the hash.
        edited = json.loads(json.dumps(self.schema))
        edited['self_global'][1]['scale'] = 2
        self.assertNotEqual(self.gen.fnv1a32(self.gen.canonical_bytes(edited)), h)

    def test_header_constants_equal_python(self):
        from nfs import schema_gen as S
        hdr = (ROOT / 'bot/src/nn_schema.h').read_text(encoding='utf-8')

        def c(name):
            m = re.search(rf'\b{name} = (\d+)', hdr)
            self.assertIsNotNone(m, name)
            return int(m.group(1))
        self.assertEqual(c('kSelfGlobalDim'), S.SELF_GLOBAL_DIM)
        self.assertEqual(c('kAllyRows'), S.ALLY_ROWS)
        self.assertEqual(c('kAllyDim'), S.ALLY_DIM)
        self.assertEqual(c('kEnemyRows'), S.ENEMY_ROWS)
        self.assertEqual(c('kEnemyDim'), S.ENEMY_DIM)
        self.assertEqual(c('kRawTurnSize'), S.RAW_TURN_SIZE)
        self.assertEqual(S.OBS_DIM, S.SELF_GLOBAL_DIM + S.ALLY_ROWS * S.ALLY_DIM + S.ALLY_ROWS + S.ENEMY_ROWS * S.ENEMY_DIM + S.ENEMY_ROWS)
        self.assertEqual(len(S.SG_NAMES), S.SELF_GLOBAL_DIM)
        self.assertEqual(len(S.ALLY_NAMES), S.ALLY_DIM)
        self.assertEqual(len(S.ENEMY_NAMES), S.ENEMY_DIM)

    def test_every_feature_documented(self):
        classes = set(self.schema['visibility_classes'])
        required = {'name', 'source', 'units', 'scale', 'clip', 'visibility'}

        def walk(feats):
            for f in feats:
                if 'repeat' in f:
                    yield from walk(f['fields'])
                    continue
                yield f
        n = 0
        for block in ('self_global', 'ally_row', 'enemy_row'):
            for f in walk(self.schema[block]):
                n += 1
                self.assertTrue(required <= set(f), f)
                self.assertIn(f['visibility'], classes, f['name'])
                self.assertGreater(f['scale'], 0)
                lo, hi = f['clip']
                self.assertLessEqual(lo, 0)
                self.assertGreaterEqual(hi, 0)
                self.assertTrue(f['source'].strip())
        self.assertGreater(n, 50)

    def test_rows_cover_all_bodies(self):
        # bot.h: kClaimSlots = 6 bodies per team at most -> 5 allies besides self, 6 enemies.
        bot_h = (ROOT / 'bot/src/bot.h').read_text(encoding='utf-8')
        slots = int(re.search(r'kClaimSlots = (\d+)', bot_h).group(1))
        self.assertEqual(self.schema['rows']['ally']['K'], slots - 1)
        self.assertEqual(self.schema['rows']['enemy']['K'], slots)

    def test_float_literals_exact(self):
        import numpy as np
        from nfs import schema_gen as S
        blocks = [(S.SG_INV_SCALE, self.gen.build(self.schema)['sg']), (S.ALLY_INV_SCALE, self.gen.build(self.schema)['ally']),
                  (S.ENEMY_INV_SCALE, self.gen.build(self.schema)['enemy'])]
        for arr, feats in blocks:
            self.assertEqual(len(arr), len(feats))
            for v, f in zip(arr, feats):
                # The printed decimal parses to exactly float32(1/scale) (the C++ literal uses the same digits).
                self.assertEqual(np.float32(v), np.float32(1.0 / f['scale']), f['name'])


if __name__ == '__main__':
    unittest.main()
