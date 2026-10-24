"""Synthetic direct-model shapes, numeric/native parity, semantic-version and export round-trip tests."""
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

from nfs.policy.model import DirectPolicyNet,load_config,init_untrained,HEAD_IDS
from nfs.policy import export as E

ROOT=Path(__file__).resolve().parents[2]
TMP=ROOT/"artifacts/tmp/v2_model"


def synthetic_config():
    return load_config("policy_v2",action_hashes={name:100+hid for name,hid in HEAD_IDS.items()},action_schema_hash=0x1234abcd)


class TestPolicyModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TMP.mkdir(parents=True,exist_ok=True)
        cls.cfg=synthetic_config()
        cls.model=init_untrained(DirectPolicyNet(cls.cfg),seed=20261024,zero_logits=False)
        cls.export_dir=TMP/"native_export"
        E.export_model(cls.model,"synthetic_v2",cls.export_dir,"untrained",dict(synthetic=True,source="synthetic parity fixture"))
        cls.exe=TMP/"model.exe"
        compiler=os.environ.get("NFS_GXX", "C:/msys64/ucrt64/bin/g++.exe")
        cls.env=dict(os.environ,PATH=str(Path(compiler).parent)+os.pathsep+os.environ.get("PATH",""),TMP=str(TMP),TEMP=str(TMP))
        p=subprocess.run([compiler,"-std=c++20","-O2","-ffp-contract=off","-I",str(ROOT/"bot/src"),"-I",str(cls.export_dir),
                          str(ROOT/"tests/cpp/test_policy_model.cpp"),"-o",str(cls.exe)],capture_output=True,text=True,env=cls.env)
        if p.returncode: raise AssertionError(p.stdout+p.stderr)

    def test_native_descriptor_and_failure_checks(self):
        p=subprocess.run([str(self.exe),"checks"],capture_output=True,text=True,env=self.env)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertIn("0 failures",p.stdout)

    def test_cpp_torch_forward_parity_all_heads_contexts(self):
        rng=np.random.default_rng(20261024)
        payload=[]; expected=[]
        o=self.cfg["obs"]; D=o["obs_dim"]
        for name,hid in HEAD_IDS.items():
            for context in range(4):
                for K in (1,3,8,16):
                    obs=rng.normal(size=D).astype("<f4")
                    # Include zero/max and mixed entity masks, preserving the runtime pool semantics.
                    a=o["self_global_dim"]+o["ally_rows"]*o["ally_dim"]
                    e=a+o["ally_rows"]+o["enemy_rows"]*o["enemy_dim"]
                    obs[a:a+o["ally_rows"]]=rng.integers(0,2,o["ally_rows"])
                    obs[e:e+o["enemy_rows"]]=rng.integers(0,2,o["enemy_rows"])
                    feat=rng.normal(size=(K,12)).astype("<f4"); legal=(rng.random(K)>.3).astype("u1"); legal[-1]=1
                    payload.append(struct.pack("<III",hid,context,K)+obs.tobytes()+feat.tobytes()+legal.tobytes())
                    with torch.no_grad():
                        h=self.model.encode(torch.from_numpy(obs[None]))
                        z=self.model.head_logits(name,h,torch.from_numpy(feat[None]),torch.from_numpy(legal[None]),torch.tensor([context]))
                    expected.append((K,h.numpy()[0],z.numpy()[0]))
        p=subprocess.run([str(self.exe)],input=b"".join(payload),capture_output=True,env=self.env)
        self.assertEqual(p.returncode,0,p.stderr.decode(errors="replace"))
        offset=0; maxerr=0.
        for K,h,z in expected:
            ok,=struct.unpack_from("<I",p.stdout,offset);offset+=4;self.assertEqual(ok,1)
            ch=np.frombuffer(p.stdout,"<f4",len(h),offset);offset+=len(h)*4
            cz=np.frombuffer(p.stdout,"<f4",K,offset);offset+=K*4
            np.testing.assert_allclose(ch,h,rtol=2e-5,atol=2e-6)
            np.testing.assert_array_equal(np.isfinite(cz),np.isfinite(z))
            finite=np.isfinite(z);np.testing.assert_allclose(cz[finite],z[finite],rtol=2e-5,atol=2e-6)
            maxerr=max(maxerr,float(np.max(np.abs(cz[finite]-z[finite]))))
            self.assertEqual(int(np.argmax(cz)),int(np.argmax(z)))
        self.assertEqual(offset,len(p.stdout)); self.assertLess(maxerr,2e-6)

    def test_roundtrip_and_deterministic_export(self):
        before=self.model.state_dict()
        loaded=E.load_model(self.export_dir,expected_obs=self.cfg["obs"]["obs_schema_hash"],expected_action=0x1234abcd)
        for key,t in before.items(): self.assertTrue(torch.equal(t,loaded.state_dict()[key]),key)
        other=TMP/"deterministic"
        E.export_model(self.model,"synthetic_v2",other,"untrained",dict(synthetic=True,source="synthetic parity fixture"))
        for filename in ("weights.f32","manifest.json","nn_policy_weights_synthetic_v2.h"):
            self.assertEqual((self.export_dir/filename).read_bytes(),(other/filename).read_bytes())

    def test_zero_logits_control_ties_masks_permutations(self):
        zero=init_untrained(DirectPolicyNet(self.cfg),seed=2,zero_logits=True)
        x=torch.zeros(2,self.cfg["obs"]["obs_dim"]); feat=torch.randn(2,5,12)
        legal=torch.tensor([[0,1,1,0,1],[1,0,1,1,1]],dtype=torch.bool)
        z=zero(x,"move",feat,legal,torch.tensor([0,3]))
        self.assertEqual(z.argmax(1).tolist(),[1,0])
        self.assertTrue(torch.equal(z[legal],torch.zeros_like(z[legal])))
        perm=torch.tensor([4,2,0,1,3])
        with torch.no_grad():
            h=self.model.encode(x)
            a=self.model.head_logits("move",h,feat,legal)
            b=self.model.head_logits("move",h,feat[:,perm],legal[:,perm])
        self.assertTrue(torch.equal(a[:,perm],b))

    def test_direct_logits_are_not_teacher_residual_bounded(self):
        m=init_untrained(DirectPolicyNet(self.cfg),1)
        with torch.no_grad(): m.heads["bank"]["w2"].zero_();m.heads["bank"]["b2"].fill_(37)
        z=m(torch.zeros(1,self.cfg["obs"]["obs_dim"]),"bank",torch.zeros(1,2,12),torch.ones(1,2,dtype=torch.bool))
        self.assertEqual(z.tolist(),[[37,37]])
        with self.assertRaises(TypeError):m.head_logits("bank",torch.zeros(1,8),torch.zeros(1,2,12),torch.ones(1,2),prior=torch.ones(1,2))

    def test_reject_v1_semantics_even_shapes_match(self):
        for key,value in [("interpretation_version",1),("policy_kind","teacher_residual"),("kernel_arch_version",2)]:
            cfg=copy.deepcopy(self.cfg);cfg[key]=value
            with self.assertRaises(ValueError):DirectPolicyNet(cfg)
        raw=json.loads((ROOT/"configs/model/fs_v1.json").read_text())
        with self.assertRaises(ValueError):load_config(raw)

    def test_installed_candidate_schema_hashes_resolve(self):
        cfg=load_config("policy_v2")
        schema=json.loads((ROOT/"schemas/policy_v2.json").read_text())
        self.assertEqual(cfg["action_schema_hash"],schema["action_schema_hash"])
        self.assertEqual({h["name"]:h["action_hash"] for h in cfg["heads"]},
                         {h["name"]:h["action_hash"] for h in schema["heads"]})

    def test_stale_stored_schema_hash_and_invalid_dimensions_rejected(self):
        raw=json.loads((ROOT/"configs/model/policy_v2.json").read_text())
        schema=json.loads((ROOT/"schemas/policy_v2.json").read_text())
        schema["heads"][0]["features"][0]["description"]+=" semantic change"
        altered=TMP/"stale_schema.json";altered.write_text(json.dumps(schema))
        raw["action_schema"]=str(altered)
        with self.assertRaisesRegex(ValueError,"head schema hash"):load_config(raw)
        bad=copy.deepcopy(self.cfg);bad["obs"]["ally_rows"]=-1
        with self.assertRaises(ValueError):DirectPolicyNet(bad)
        bad=copy.deepcopy(self.cfg);bad["heads"][0]["R"]=float("nan")
        with self.assertRaises(ValueError):DirectPolicyNet(bad)

    def test_reject_nonfinite_corrupt_schema_and_header(self):
        scratch=TMP/"corrupt"
        def fresh():
            E.export_model(self.model,"synthetic_v2",scratch,"untrained",dict(synthetic=True))
        fresh(); data=bytearray((scratch/"weights.f32").read_bytes());data[-1]^=1;(scratch/"weights.f32").write_bytes(data)
        with self.assertRaisesRegex(E.ExportError,"checksum"):E.load_blob(scratch)
        fresh();data=bytearray((scratch/"weights.f32").read_bytes());data[:4]=struct.pack("<f",float("nan"));(scratch/"weights.f32").write_bytes(data)
        with self.assertRaisesRegex(E.ExportError,"NaN"):E.load_blob(scratch)
        fresh();hp=scratch/"nn_policy_weights_synthetic_v2.h";hp.write_text(hp.read_text()+"// tampered\n")
        with self.assertRaisesRegex(E.ExportError,"header"):E.load_blob(scratch)
        fresh()
        with self.assertRaisesRegex(E.ExportError,"action schema"):E.load_blob(scratch,expected_action=19)
        man=json.loads((scratch/"manifest.json").read_text());man["interpretation_version"]=1;(scratch/"manifest.json").write_text(json.dumps(man))
        with self.assertRaisesRegex(E.ExportError,"v1"):E.load_blob(scratch)
        model=copy.deepcopy(self.model)
        with torch.no_grad():model.heads["shop"]["b2"].fill_(float("inf"))
        with self.assertRaisesRegex(E.ExportError,"NaN/Inf"):E.export_model(model,"bad",scratch,"untrained",{})

    def test_padding_invariance_and_invalid_inputs(self):
        o=self.cfg["obs"];x=torch.randn(1,o["obs_dim"])
        a=o["self_global_dim"]+o["ally_rows"]*o["ally_dim"]; e=a+o["ally_rows"]+o["enemy_rows"]*o["enemy_dim"]
        x[:,a:a+o["ally_rows"]]=0;x[:,e:e+o["enemy_rows"]]=0
        y=x.clone();y[:,o["self_global_dim"]:a]=123;y[:,a+o["ally_rows"]:e]=-345
        self.assertTrue(torch.equal(self.model.encode(x),self.model.encode(y)))
        h=torch.zeros(1,self.cfg['encoder']['ctx']);f=torch.zeros(1,2,12);mask=torch.ones(1,2,dtype=torch.bool)
        f[0,0,0]=float("nan")
        with self.assertRaisesRegex(ValueError,"nonfinite"):self.model.head_logits("shop",h,f,mask)
        with self.assertRaisesRegex(ValueError,"context"):self.model.head_logits("shop",h,torch.zeros_like(f),mask,torch.tensor([4]))


if __name__=="__main__":unittest.main()
