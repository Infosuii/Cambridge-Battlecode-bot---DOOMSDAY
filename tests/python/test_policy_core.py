"""Independent synthetic core scenarios and actual-schema NFS2 joins. No games, training or optimizer calls."""
from pathlib import Path
import json
import os
import subprocess
import unittest
import numpy as np
import torch
from nfs.policy.model import load_config,DirectPolicyNet,init_untrained
from nfs.policy.export import export_model
from nfs.policy import records as R
from nfs.policy import candidates as C
from nfs.policy import observation as O
from nfs.policy import dataset as D

ROOT=Path(__file__).resolve().parents[2]
TMP=ROOT/"artifacts/tmp/policy_core"


class TestPolicyCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TMP.mkdir(parents=True,exist_ok=True)
        cls.cfg=load_config("policy_v2")
        cls.random=init_untrained(DirectPolicyNet(cls.cfg),seed=314159,zero_logits=False)
        zero=init_untrained(DirectPolicyNet(cls.cfg),seed=314159,zero_logits=True)
        for name,model in (("core_random",cls.random),("core_zero",zero)):
            export_model(model,name,TMP,"untrained",dict(synthetic=True,source="independent pure runtime protocol tests"))
        cxx=json.loads((ROOT/"config/paths.json").read_text())["native_cxx"]
        cls.env=dict(os.environ,TMP=str(TMP),TEMP=str(TMP),PATH=str(Path(cxx).parent)+os.pathsep+os.environ.get("PATH",""))
        cls.exe=TMP/"core.exe"
        p=subprocess.run([cxx,"-std=c++20","-O2","-ffp-contract=off","-I"+str(ROOT/"bot/src"),"-I"+str(TMP),
                          str(ROOT/"tests/cpp/test_policy_core.cpp"),"-o",str(cls.exe)],env=cls.env,capture_output=True,text=True)
        if p.returncode:raise AssertionError(p.stdout+p.stderr)

    def run_mode(self,mode,*args):
        p=subprocess.run([str(self.exe),mode,*map(str,args)],env=self.env,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        return p.stdout

    def test_warmup_and_all_checksum_rejections(self):self.run_mode("warmup")
    def test_budget_capture_gating_and_real_candidate_spend(self):self.run_mode("budget")
    def test_snapshot_cache_and_explicit_action_invalidation(self):self.run_mode("cache")
    def test_ticket_replay_overlap_and_required_matching_ack(self):self.run_mode("tickets")
    def test_ticket_cannot_change_reserved_capacity_or_head(self):self.run_mode("ticket_integrity")
    def test_execution_ack_cannot_forge_selected_action_or_identity(self):self.run_mode("ack_integrity")

    def dataset(self,text):
        recs=R.decode_stdout(text,expected_obs_hash=O.OBS_SCHEMA_HASH,expected_action_hash=C.ACTION_SCHEMA_HASH)
        ds=D.build_dataset(recs,episode_id="synthetic_core_episode",group_id="synthetic_core_group",synthetic=True,
                           expected_action_hash=C.ACTION_SCHEMA_HASH)
        return recs,ds

    def test_sampled_behavior_logp_true_execution_and_dataset_roundtrip(self):
        text=self.run_mode("sample_records");recs,ds=self.dataset(text)
        self.assertEqual(len(ds.rows),8)
        self.assertEqual(ds.counts["ppo_eligible"],6)
        self.assertEqual(ds.counts["excluded_missing_ack"],1)
        self.assertEqual(ds.counts["imitation_eligible"],0)
        batch=D.collate(ds.rows);maxerr=0.
        for i,row in enumerate(ds.rows):
            d=row["decision"];K=d["K"];head=R.HEADS[d["head"]]
            self.assertEqual(d["sampled"],1);self.assertEqual(d["teacher"],-1);self.assertNotEqual(d["chosen"],0)
            with torch.no_grad():
                z=self.random(batch["obs"][i:i+1],head,batch["feat"][i:i+1,:K],batch["legal"][i:i+1,:K],batch["context"][i:i+1])
                lp=torch.log_softmax(z,1)[0,d["chosen"]]
            finite=np.isfinite(d["logits"])
            np.testing.assert_allclose(z.numpy()[0,finite],d["logits"][finite],rtol=2e-5,atol=2e-6)
            maxerr=max(maxerr,abs(float(lp)-d["logp"]))
            self.assertEqual(d["fuel"]["candidate"],123);self.assertEqual(d["fuel"]["observation"],50)
        self.assertLess(maxerr,2e-6)
        path,_=D.save_dataset(ds,TMP/"synthetic_core_records.npz")
        arrays,meta=D.load_arrays(path)
        self.assertTrue(meta["synthetic"]);np.testing.assert_array_equal(arrays["behavior_logp"],batch["behavior_logp"].numpy())

    def test_argmax_records_are_explicitly_not_on_policy_samples(self):
        _,ds=self.dataset(self.run_mode("argmax_records"))
        self.assertEqual(ds.counts["ppo_eligible"],0)
        for row in ds.rows:
            d=row["decision"];self.assertEqual(d["sampled"],0);self.assertEqual(d["logp"],0)
            self.assertEqual(d["chosen"],int(np.argmax(d["logits"])))

    def test_textual_flush_fuel_boundary_and_record_bytes(self):
        path=TMP/"one_context.nfs2"
        self.run_mode("flush",path)
        raw=path.read_bytes();self.assertTrue(raw.startswith(b"NFS2 "));self.assertTrue(raw.endswith(b"\n"))
        rec=R.decode_line(raw.decode())
        self.assertEqual(rec["kind"],"context");self.assertEqual(len(rec["raw"]),O.OBS_DIM*4)


if __name__=="__main__":unittest.main()
