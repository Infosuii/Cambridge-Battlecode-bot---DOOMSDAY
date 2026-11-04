"""Contract self-tests (stdlib only): python tools/rl_env_1104/test_contract.py"""
import math
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contract as C  # noqa: E402

LAY = C.LAYOUTS[4]
BASE = dict(layout=4, action_schema="target11-v1", reward_spec="test", run_ns="test",
            policy={"name": "t", "wasm_sha256": "0" * 64, "build": "debug", "flags": []},
            engine={"cambc": "4.0.0", "engine": "2.0.0"})


def episode(n_bodies=2, rows_per_body=3, status="terminated", bad=None):
    nf, na = LAY.nf, 11
    r = {c: [] for c in C.required_columns(BASE)}
    for b in range(n_bodies):
        for k in range(rows_per_body):
            x = [0] * nf
            x[LAY.self_id_index] = b
            for g in range(3):  # three valid camp rows
                x[LAY.offset("c") + g * LAY.width("c")] = 1
            last = k == rows_per_body - 1
            m = [1, 1, 1] + [0] * 7 + [1]
            r["x_fresh"] += x
            r["x_stale"] += [0] * nf
            r["has_stale"].append(0)
            r["feat_round"].append(10 * k)
            r["stale_round"].append(-1)
            r["act_round"].append(10 * k)
            r["body_id"].append(b)
            r["slot"].append(b)
            r["mask"] += m
            r["action"].append(k % 3)
            r["teacher_action"].append(0)
            r["executed"].append(-1)
            r["logp"].append(-0.5)
            r["has_logp"].append(1)
            r["weight"].append(1.0)
            r["changed"].append(1)
            r["reset"].append(1 if k == 0 else 0)
            r["reward"].append(0.0)
            r["dt_rounds"].append(10)
            r["terminated"].append(1 if last and status == "terminated" else 0)
            r["truncated"].append(1 if last and status != "terminated" else 0)
    if bad:
        bad(r)
    meta = dict(key=f"k{status}{id(r)}", map_file="m", map_hash="abc", opponent={"name": "v92", "wasm_sha256": "1" * 64},
                side="A", seed="1", status=status, our_team="teamA", outcome="teamA", rounds_completed=30)
    return meta, r


class ContractTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def roundtrip(self, *eps):
        w = C.ShardWriter(self.d, BASE)
        for meta, rows in eps:
            w.add_episode(meta, rows)
        path = w.flush()
        return C.load_shard(path, use_numpy=False)

    def test_layout_sizes(self):
        self.assertEqual(C.LAYOUTS[2].nf, 500)
        self.assertEqual(C.LAYOUTS[4].nf, 556)

    def test_valid_roundtrip(self):
        man, cols = self.roundtrip(episode(), episode(status="truncated"))
        self.assertEqual(C.validate(man, cols), [])
        self.assertEqual(man["rows"], 12)
        self.assertEqual(len(cols["x_fresh"]), 12 * 556)

    def test_illegal_action(self):
        man, cols = self.roundtrip(episode(bad=lambda r: r["action"].__setitem__(0, 5)))
        self.assertTrue(any("not legal" in e for e in C.validate(man, cols)))

    def test_fabricated_logp(self):
        def bad(r):
            r["has_logp"][1] = 0  # logp still set: a fabricated probability for a deterministic row
        man, cols = self.roundtrip(episode(bad=bad))
        self.assertTrue(any("logp/has_logp" in e for e in C.validate(man, cols)))
        def ok(r):
            r["has_logp"][1], r["logp"][1] = 0, math.nan
        man, cols = self.roundtrip(episode(bad=ok))
        self.assertEqual(C.validate(man, cols), [])

    def test_death_is_not_terminal(self):
        man, cols = self.roundtrip(episode(bad=lambda r: r["terminated"].__setitem__(0, 1)))
        self.assertTrue(any("death is not an episode end" in e for e in C.validate(man, cols)))

    def test_body_id_must_match_features(self):
        man, cols = self.roundtrip(episode(bad=lambda r: r["body_id"].__setitem__(0, 7)))
        self.assertTrue(any("self-id" in e for e in C.validate(man, cols)))

    def test_resume_keys_and_no_layout_mixing(self):
        meta, rows = episode()
        w = C.ShardWriter(self.d, BASE)
        w.add_episode(meta, rows)
        w.flush()
        self.assertIn(meta["key"], C.ShardWriter(self.d, BASE).done_keys())
        w2 = C.ShardWriter(os.path.join(self.d, "l2"), dict(BASE, layout=2))
        m2, r2 = episode()
        with self.assertRaises(ValueError):  # layout-4 rows into a layout-2 writer: wrong width
            w2.add_episode(m2, r2)
        with self.assertRaises(ValueError):
            list(C.iter_shards(self.d, layout=2))

    def test_split_is_per_map(self):
        self.assertEqual(C.episode_split("abc"), C.episode_split("abc"))
        self.assertIn(C.episode_split("xyz"), ("train", "dev"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
