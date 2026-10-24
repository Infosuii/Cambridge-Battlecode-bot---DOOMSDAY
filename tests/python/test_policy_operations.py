"""Synthetic/read-only operations tests. No engine games or match-data training."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from nfs.policy import operations as P

ROOT=Path(__file__).resolve().parents[2]

class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='synthetic_ops_',dir=ROOT/'artifacts/tmp');self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()

    def test_version_comparison_has_true_non_neural_baseline_and_bounded_plan(self):
        base=ROOT/'models/policy_v2_untrained';plan=P.comparison_plan(base,[base],['00rows'])
        self.assertEqual(plan['games'],4);self.assertEqual(plan['opponents'][0]['kind'],'non_neural_baseline')
        self.assertTrue(plan['opponents'][1]['same_weights_control']);self.assertFalse(plan['promotion_authorized'])
        with self.assertRaisesRegex(ValueError,'exceeds bound'):P.comparison_plan(base,[base],['00rows'],max_games=2)
        final=json.loads((ROOT/'evaluation/schedules/map_partitions.json').read_text())['partitions']['final'][0]
        with self.assertRaisesRegex(ValueError,'final'):P.comparison_plan(base,[],[final])

    def test_baseline_preprocessor_proves_neural_switches_are_off(self):
        path,audit=P.baseline_source(self.root/'baseline')
        self.assertTrue(all(value=='0' for value in audit['neural_macros'].values()))
        self.assertIn('A2_MLDRAFT 0',(path/'src/common.h').read_text())
        self.assertIn('inherited trained draft disabled',audit['drafting'])

    def test_status_validates_checkpoint_checksum_and_ignores_partial_metric_line(self):
        state=b'synthetic checkpoint bytes';(self.root/'checkpoint.pt').write_bytes(state)
        (self.root/'checkpoint.json').write_text(json.dumps(dict(checkpoint='checkpoint.pt',sha256=hashlib.sha256(state).hexdigest(),absolute_deadline=0)))
        (self.root/'metrics.jsonl').write_text('{"event":"update","synthetic":true}\n{"partial":')
        result=P.status(self.root);self.assertTrue(result['checkpoint']['checksum_valid']);self.assertTrue(result['deadline_expired'])
        self.assertEqual(len(result['last_events']),1)
        (self.root/'checkpoint.pt').write_bytes(b'corrupt');self.assertFalse(P.status(self.root)['checkpoint']['checksum_valid'])

    def test_status_cannot_follow_an_index_outside_its_run(self):
        (self.root/'checkpoint.json').write_text(json.dumps(dict(checkpoint='../escape.pt',sha256='x',absolute_deadline=0)))
        with self.assertRaisesRegex(ValueError,'escapes'):P.status(self.root)

    def test_invalid_automatic_evaluation_is_rejected_before_training(self):
        p=self.root/'eval.json';p.write_text(json.dumps(dict(every_epochs=0)))
        with self.assertRaisesRegex(ValueError,'cadence'):P.validate_evaluation_config(p,ROOT/'models/policy_v2_untrained')

    def test_action_inspection_never_joins_another_champions_ack(self):
        first=dict(kind='decision',round=7,champion=1,decision_id=42,head=6,source=0,selected_id=99,chosen=0,K=1,sampled=1,logp=0.)
        second=dict(first,champion=2,selected_id=199)
        ack=dict(kind='execution',champion=2,decision_id=42,outcome=1,executed_id=199,reason=0)
        with patch.object(P.engine,'team_stdout',return_value='synthetic'),patch.object(P.R,'decode_stdout',return_value=[first,second,ack]):
            result=P.inspect_game(self.root)
        self.assertIsNone(result['actions'][0]['execution'])
        self.assertEqual(result['actions'][1]['execution']['executed_id'],199)

    def test_regular_evaluation_cadence_calls_comparison_without_training(self):
        import shutil
        from nfs.policy.export import load_model
        shutil.copytree(ROOT/'models/policy_v2_untrained',self.root/'behavior')
        config=self.root/'evaluation.json';config.write_text(json.dumps(dict(every_epochs=2,max_evaluations=1,maps=['00rows'],max_games=4)))
        model=load_model(ROOT/'models/policy_v2_untrained')
        with patch.object(P,'export_model'),patch.object(P,'compare',return_value=dict(implementation_passed=True,summary={})) as compare:
            self.assertIsNone(P.evaluate_epoch(model,self.root,1,'role',config))
            result=P.evaluate_epoch(model,self.root,2,'role',config)
            self.assertTrue(result['implementation_passed']);compare.assert_called_once()

if __name__=='__main__':unittest.main()
