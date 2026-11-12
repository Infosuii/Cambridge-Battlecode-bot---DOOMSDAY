import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import numpy as np
import torch
from rl_learner_1104.cl1 import CampPointer,PREPROCESS_VERSION
from rl_learner_1104.model import masked_distribution
from rl_learner_1104.on_policy import ACTION_SCHEMA
from rl_learner_1104.rollout_io import trajectories,read_columns


def fixture(actor_hash):
    torch.manual_seed(1104)
    actor=CampPointer()
    x=np.zeros((3,448),dtype=np.int16)
    x[:,0]=[0,1,2];x[:,3]=1000;x[:,47]=7;x[:,224]=1
    masks=np.zeros((3,13),dtype=np.uint8);masks[:,[0,12]]=1
    actions=np.array([0,12,0],dtype=np.int16)
    reset=np.array([1,0,0],dtype=np.uint8)
    lp=[];hidden=actor.initial_state(1)
    with torch.no_grad():
        for i in range(3):
            logits,hidden=actor(torch.from_numpy(x[i:i+1]),hidden,torch.tensor([bool(reset[i])]))
            d=masked_distribution(logits,torch.from_numpy(masks[i:i+1].astype(bool)))
            lp.append(float(d.log_prob(torch.tensor([int(actions[i])]))))
    cols=dict(x_fresh=x,episode=np.zeros(3,dtype=np.uint32),body_id=np.full(3,7,dtype=np.int32),
              boundary=np.zeros(3,dtype=np.uint8),action=actions,executed=actions.copy(),mask=masks,
              logp=np.array(lp,dtype=np.float32),has_logp=np.ones(3,dtype=np.uint8),reset=reset,
              dt_rounds=np.array([1,1,0],dtype=np.int32),terminated=np.array([0,0,1],dtype=np.uint8),
              truncated=np.zeros(3,dtype=np.uint8),bootstrap_valid=np.zeros(3,dtype=np.uint8),
              act_round=np.arange(3,dtype=np.int32),feat_round=np.arange(3,dtype=np.int32),
              decision_index=np.arange(3,dtype=np.int32))
    man=dict(rows=3,contract_version='rlenv-2',layout=10,action_schema=ACTION_SCHEMA,sampling='complete',
             observation_point='farm-pre-actor',preprocess=PREPROCESS_VERSION,temperature=1.,data_origin='synthetic-test',
             policy=dict(actor_json_sha256=actor_hash,wasm_sha256='fixture',encoder_sha256='fixture'),
             episodes=[dict(key='fixture',ppo_eligible=True,status='terminated',incomplete=False,fuel_failed=False,
                            log_cut=False,final_scores=dict(ours=1000,theirs=0),end_round=2,terminal_outcome=1,
                            engine_build_hash='fixture',map_hash='fixture')])
    return actor,man,cols


class RolloutIOTests(unittest.TestCase):
    def test_adapter_and_terminal_zero_dt(self):
        _,m,c=fixture('fixture')
        batch=trajectories(m,c,'fixture')
        self.assertEqual(len(batch),1)
        self.assertEqual(batch[0].elapsed,[1,1,0])
        self.assertEqual(batch[0].rewards[-1],1.)

    def test_missing_decisions_and_invalid_masks_rejected(self):
        _,m,c=fixture('fixture')
        c['decision_index'][1]=9
        with self.assertRaisesRegex(ValueError,'decision'):
            trajectories(m,c,'fixture')
        c['decision_index'][1]=1;c['mask'][0,0]=2
        with self.assertRaisesRegex(ValueError,'boolean'):
            trajectories(m,c,'fixture')

    def test_changed_schema_and_missing_integrity_rejected(self):
        _,m,c=fixture('fixture')
        m['action_schema']='target13-cl1'
        with self.assertRaises(ValueError):
            trajectories(m,c,'fixture')
        m['action_schema']=ACTION_SCHEMA;del m['episodes'][0]['fuel_failed']
        with self.assertRaises(ValueError):
            trajectories(m,c,'fixture')

    def test_actual_cli_update_checkpoint_and_export_on_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);a,_,_=fixture('pending')
            spec=dict(format='jd-cl1-pointer-f32-v1',preprocess=PREPROCESS_VERSION,
                      tensors={k:dict(shape=list(v.shape),values=v.flatten().tolist()) for k,v in a.state_dict().items()})
            p=root/'actor.json';p.write_text(json.dumps(spec))
            h=hashlib.sha256(p.read_bytes()).hexdigest()
            _,m,c=fixture(h)
            shard=root/'shard';shard.mkdir()
            m['columns']={}
            for name,col in c.items():
                col.tofile(shard/(name+'.bin'))
                m['columns'][name]=dict(dtype=str(col.dtype),shape=list(col.shape))
            (shard/'shard.json').write_text(json.dumps(m))
            loaded,columns,_=read_columns(shard)
            self.assertEqual(len(trajectories(loaded,columns,h)),1)
            run=subprocess.run([sys.executable,str(Path(__file__).with_name('train_ppo.py')),
                                '--actor',str(p),'--shard',str(shard),'--out',str(root/'updated'),'--epochs','1'],
                               capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            report=json.loads((root/'updated'/'report.json').read_text())
            self.assertEqual(report['status'],'SYNTHETIC_TEST_ONLY')
            self.assertNotEqual(report['input_actor_sha256'],report['output_actor_sha256'])
            self.assertTrue((root/'updated'/'export'/'parity.json').exists())
            trainer=torch.load(root/'updated'/'trainer_state.pt',weights_only=True)
            self.assertEqual(trainer['iteration'],1)


if __name__=='__main__':
    unittest.main()
