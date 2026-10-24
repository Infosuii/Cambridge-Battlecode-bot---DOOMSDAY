"""Synthetic lossless recovery, corruption and safe-resume checks; no project source is modified."""
import contextlib
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import types
import unittest

ROOT=Path(__file__).resolve().parents[2]

class RecoveryArchive(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'artifacts/tmp',prefix='recovery-test-')
        self.root=Path(self.temp.name);(self.root/'config').mkdir();self.source=self.root/'source';self.source.mkdir()
        (self.root/'config/recovery_sources.json').write_text(json.dumps(dict(roots=dict(main=str(self.source)),project_prefix='main')))
        spec=importlib.util.spec_from_file_location('recovery_fixture',ROOT/'tools/recovery_archive.py')
        self.archive=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.archive)
        self.archive.ROOT=self.root;self.archive.OUT=self.root/'recovery';self.archive.CHUNK=1024;self.archive.PACK_LIMIT=4096
        self.archive.ARGS=types.SimpleNamespace(resume=False)
        self.output=io.StringIO();self.redirect=contextlib.redirect_stdout(self.output);self.redirect.__enter__()
    def tearDown(self):
        self.redirect.__exit__(None,None,None);self.temp.cleanup()
    def fixture(self):
        payload=(bytes(range(256))*30)+b'tail'
        (self.source/'data.bin').write_bytes(payload);(self.source/'duplicate.bin').write_bytes(payload)
        (self.source/'empty').write_bytes(b'');(self.source/'nested').mkdir();(self.source/'nested/hello.txt').write_text('synthetic unicode: café')
        (self.source/'credentials.json').write_text('SYNTHETIC_EXCLUDED_SECRET')
        return payload
    def test_lossless_dedup_and_secret_exclusion(self):
        payload=self.fixture();self.archive.snapshot();self.archive.verify(full=True)
        receipt=json.loads((self.archive.OUT/'snapshot.json').read_text());self.assertEqual(receipt['errors'],0)
        self.assertEqual(receipt['files'],4);self.assertEqual(receipt['excluded'],1)
        self.assertLess(receipt['unique_bytes'],len(payload));dest=self.root/'restored';self.archive.restore(dest,'project')
        self.assertEqual((dest/'data.bin').read_bytes(),payload);self.assertEqual((dest/'duplicate.bin').read_bytes(),payload)
        self.assertEqual((dest/'empty').read_bytes(),b'');self.assertFalse((dest/'credentials.json').exists())
        self.assertEqual(json.loads((dest/'RESTORE_RECEIPT.json').read_text())['files'],4)
        with self.assertRaises(RuntimeError):self.archive.restore(dest,'all')
    def test_corruption_refused(self):
        self.fixture();self.archive.snapshot();pack=next((self.archive.OUT/'packs').glob('*.zip'))
        b=bytearray(pack.read_bytes());b[40]^=1;pack.write_bytes(b)
        with self.assertRaises(RuntimeError):self.archive.verify(full=True)
    def test_resume_reuses_closed_packs_and_preserves_bad_tail(self):
        self.fixture();self.archive.snapshot();old={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.archive.OUT/'packs').glob('*.zip')}
        (self.archive.OUT/'snapshot.json').rename(self.archive.OUT/'prior-receipt.json')
        (self.archive.OUT/'packs/pack-00099.zip').write_bytes(b'synthetic interrupted tail')
        (self.source/'new.txt').write_text('a new synthetic file')
        self.archive.ARGS.resume=True;self.archive.snapshot();self.archive.verify(full=True)
        self.assertTrue((self.archive.OUT/'incomplete/pack-00099.zip').exists())
        for name,digest in old.items():self.assertEqual(hashlib.sha256((self.archive.OUT/'packs'/name).read_bytes()).hexdigest(),digest)
        self.archive.restore(self.root/'restored','all')
        self.assertEqual((self.root/'restored/main/new.txt').read_text(),'a new synthetic file')
    def test_unsafe_restore_paths_refused(self):
        for path in ('../escape','/absolute','a/../../b','C:/outside'):
            with self.assertRaises(ValueError):self.archive.safe_relative(path)
        self.assertEqual(str(self.archive.safe_relative('folder/file.txt')),'folder/file.txt')

if __name__=='__main__':unittest.main()
