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
BASE = dict(layout=4, action_schema="target11-v1", reward_spec="test", run_ns="test", sampling="complete",
            policy={"name": "t", "wasm_sha256": "0" * 64, "build": "debug", "flags": []},
            engine={"cambc": "4.0.0", "engine": "2.0.0"})


def episode(n_bodies=2, rows_per_body=3, status="terminated", bad=None, boundary=False):
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
            r["boundary"].append(0)
            r["bootstrap_valid"].append(1 if last and boundary else 0)
        if boundary:  # observation-only row at the cut
            for c in r:
                if c in ("x_fresh", "x_stale"):
                    r[c] += r[c][-nf:]
                elif c == "mask":
                    r[c] += [0] * na
                elif r[c]:  # `episode` is filled in by the writer
                    r[c].append(r[c][-1])
            r["action"][-1], r["weight"][-1], r["has_logp"][-1], r["logp"][-1] = -1, 0.0, 0, math.nan
            r["boundary"][-1], r["bootstrap_valid"][-1], r["truncated"][-1], r["reset"][-1] = 1, 0, 0, 0
            r["feat_round"][-1] = r["act_round"][-1] = 30
    if bad:
        bad(r)
    meta = dict(key=f"k{status}{id(r)}", map_file="m", map_hash="abc", opponent={"name": "v92", "wasm_sha256": "1" * 64},
                side="A", seed="1", status=status, our_team="teamA", outcome="teamA", rounds_completed=30,
                reward_complete=True)
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

    def test_truncated_bootstrap_needs_boundary_row(self):
        man, cols = self.roundtrip(episode(status="truncated", boundary=True))
        self.assertEqual(C.validate(man, cols), [])
        self.assertTrue(man["episodes"][0]["ppo_eligible"])
        def no_row(r):  # claims a bootstrap but has no final observation
            r["bootstrap_valid"][2] = 1
        man, cols = self.roundtrip(episode(status="truncated", bad=no_row))
        self.assertTrue(any("no boundary row follows" in e for e in C.validate(man, cols)))

    def test_log_cut_never_bootstraps_or_trains(self):
        man, cols = self.roundtrip(episode(status="truncated_log", boundary=True))
        errs = C.validate(man, cols)
        self.assertTrue(any("may not bootstrap" in e for e in errs))
        self.assertFalse(man["episodes"][0]["ppo_eligible"])

    def test_subsampled_shard_is_not_ppo_data(self):
        w = C.ShardWriter(self.d, dict(BASE, sampling="subsampled"))
        meta, rows = episode()
        w.add_episode(meta, rows)
        man, cols = C.load_shard(w.flush(), use_numpy=False)
        self.assertEqual(C.validate(man, cols), [])
        self.assertFalse(man["episodes"][0]["ppo_eligible"])

    def test_split_is_per_map(self):
        self.assertEqual(C.episode_split("abc"), C.episode_split("abc"))
        self.assertIn(C.episode_split("xyz"), ("train", "dev"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
