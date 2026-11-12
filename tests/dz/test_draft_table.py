import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec=importlib.util.spec_from_file_location('draft_table',Path(__file__).resolve().parents[2]/'tools/dz_draft_table.py')
table=importlib.util.module_from_spec(spec);spec.loader.exec_module(table)


class DraftTableTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.patch=patch.object(table,'ROOT',self.root);self.patch.start();self.addCleanup(self.patch.stop)
        self.pool=self.root/'maps/local-benchmarks';self.pool.mkdir(parents=True)
        for i in range(70):(self.pool/f'map{i:02}.map26a').touch()
        self.selection=self.root/'selection.txt';self.output=self.root/'table.inc'

    def capsule(self,duplicate=False):
        folder=self.root/'research/dz/runs/signatures';folder.mkdir(parents=True)
        games=[]
        with zipfile.ZipFile(folder/'evidence.zip','w') as z:
            for i in range(70):
                name=f'map{i:02}'
                for side in ('A','B'):
                    games.append(dict(map=name,side=side,faults=0,fuel_outs=0,caught_action_errors=0,caught_module_errors=0))
                    sig=1000 if duplicate else 1000+i
                    z.writestr(f'games/{name}-{side}/candidate.stdout',f'DZ_SIG signature={sig} variant=0\n')
        (folder/'results.json').write_text(json.dumps({'per_game':games}))

    def run_table(self,mapping):
        self.selection.write_text(json.dumps({'table':mapping})+'\nselection commentary')
        args=['table','--selection',str(self.selection),'--signatures-run','signatures','--output',str(self.output)]
        with patch('sys.argv',args),contextlib.redirect_stdout(io.StringIO()):table.main()

    def test_variant_id_and_signature_are_preserved(self):
        self.capsule();self.run_table({'map00':7})
        self.assertIn('{1000u, 7}',self.output.read_text())
        with self.assertRaises(FileExistsError):self.run_table({'map00':5})
        self.assertIn('{1000u, 7}',self.output.read_text())

    def test_registered_map_holdout_is_rejected(self):
        self.capsule()
        with self.assertRaises(ValueError):self.run_table({'map04':7})
        self.assertFalse(self.output.exists())

    def test_ambiguous_signature_cannot_generate_a_table(self):
        self.capsule(duplicate=True)
        with self.assertRaises(ValueError):self.run_table({'map00':7})


if __name__=='__main__':unittest.main()
