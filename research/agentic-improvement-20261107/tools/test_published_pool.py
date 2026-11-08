from pathlib import Path
import tempfile
import unittest
from published_pool import verified_pool

class PublishedPoolTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.local=self.root/'local';self.official=self.root/'official'
        self.local.mkdir();self.official.mkdir();self.catalog=[{'name':'the_line','mapId':'official-id'}]
        (self.local/'the-line.map26a').write_bytes(b'official-map')
        (self.official/'the_line.map26a').write_bytes(b'official-map')
    def test_custom_fixture_does_not_enter_published_pool(self):
        (self.local/'cast_008_major_objectives.map26a').write_bytes(b'synthetic')
        result=verified_pool(self.local,self.official,self.catalog)
        self.assertEqual(len(result),1);self.assertEqual(result[0]['mapId'],'official-id')
    def test_edited_official_named_file_is_refused(self):
        (self.local/'the-line.map26a').write_bytes(b'edited')
        with self.assertRaises(AssertionError):verified_pool(self.local,self.official,self.catalog)
    def test_incomplete_official_download_is_refused(self):
        self.catalog.append({'name':'missing','mapId':'missing-id'})
        with self.assertRaises(AssertionError):verified_pool(self.local,self.official,self.catalog)

if __name__=='__main__':unittest.main()
