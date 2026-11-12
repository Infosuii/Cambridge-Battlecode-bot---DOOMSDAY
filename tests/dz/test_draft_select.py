import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('draft_select', Path(__file__).resolve().parents[2]/'tools/dz_draft_select.py')
select = importlib.util.module_from_spec(spec)
spec.loader.exec_module(select)


class DraftSelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.patch = patch.object(select, 'ROOT', self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def write_run(self, name, rows):
        folder = self.root/'research/dz/runs'/name
        folder.mkdir(parents=True)
        (folder/'results.json').write_text(json.dumps({'per_game': rows}))

    def rows(self, name='map00', banked=10):
        return [dict(map=name, side=s, banked=banked, opponent_banked=0,
                     faults=0, fuel_outs=0, opponent_faults=0) for s in ('A', 'B')]

    def test_incomplete_side_rejected(self):
        self.write_run('broken', self.rows()[:1])
        with self.assertRaises(ValueError):
            select.per_map('broken')

    def test_duplicate_rejected(self):
        rows = self.rows()
        self.write_run('broken', rows + rows[:1])
        with self.assertRaises(ValueError):
            select.per_map('broken')

    def test_faulty_candidate_rejected(self):
        rows = self.rows()
        rows[0]['fuel_outs'] = 1
        self.write_run('broken', rows)
        with self.assertRaises(ValueError):
            select.per_map('broken')

    def test_actual_variant_id_and_registered_holdout(self):
        pool = self.root/'maps/local-benchmarks'
        pool.mkdir(parents=True)
        for i in range(70):
            (pool/f'map{i:02}.map26a').touch()
        self.write_run('base', self.rows() + self.rows('map04'))
        self.write_run('new', self.rows(banked=100) + self.rows('map04', 100))
        output = io.StringIO()
        with patch('sys.argv', ['select', '--runs', 'base', 'new', '--variants', '0', '7']), contextlib.redirect_stdout(output):
            select.main()
        report, _ = json.JSONDecoder().raw_decode(output.getvalue())
        self.assertEqual(report['table'], {'map00': 7})


if __name__ == '__main__':
    unittest.main()
