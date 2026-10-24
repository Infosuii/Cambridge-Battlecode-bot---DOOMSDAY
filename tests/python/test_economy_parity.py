"""Synthetic candidate parity and legality invariants; no game data or parameter updates."""
from pathlib import Path
import json
import os
import random
import subprocess
import unittest
import numpy as np
from nfs.heads import economy as E

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "tmp" / "F2" / "native"


def values(x):
    return " ".join(str(int(v)) if isinstance(v, (bool, E.BuyKind)) else str(v) for v in vars(x).values())


class TestEconomyParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        OUT.mkdir(parents=True, exist_ok=True)
        cls.exe = OUT / "economy.exe"
        compiler = os.environ.get("NFS_GXX", "C:/msys64/ucrt64/bin/g++.exe")
        cls.native_env = dict(os.environ)
        cls.native_env["PATH"] = str(Path(compiler).parent) + os.pathsep + os.environ.get("PATH", "")
        p = subprocess.run([compiler, "-std=c++20", "-O2", "-DNN_HOST_TEST", "-I", str(ROOT / "bot/src"),
                            str(ROOT / "tests/cpp/test_economy_parity.cpp"), str(ROOT / "bot/src/nn_economy.cpp"),
                            "-o", str(cls.exe)], capture_output=True, text=True, env=cls.native_env)
        if p.returncode:
            raise AssertionError(p.stdout + p.stderr)

    def test_synthetic_cpp_python_bit_exact(self):
        rng = random.Random(20261024)
        cases = []
        for i in range(400):
            s = E.State(np.float32(rng.random()*2000), np.float32(1+rng.random()*2500),
                        rng.randrange(300), rng.randrange(1200), rng.randrange(2001), rng.randrange(1200), rng.randrange(1200))
            if i % 2:
                # Force/win/late imply the computed teacher chooses to bank.
                flags = [bool(rng.getrandbits(1)) for _ in range(9)]
                flags[0] = flags[0] or any(flags[2:5])
                t = E.BankTerms(*flags, rng.randrange(128), rng.choice([-1, rng.randrange(128)]))
                line = "bank " + values(s) + " " + values(t)
                expected = E.build_bank(s, t)
            else:
                teacher = E.Buy(E.BuyKind.plan, rng.randrange(0,42,2), rng.randrange(10), rng.randrange(600), rng.randrange(50))
                options = [E.Buy(rng.choice([E.BuyKind.shard, E.BuyKind.consumable]), rng.randrange(42),
                                 1, rng.choice([10,30]), rng.randrange(50), bool(rng.getrandbits(1))) for _ in range(rng.randrange(25))]
                line = "shop " + values(s) + " " + values(teacher) + " " + str(len(options)) + " " + " ".join(values(b) for b in options)
                expected = E.build_shop(s, teacher, options)
            cases.append((line, expected))
        p = subprocess.run([str(self.exe)], input="\n".join(x[0] for x in cases)+"\n", capture_output=True,
                           text=True, env=self.native_env)
        self.assertEqual(p.returncode, 0, p.stderr)
        lines = p.stdout.splitlines()
        self.assertEqual(len(lines), len(cases))
        for line, (_, expected) in zip(lines, cases):
            raw = line.split(); k, f, context = map(int, raw[:3]); self.assertEqual((k,f,context), (expected["K"],20,0))
            metadata = np.asarray(raw[3:3+3*k], dtype=np.float64).reshape(k,3)
            np.testing.assert_array_equal(metadata[:,0].astype(np.uint32), expected["id"])
            np.testing.assert_array_equal(metadata[:,1], expected["legal"])
            np.testing.assert_array_equal(metadata[:,2].astype(np.float32), expected["prior"])
            cpp = np.asarray(raw[3+3*k:], dtype=np.float32).reshape(k,f)
            np.testing.assert_array_equal(cpp.view(np.uint32), expected["feat"].view(np.uint32))

    def test_hard_bank_priorities_and_routes(self):
        s = E.State(gems=100)
        t = E.BankTerms(go=True, safe=True, wins=True, dist=14, raw_dist=8)
        d = E.build_bank(s,t)
        self.assertEqual(d["id"].tolist(), [2,1]); self.assertTrue(d["legal"].all())
        t.wins = False
        d = E.build_bank(s,t)
        self.assertEqual(d["id"].tolist(), [2,0,1]); self.assertEqual(E.teacher_label(d),0)
        t.raw_dist = -1
        self.assertEqual(E.build_bank(s,t)["id"].tolist(), [2,0])

    def test_shop_masks_dedup_bound_and_teacher_plan(self):
        s = E.State(gold=20)
        b = E.Buy(E.BuyKind.plan, 6, 8, 240)
        options = [E.Buy(E.BuyKind.shard,6,1,30), E.Buy(E.BuyKind.consumable,1,1,10),
                   E.Buy(E.BuyKind.consumable,1,1,10)]
        d = E.build_shop(s,b,options)
        self.assertEqual(d["id"].tolist(), [0,1,262,513]); self.assertEqual(d["legal"].tolist(), [1,1,0,1])
        many = [E.Buy(E.BuyKind.shard,i,1,30) for i in range(32)]
        self.assertEqual(E.build_shop(s,b,many)["K"],16)
        self.assertEqual(d["choices"][0].count,0)
        self.assertEqual(E.teacher_label(d),0)

    def test_teacher_plan_is_opaque_no_purchase_preview(self):
        s = E.State(hp=100, max_hp=200, gold=300)
        a = E.build_shop(s, E.Buy(E.BuyKind.plan, 6, 8, 240, 15), [])
        b = E.build_shop(s, E.Buy(E.BuyKind.shard, 32, 1, 30, 42, False), [])
        np.testing.assert_array_equal(a["feat"], b["feat"])
        opaque = a["choices"][0]
        self.assertEqual((opaque.kind, opaque.item, opaque.count, opaque.cost, opaque.owned, opaque.legal),
                         (E.BuyKind.plan,0,0,0,0,True))
        self.assertEqual(a["feat"][0,:12].tolist(), [1,0,1,0,0,0,0,0,0,0,0,0])

    def test_schemas_match_twins(self):
        for name, features in [("bank",E.BANK_FEATURES),("shop",E.SHOP_FEATURES)]:
            schema = json.loads((ROOT / f"schemas/heads/{name}.json").read_text())
            self.assertEqual(schema["F"],20); self.assertEqual([f["name"] for f in schema["features"]],list(features))
            self.assertEqual(len(features),20)


if __name__ == "__main__": unittest.main()
