from pathlib import Path
import hashlib
import json
import tempfile
import unittest
import zipfile
from restore_findings import restore

class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.snapshot=self.root/'snapshot'; self.snapshot.mkdir()
        (self.snapshot/'index').mkdir(); self.output=self.root/'restore'
        self.data='exact source\r\n'.encode(); self.hash=hashlib.sha256(self.data).hexdigest()
        part=self.snapshot/'objects.zip'
        with zipfile.ZipFile(part,'w') as z:z.writestr('sha256/'+self.hash,self.data)
        self.manifest={'archives':[{'file':'objects.zip','sha256':hashlib.sha256(part.read_bytes()).hexdigest()}],
                       'objects':{self.hash:{'archive':'objects.zip','entry':'sha256/'+self.hash}},
                       'files':{'src/bot.cpp':{'sha256':self.hash,'bytes':len(self.data)}}}
        self.save()
    def save(self):
        (self.snapshot/'index/artifacts.json').write_text(json.dumps(self.manifest))
    def test_roundtrip_and_verify_only(self):
        self.assertEqual(restore(self.snapshot,self.output,True),1); self.assertFalse(self.output.exists())
        self.assertEqual(restore(self.snapshot,self.output),1); self.assertEqual((self.output/'src/bot.cpp').read_bytes(),self.data)
    def test_different_existing_file_is_preserved(self):
        (self.output/'src').mkdir(parents=True); (self.output/'src/bot.cpp').write_bytes(b'user work')
        with self.assertRaises(AssertionError):restore(self.snapshot,self.output)
        self.assertEqual((self.output/'src/bot.cpp').read_bytes(),b'user work')
    def test_archive_tamper_is_detected(self):
        with (self.snapshot/'objects.zip').open('ab') as f:f.write(b'tamper')
        with self.assertRaises(AssertionError):restore(self.snapshot,self.output)
        self.assertFalse(self.output.exists())
    def test_path_escape_is_refused(self):
        self.manifest['files']['../outside.cpp']=self.manifest['files'].pop('src/bot.cpp'); self.save()
        with self.assertRaises(AssertionError):restore(self.snapshot,self.output)
        self.assertFalse((self.root/'outside.cpp').exists())

if __name__=='__main__':unittest.main()
