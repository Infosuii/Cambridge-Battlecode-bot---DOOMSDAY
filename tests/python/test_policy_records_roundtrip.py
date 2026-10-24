"""Synthetic NFS2 codec, execution joins and direct-logit loss tests. No data collection or optimizer steps."""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import unittest
import numpy as np
import torch
from nfs.policy import records as R
from nfs.policy import losses as L

ROOT=Path(__file__).resolve().parents[2]
TMP=ROOT/'artifacts/tmp/v2_records'

def record(**changes):
    logits=np.asarray([.25,-np.inf,1.25],np.float32);legal=np.asarray([1,0,1],np.uint8)
    r=dict(kind='decision',obs_hash=0x12345678,action_hash=0xabcdef01,round=7,champion=99,snapshot=1,decision_id=42,
           head=6,K=3,F=12,chosen=2,teacher=-1,teacher_id=R.NO_ACTION,context=0,sampled=1,source=0,flags=0,reason=0,option_id=0,
           selected_id=30,logp=-.3132616875,fuel=dict(candidate=100,observation=200,inference=300,log=400),
           id=np.asarray([10,20,30],np.uint32),legal=legal,logits=logits,feat=np.arange(36,dtype=np.float32).reshape(3,12)/100)
    r.update(changes);return r

def ack(d,**changes):
    r={k:d[k] for k in ('obs_hash','action_hash','round','champion','snapshot','decision_id')}
    r.update(kind='execution',executed_id=d['selected_id'],outcome=1,source=d['source'],reason=0,option_id=d['option_id'],action_fuel=50,log_fuel=10)
    r.update(changes);return r

class RecordCodec(unittest.TestCase):
    def compile_driver(self):
        TMP.mkdir(parents=True,exist_ok=True)
        cxx=json.loads((ROOT/'config/paths.json').read_text())['native_cxx'];exe=TMP/'test_policy_records.exe'
        env=dict(os.environ,TMP=str(TMP),TEMP=str(TMP),PATH=str(Path(cxx).parent)+os.pathsep+os.environ.get('PATH',''))
        p=subprocess.run([cxx,'-std=c++20','-O2','-ffp-contract=off','-I'+str(ROOT/'bot/src'),str(ROOT/'tests/cpp/test_policy_records_roundtrip.cpp'),'-o',str(exe)],env=env,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        return exe,env

    def test_roundtrip_no_teacher_fabrication(self):
        r=R.decode_line(R.encode_line(record()))
        self.assertEqual(r['teacher'],-1);self.assertEqual(r['teacher_id'],R.NO_ACTION)
        self.assertEqual(r['selected_id'],30);np.testing.assert_array_equal(r['feat'],record()['feat'])
        self.assertEqual(R.encode_payload(r),R.encode_payload(record()))
        self.assertEqual(R.decode_stdout('NFS1 ZmFrZQ==\n'+R.encode_line(record())+'\0'*30)[0]['chosen'],2)

    def test_checksum_version_size_and_schema_rejection(self):
        p=bytearray(R.encode_payload(record()));p[-8]^=1
        with self.assertRaises(R.RecordError):R.decode_payload(p)
        for offset,value,fmt in ((4,1,'H'),(8,999,'I')):
            p=bytearray(R.encode_payload(record()));struct.pack_into('<'+fmt,p,offset,value)
            struct.pack_into('<I',p,len(p)-4,R.checksum(p[:-4]))
            with self.assertRaises(R.RecordError):R.decode_payload(p)
        with self.assertRaises(R.RecordError):R.decode_line(R.encode_line(record()),expected_action_hash=12)
        with self.assertRaises(R.RecordError):R.decode_line('NFS2 !!!')
        stats={};self.assertEqual([],R.decode_stdout('NFS2 !!!',strict=False,stats=stats));self.assertEqual(stats,{'invalid':1})

    def test_bounds_masks_finite_and_optional_teacher(self):
        bad=[record(F=24),record(K=17),record(context=4),record(chosen=-1),record(teacher=0),record(sampled=2),
             record(id=np.asarray([10,10,30])),record(legal=np.asarray([1,2,1])),record(selected_id=10),
             record(feat=np.full((3,12),np.nan)),record(logits=np.asarray([np.inf,-np.inf,1.])),record(logp=float('nan'))]
        for r in bad:
            with self.subTest(keys=r),self.assertRaises(R.RecordError):R.encode_payload(r)
        r=record(teacher=0,teacher_id=10);self.assertEqual(R.decode_line(R.encode_line(r))['teacher'],0)
        r=record(teacher=-1,teacher_id=999);self.assertEqual(R.decode_line(R.encode_line(r))['teacher_id'],999)
        r=record(K=0,chosen=-1,selected_id=R.NO_ACTION,source=2,sampled=0,logp=0,id=np.asarray([],np.uint32),legal=np.asarray([],np.uint8),logits=np.asarray([],np.float32),feat=np.empty((0,12),np.float32))
        self.assertEqual(R.decode_line(R.encode_line(r))['chosen'],-1)

    def test_native_cpp_roundtrip_and_ring_bounds(self):
        from nfs.policy import observation as obs
        exe,env=self.compile_driver()
        p=subprocess.run([str(exe),str(obs.OBS_SCHEMA_HASH),str(obs.OBS_DIM)],env=env,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr[-4000:])
        recs=R.decode_stdout(p.stdout,expected_obs_hash=obs.OBS_SCHEMA_HASH)
        self.assertEqual([r['kind'] for r in recs],['context','decision','execution','decision','execution'])
        self.assertEqual(recs[1]['teacher'],-1);self.assertEqual(recs[3]['teacher'],0)
        self.assertAlmostEqual(recs[1]['logp'],record()['logp'],places=6)
        self.assertEqual(692,len(recs[0]['raw']))
        self.assertIn('invalid=3 ring=500 overflow=1',p.stdout)
        from nfs.policy.dataset import build_dataset,collate
        ds=build_dataset(recs,episode_id='synthetic_cpp',group_id='synthetic_cpp_group',synthetic=True,expected_action_hash=0xabcdef01)
        self.assertEqual(ds.counts['ppo_eligible'],1);self.assertEqual(ds.counts['imitation_eligible'],1)
        self.assertEqual(tuple(collate(ds.rows)['obs'].shape),(2,173))

    def test_varied_cpp_behavior_logp_torch_parity_all_heads(self):
        from nfs.policy import observation as obs
        from nfs.models.reference import masked_sample
        exe,env=self.compile_driver()
        p=subprocess.run([str(exe),str(obs.OBS_SCHEMA_HASH),str(obs.OBS_DIM),'varied'],env=env,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        recs=R.decode_stdout(p.stdout);self.assertEqual(len(recs),128)
        max_error=0.
        for r in recs:
            logits=torch.tensor(r['logits'])[None];legal=torch.tensor(r['legal'],dtype=torch.bool)[None]
            got,valid=L.selected_logp(logits,legal,torch.tensor([r['chosen']]))
            self.assertTrue(valid[0]);max_error=max(max_error,abs(float(got[0])-r['logp']))
            pick,lp=masked_sample(r['logits'],r['legal'],np.float32((r['K']%7)/7))
            self.assertEqual(pick,r['chosen']);self.assertAlmostEqual(float(lp),r['logp'],places=6)
        self.assertLess(max_error,2e-6)

class ExecutionDataset(unittest.TestCase):
    def fixture(self,**changes):
        from nfs.policy import observation as obs
        d=record(obs_hash=obs.OBS_SCHEMA_HASH,**changes)
        ctx={k:d[k] for k in ('obs_hash','action_hash','round','champion','snapshot')}
        ctx.update(kind='context',decision_id=0,raw=np.zeros(obs.OBS_DIM,dtype='<f4').tobytes())
        return ctx,d,ack(d)

    def build(self,records):
        from nfs.policy.dataset import build_dataset
        return build_dataset(records,episode_id='synthetic_episode_1',group_id='synthetic_group_1',synthetic=True,expected_action_hash=0xabcdef01)

    def test_only_acknowledged_selected_samples_enter_ratio(self):
        c,d,a=self.fixture();ds=self.build([c,d,a]);self.assertTrue(ds.rows[0]['ppo_mask'])
        for kwargs in (dict(outcome=0),dict(outcome=3),dict(outcome=4,source=3),dict(executed_id=10),dict(reason=11)):
            self.assertFalse(self.build([c,d,ack(d,**kwargs)]).rows[0]['ppo_mask'])
        self.assertFalse(self.build([c,d]).rows[0]['ppo_mask'])
        self.assertFalse(self.build([d,a]).rows[0]['ppo_mask'])
        c,d,a=self.fixture(flags=R.DEFINED_OPTION,option_id=900)
        self.assertTrue(self.build([c,d,ack(d,outcome=2)]).rows[0]['ppo_mask'])
        c,d,a=self.fixture();self.assertFalse(self.build([c,d,ack(d,outcome=2)]).rows[0]['ppo_mask'])

    def test_teacher_optional_outside_and_real_executed_imitation(self):
        c,d,a=self.fixture(teacher=2,teacher_id=30)
        self.assertTrue(self.build([c,d,a]).rows[0]['imitation_mask'])
        c,d,a=self.fixture(teacher=0,teacher_id=10)
        self.assertFalse(self.build([c,d,a]).rows[0]['imitation_mask'])
        c,d,a=self.fixture(teacher_id=999)
        ds=self.build([c,d,a]);self.assertFalse(ds.rows[0]['imitation_mask']);self.assertEqual(ds.counts['teacher_outside_candidates'],1)
        c,d,a=self.fixture();self.assertEqual(self.build([c,d,a]).counts['teacher_absent'],1)

    def test_argmax_continuation_safety_and_fallback_exclusions(self):
        for source,sampled in ((0,0),(1,0),(2,0),(3,0)):
            c,d,a=self.fixture(source=source,sampled=sampled,logp=0)
            ds=self.build([c,d,a]);self.assertFalse(ds.rows[0]['ppo_mask'])
        c,d,a=self.fixture(reason=3);self.assertFalse(self.build([c,d,a]).rows[0]['ppo_mask'])

    def test_stream_schema_duplicates_and_logprob_integrity(self):
        from nfs.policy.dataset import DatasetError,build_dataset
        c,d,a=self.fixture()
        for recs in ([c,c,d,a],[c,d,d,a],[c,d,a,a]):
            with self.assertRaises(DatasetError):self.build(recs)
        with self.assertRaises(DatasetError):self.build([c,d,ack(d,snapshot=2)])
        d['logp']=-2
        with self.assertRaises(DatasetError):self.build([c,d,a])
        with self.assertRaises(DatasetError):build_dataset([],episode_id='x',group_id='y',synthetic=True,engine_version='1.0.2')

    def test_pending_ack_final_ack_and_option_intervals(self):
        from nfs.policy.dataset import option_intervals
        c,d,a=self.fixture(flags=R.OPTION_START|R.DEFINED_OPTION,option_id=7)
        ds=self.build([c,d,ack(d,outcome=0),a]);self.assertFalse(ds.rows[0]['ppo_mask'])
        self.assertEqual(ds.counts['excluded_option_unclosed'],1)
        d2=copy.deepcopy(d);d2.update(decision_id=43,round=9,source=1,sampled=0,logp=0,flags=R.OPTION_END|R.DEFINED_OPTION)
        ds=self.build([c,d,a,d2,ack(d2,outcome=2)])
        spans=option_intervals(ds.rows);self.assertEqual(spans[0]['duration_rounds'],2);self.assertTrue(spans[0]['closed'])
        self.assertFalse(ds.rows[1]['ppo_mask'])

    def test_collation_group_split_and_checksum_artifact(self):
        from nfs.policy.dataset import collate,split_by_group,assert_disjoint_groups,save_dataset,load_arrays,DatasetError
        c,d,a=self.fixture();ds=self.build([c,d,a]);batch=collate(ds.rows)
        self.assertEqual(tuple(batch['feat'].shape),(1,16,12));self.assertEqual(int(batch['teacher'][0]),-1)
        train,val=split_by_group(ds.rows);self.assertEqual(len(train)+len(val),1)
        with self.assertRaises(DatasetError):assert_disjoint_groups(ds.rows,ds.rows)
        TMP.mkdir(parents=True,exist_ok=True);path,_=save_dataset(ds,TMP/'synthetic_dataset.npz')
        arrays,meta=load_arrays(path);self.assertTrue(meta['synthetic']);np.testing.assert_array_equal(arrays['feat'],batch['feat'].numpy())
        path.write_bytes(path.read_bytes()+b'corrupt')
        with self.assertRaises(DatasetError):load_arrays(path)

class DirectLosses(unittest.TestCase):
    def test_masked_logp_cpp_formula_and_empty_rows(self):
        logits=torch.tensor([[.25,99.,1.25],[0.,0.,0.]],requires_grad=True);legal=torch.tensor([[1,0,1],[0,0,0]],dtype=torch.bool)
        lp,valid=L.selected_logp(logits,legal,torch.tensor([2,-1]))
        self.assertAlmostEqual(float(lp[0].detach()),-.3132616875,places=6);self.assertEqual(valid.tolist(),[True,False])
        loss,_=L.imitation_loss(logits,legal,torch.tensor([2,-1]),imitation_mask=torch.ones(2,dtype=torch.bool));loss.backward()
        self.assertEqual(float(logits.grad[0,1]),0);self.assertTrue(torch.isfinite(logits.grad).all())

    def test_ppo_excludes_unexecuted_rows_and_finite_empty_gradient(self):
        logits=torch.tensor([[.25,0.,1.25],[.25,0.,1.25]],requires_grad=True);legal=torch.tensor([[1,0,1],[1,0,1]],dtype=torch.bool)
        chosen=torch.tensor([2,0]);old=torch.tensor([-.3132616875,-1.3132616875]);adv=torch.tensor([1.,10000.])
        loss,metrics=L.ppo_loss(logits,legal,chosen,old,adv,ppo_mask=torch.tensor([True,False]))
        self.assertEqual(metrics['samples'],1);self.assertAlmostEqual(float(loss.detach()),-1.,places=6);loss.backward()
        self.assertEqual(float(logits.grad[1].abs().sum()),0)
        x=torch.full((2,3),float('-inf'),requires_grad=True)
        z,m=L.ppo_loss(x,torch.zeros(2,3,dtype=torch.bool),chosen,old,adv,ppo_mask=torch.ones(2,dtype=torch.bool));z.backward()
        self.assertEqual(m['samples'],0);self.assertTrue(torch.isfinite(x.grad).all())

    def test_actual_direct_model_synthetic_gradient_and_no_teacher_input(self):
        from nfs.policy.model import DirectPolicyNet,load_config,init_untrained,HEAD_NAMES
        cfg=load_config('policy_v2',action_hashes={n:100+i for i,n in enumerate(HEAD_NAMES)},action_schema_hash=42)
        model=init_untrained(DirectPolicyNet(cfg),seed=9)
        torch.manual_seed(3);obs=torch.randn(3,cfg['obs']['obs_dim']);feat=torch.randn(3,4,12)
        mask=torch.tensor([[1,0,1,1],[1,1,0,1],[1,1,1,1]],dtype=torch.bool)
        logits=model(obs,'move',feat,mask,torch.tensor([0,1,3]));teacher=torch.tensor([2,-1,0])
        loss,m=L.imitation_loss(logits,mask,teacher,imitation_mask=torch.tensor([True,False,True]));loss.backward()
        self.assertEqual(m['samples'],2);self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0 for p in model.parameters()))
        self.assertTrue(all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters()))

    def test_smdp_and_critic(self):
        got=L.smdp_returns([1,2],[3,2],gamma=.9,bootstrap=4)
        self.assertAlmostEqual(got[1],2+.9**2*4);self.assertAlmostEqual(got[0],1+.9**3*got[1])
        v=torch.tensor([1.,2.],requires_grad=True)
        loss=L.critic_loss(v,torch.tensor([3.,20.]),mask=torch.tensor([1,0],dtype=torch.bool));loss.backward()
        self.assertEqual(v.grad.tolist(),[-4.,0.])
        advantages,returns=L.smdp_gae([1,2],[.5,.25],[.25,4],[3,2],[False,True],gamma=.9,gae_lambda=.8)
        self.assertAlmostEqual(advantages[1],1.75)
        self.assertAlmostEqual(advantages[0],1+.9**3*.25-.5+(.9*.8)**3*1.75)
        self.assertAlmostEqual(returns[0],.5+advantages[0])

if __name__=='__main__':unittest.main()
