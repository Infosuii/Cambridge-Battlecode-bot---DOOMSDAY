"""Synthetic batch parity/authorization tests. No optimizer step, games or training."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import torch
from nfs.policy import training as T, model as M, export as E, observation as O, candidates as C

ROOT=Path(__file__).resolve().parents[2]

class TrainingPreflight(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='training_synthetic_',dir=ROOT/'artifacts/tmp')
        self.root=Path(self.temp.name)
        self.model=M.init_untrained(M.build_model('policy_v2'),77)
        self.manifest=E.export_model(self.model,'synthetic_training',self.root/'model','untrained',dict(synthetic=True))
        self.write_batch('train','synthetic_train_group');self.write_batch('validation','synthetic_validation_group')

    def tearDown(self):self.temp.cleanup()

    def write_batch(self,name,group):
        n=4;obs=np.zeros((n,O.OBS_DIM),np.float32);feat=np.zeros((n,16,12),np.float32)
        legal=np.zeros((n,16),bool);legal[:,:3]=True;feat[:,1,0]=.5;feat[:,2,0]=-.5
        with torch.no_grad():
            logits=self.model(torch.tensor(obs),'move',torch.tensor(feat),torch.tensor(legal),torch.zeros(n,dtype=torch.int64))
            chosen=torch.argmax(logits,dim=-1);logp=torch.log_softmax(logits,dim=-1).gather(1,chosen[:,None]).squeeze(1)
        path=self.root/(name+'.npz')
        np.savez_compressed(path,obs=obs,feat=feat,legal=legal,behavior_logits=logits.numpy(),behavior_logp=logp.numpy(),
            chosen=chosen.numpy(),teacher=np.full(n,-1,np.int64),head=np.full(n,M.HEAD_IDS['move'],np.int64),
            context=np.zeros(n,np.int64),ppo_mask=np.ones(n,bool),imitation_mask=np.zeros(n,bool),terminal_return=np.ones(n,np.float32))
        meta=dict(version=2,format='NFS2',synthetic=True,engine_version='1.0.3',obs_hash=O.OBS_SCHEMA_HASH,
            action_hash=C.ACTION_SCHEMA_HASH,behavior_model_checksum=self.manifest['checksum'],
            rows=[dict(group_id=group,episode_id=name,synthetic=True) for _ in range(n)],sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        path.with_suffix('.manifest.json').write_text(json.dumps(meta))

    def flight(self):return T.preflight(self.root/'model',self.root/'train.npz',self.root/'validation.npz','move')[0]

    def test_roundtrip_and_exact_pinned_behavior_parity(self):
        report=self.flight();self.assertEqual(report['train']['eligible'],4)
        self.assertTrue(report['validation']['synthetic']);self.assertLess(report['train']['max_logit_error'],1e-6)

    def test_group_leakage_is_rejected(self):
        self.write_batch('validation','synthetic_train_group')
        with self.assertRaisesRegex(ValueError,'leakage'):self.flight()

    def test_changed_behavior_weights_are_rejected(self):
        other=M.init_untrained(M.build_model('policy_v2'),78)
        E.export_model(other,'synthetic_training',self.root/'model','untrained',dict(synthetic=True))
        with self.assertRaisesRegex(ValueError,'exact recorded'):self.flight()

    def test_authorization_precedes_all_data_and_parameter_work(self):
        out=self.root/'must_not_exist'
        with self.assertRaises(PermissionError):T.fit('missing','missing','missing',out,authorized=False)
        self.assertFalse(out.exists())

    def test_terminal_discount_uses_last_started_round_without_off_by_one(self):
        game=dict(win=1,gems=1100,opponent_gems=900,rounds=10)
        self.assertAlmostEqual(T.terminal_return(game,9,.5),1.05)
        self.assertAlmostEqual(T.terminal_return(game,5,.5),1.05/16)
        with self.assertRaises(ValueError):T.terminal_return(game,10,.5)

    def test_output_cannot_escape_workspace_artifacts(self):
        with self.assertRaises(ValueError):T.writable(ROOT/'references/never_write')

    def test_generated_budget_matches_source_and_rejects_uncalibrated_architecture(self):
        import sys,copy
        sys.path.insert(0,str(ROOT/'tools'))
        from gen_policy_budget import render
        self.assertEqual(render(self.model.cfg),(ROOT/'bot/src/nn_policy_budget.h').read_text())
        changed=copy.deepcopy(self.model.cfg);changed['encoder']['ctx']+=1
        with self.assertRaisesRegex(ValueError,'new measured'):render(changed)

    def test_explicit_saved_model_and_record_head_install(self):
        import sys
        sys.path.insert(0,str(ROOT/'tools'))
        from install_policy_v2 import install
        target=install(self.root/'installed','direct_sample_record',self.root/'model',123,'move')
        text=(target/'src/nn_policy_config.h').read_text()
        self.assertIn('NN_POLICY_LOG_HEAD_MASK 64',text);self.assertIn('NN_POLICY_SEED 123ull',text)
        self.assertEqual(json.loads((target/'model/manifest.json').read_text())['checksum'],self.manifest['checksum'])

if __name__=='__main__':unittest.main()
