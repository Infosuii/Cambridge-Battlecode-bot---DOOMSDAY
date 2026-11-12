"""A fresh Windows clone can use an installed CLI without local vendor files."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('dz_portable_runner', Path(__file__).resolve().parents[2] / 'tools/dz.py')
DZ = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DZ)


class CliResolutionTests(unittest.TestCase):
    def test_explicit_override(self):
        with tempfile.TemporaryDirectory() as folder:
            cli = Path(folder) / 'custom cli.exe'
            with patch.dict(os.environ, {'DZ_CAMBC': str(cli)}), patch.object(DZ.shutil, 'which', return_value=None):
                self.assertEqual(DZ.resolve_cli(), cli.resolve())

    def test_installed_cli_without_vendor(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            installed = root / 'installed' / 'cambc'
            with patch.dict(os.environ, {'DZ_CAMBC': ''}), patch.object(DZ, 'ROOT', root), patch.object(DZ.shutil, 'which', return_value=str(installed)):
                self.assertEqual(DZ.resolve_cli(), installed)

    @unittest.skipUnless(os.name == 'nt', 'Native Windows vendor preference')
    def test_existing_vendor_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            vendored = root / 'tools/vendor/cambc.exe'
            vendored.parent.mkdir(parents=True)
            vendored.write_bytes(b'fixture; not executed')
            with patch.dict(os.environ, {'DZ_CAMBC': ''}), patch.object(DZ, 'ROOT', root):
                self.assertEqual(DZ.resolve_cli(), vendored)


if __name__ == '__main__':
    unittest.main()
