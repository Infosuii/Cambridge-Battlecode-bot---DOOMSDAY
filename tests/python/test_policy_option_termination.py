"""Synthetic macro interruptions must never enter actor ratios. No optimizer or match data."""
import copy
import unittest
import numpy as np
from nfs.policy import records as R
from nfs.policy import dataset as D
from nfs.policy import observation as O

def decision():
    return dict(kind='decision',obs_hash=O.OBS_SCHEMA_HASH,action_hash=1,round=7,champion=99,snapshot=1,
        decision_id=42,head=3,K=1,F=12,chosen=0,teacher=-1,context=0,sampled=1,source=0,flags=0,
        reason=0,option_id=0,selected_id=30,logp=0,id=np.array([30],dtype=np.uint32),legal=np.array([1]),
        logits=np.zeros(1,dtype=np.float32),feat=np.zeros((1,12),dtype=np.float32))
def ack(d):
    return dict({k:d[k] for k in ('obs_hash','action_hash','round','champion','snapshot','decision_id')},
        kind='execution',executed_id=d['selected_id'],outcome=1,source=d['source'],reason=0,option_id=d['option_id'])
def context(d):
    return dict({k:d[k] for k in ('obs_hash','action_hash','round','champion','snapshot')},
        kind='context',decision_id=0,raw=np.zeros(O.OBS_DIM,dtype='<f4').tobytes())

class OptionTerminationTests(unittest.TestCase):
    def episode(self,end_reason=None,end=True):
        d=decision();d.update(flags=R.OPTION_START|R.DEFINED_OPTION,option_id=77)
        a=ack(d);a['outcome']=2
        records=[context(d),d,a]
        if end:
            e=copy.deepcopy(d);e.update(decision_id=d['decision_id']+1,round=d['round']+3,source=1,
                flags=R.OPTION_END|R.DEFINED_OPTION,sampled=0,logp=0,reason=end_reason or 0)
            ea=ack(e);ea.update(outcome=2,reason=end_reason or 0)
            records.extend([e,ea])
        return D.build_dataset(records,episode_id='synthetic_option',group_id='synthetic_group',synthetic=True)
    def test_unclosed_start_excluded(self):
        d=self.episode(end=False);self.assertFalse(d.rows[0]['ppo_mask']);self.assertEqual(d.counts['excluded_option_unclosed'],1)
    def test_interrupted_start_excluded(self):
        d=self.episode(10);self.assertFalse(d.rows[0]['ppo_mask']);self.assertEqual(d.counts['excluded_option_interrupted'],1)
    def test_completed_sample_preserved(self):
        d=self.episode(0);self.assertTrue(d.rows[0]['ppo_mask']);self.assertEqual(d.counts['ppo_eligible'],1)
