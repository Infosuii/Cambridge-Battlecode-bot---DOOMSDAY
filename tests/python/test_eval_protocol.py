"""Frozen protocol integrity: lock matches, schedules reproducible from code, partitions disjoint, framework
schedules never touch final/selection maps, every map labelled reused_benchmark."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'python'))
from nfs.evaluate import protocol as P  # noqa: E402


@unittest.skipUnless(P.LOCK.exists(), 'protocol not frozen yet')
class TestFrozenProtocol(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proto = P.load(verify=True)
        cls.parts = P.load_schedule('map_partitions')['partitions']

    def test_lock_and_code_agree(self):
        built, schedules = P.build()
        self.assertEqual(P._dump(built), P.PROTOCOL.read_text(encoding='utf-8'),
                         'protocol code changed after freezing: supersede explicitly with a reason')
        for k, v in schedules.items():
            self.assertEqual(P._dump(v), (P.SCHEDULES / f'{k}.json').read_text(encoding='utf-8'), k)

    def test_partitions(self):
        f, s, t = (set(self.parts[k]) for k in ('final', 'selection', 'training'))
        self.assertFalse(f & s or f & t or s & t)
        self.assertEqual(len(f | s | t), 40)
        self.assertEqual((len(f), len(s), len(t)), (12, 10, 18))

    def test_framework_schedules_use_training_maps_only(self):
        train = set(self.parts['training'])
        for name in ('repro', 'equivalence', 'smoke', 'fuel_profile'):
            maps = {c['map'] for c in P.load_schedule(name)['cells']}
            self.assertTrue(maps <= train, (name, maps - train))

    def test_gate_schedules(self):
        fin, sel = P.load_schedule('final'), P.load_schedule('selection')
        self.assertEqual({c['map'] for c in fin['cells']}, set(self.parts['final']))
        self.assertEqual({c['map'] for c in sel['cells']}, set(self.parts['selection']))
        self.assertEqual(len(fin['cells']), 12 * 2 * 4)
        self.assertEqual({c['opponent'] for c in fin['cells']}, {'original', 'v47', 'first-hour', 'v50'})

    def test_labels(self):
        labels = P.load_schedule('map_partitions')['labels']
        self.assertEqual(set(labels.values()), {'reused_benchmark'})
        for k in self.proto['schedules']:
            self.assertEqual(P.load_schedule(k)['map_label'], 'reused_benchmark')
        self.assertEqual(P.load_schedule('smoke')['label'], 'untrained framework check')

    def test_reference_hashes_frozen(self):
        man = json.loads((ROOT / 'references/builds/manifest.json').read_text())['opponents']
        for k, v in self.proto['references'].items():
            self.assertEqual(v['wasm_sha256'], man[k]['wasm_sha256'])


if __name__ == '__main__':
    unittest.main()
