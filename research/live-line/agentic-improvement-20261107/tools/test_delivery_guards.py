from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import ladder_delivery as delivery

class DeliveryGuards(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name); self.release=self.base/'release/test'; self.release.mkdir(parents=True)
        self.cli=self.base/'cambc.exe'; self.cli.write_bytes(b'fixture-cli')
        self.source=self.base/'arena/bots/test/src'; self.source.mkdir(parents=True)
        (self.source/'bot.cpp').write_bytes(b'correct-source')
        archive=self.release/'test.zip'
        with zipfile.ZipFile(archive,'w') as z:z.writestr('src/bot.cpp',b'correct-source')
        self.manifest={'candidate':'test','source_digest':'f'*64,'cli_sha256':hashlib.sha256(self.cli.read_bytes()).hexdigest(),
                       'source_zip':{'file':'test.zip','sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}}
        (self.release/'manifest.json').write_text(json.dumps(self.manifest))
        self.info={'team':{'id':delivery.TEAM},'active':{'version':111},'selected':{'version':111},'submissions':[]}

    def run_guard(self):
        with patch.object(delivery,'BASE',self.base), patch.object(delivery,'CLI',self.cli), \
             patch.object(delivery,'cli',return_value=self.info) as call, \
             patch('sys.argv',['delivery','upload',str(self.release),'--expected','111']):
            with self.assertRaises(AssertionError):delivery.main()
            self.assertEqual(call.call_args_list[0].args,('submissions','list','--json'))
            self.assertEqual(call.call_count,1,'A guarded failure must never reach upload')

    def test_concurrent_active_change_refuses_upload(self):
        self.info['active']['version']=112;self.run_guard()
    def test_uncertain_upload_never_blindly_retries(self):
        (self.release/'ladder-receipt.json').write_text(json.dumps({'expected_version':111,'phase':'upload_uncertain'}));self.run_guard()
    def test_changed_source_refuses_upload(self):
        (self.source/'bot.cpp').write_bytes(b'changed');self.run_guard()
    def test_extra_source_refuses_upload(self):
        (self.source/'extra.cpp').write_bytes(b'new');self.run_guard()
    def test_wrong_team_refuses_upload(self):
        self.info['team']['id']='other-team';self.run_guard()

if __name__=='__main__':unittest.main()
