"""E0 conformance tests on the real engine (task rl-env-collector-1104). Standard library only; ~2-3 min on 4 cores.

usage (repo root): python tools/rl_env_1104/e0_tests.py [-v]   (env E0_MAPS=comma list of pool map names to override)

  1 default_build_is_v92        recorder bot with CLRL_REC 0, release: same SHA-256 as bots/v92
  2 recorder_does_not_change_play  recorder (debug) vs v92 gives the same scores/outcome/length as release v92 vs v92
  3 deterministic_rows          the same game collected twice gives identical CLR1 rows
  4 recorder_fuel_cost          per-turn charged fuel of the recorder's team vs a v92 debug build: >= 95% of turns
                                identical (CLRL_REFUND refunds the debug_block guard); prints the residual. Known gap:
                                not yet exactly zero, so fuel-threshold branches in v92 can still differ on a few turns
  5 visibility                  enemy rows: visible => age 0; hidden => last-known position frozen since last sighting;
                                ally rows only from this body's own view
  6 lifecycle                   death is not an episode end; resets = first decision + one per death gap; validator OK
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import struct
import subprocess
import sys
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import collect as K  # noqa: E402
import contract as C  # noqa: E402

ROOT, CLI = K.ROOT, K.CLI
WORK = os.path.join(ROOT, "artifacts", "tmp", "rl_env_1104", "e0")
MAPS = [m.strip() for m in os.environ.get("E0_MAPS", "00corners,00crater").split(",") if m.strip()]
LAY = C.LAYOUTS[10]
E_OFF, E_W = LAY.offset("e"), LAY.width("e")


def run_game(a: str, b: str, mp: str, tag: str, release: bool) -> tuple:
    out = os.path.join(WORK, tag)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    st = os.path.join(out, "s.json")
    cmd = [CLI, "run", a, b, "--map", f"maps/ladder-pool/{mp}.map26a", "-o", out, "--statistics", st, "--json",
           "--log-limit", str(K.LOG_LIMIT)] + (["--release"] if release else [])
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=900)
    bundles = [os.path.join(out, n) for n in os.listdir(out) if n.endswith(".repl26a")]
    if r.returncode or not bundles or not os.path.exists(st):
        raise AssertionError(f"game {tag} failed: {r.stdout[-800:]} {r.stderr[-800:]}")
    with open(st, encoding="utf-8") as f:
        return bundles[0], json.load(f)


def team_file(bundle: str, name: str) -> bytes:
    with zipfile.ZipFile(bundle) as z:
        return z.read(name)


def scores(summary: dict) -> tuple:
    m = summary["match"]
    return (m["outcome"], m["roundsCompleted"], tuple(int(t["submittedGems"]) for t in summary["teams"]))


class E0(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(WORK, exist_ok=True)
        cls.rec, cls.rec_hash = K.prepare_recorder(WORK)  # CLRL_REC 1 copy
        cls.games = {}

    def game(self, a, b, mp, tag, release):
        key = (a, b, mp, release, tag)
        if key not in self.games:
            self.games[key] = run_game(a, b, mp, tag, release)
        return self.games[key]

    def test_1_default_build_is_v92(self):
        outs = {}
        for name, bot in (("v92", "bots/v92"), ("rec0", "bots/claude-rlenv-1104")):
            w = os.path.join(WORK, f"{name}.wasm")
            r = subprocess.run([CLI, "build", bot, "--release", "--output", w], cwd=ROOT, capture_output=True, text=True,
                               timeout=900)
            self.assertEqual(r.returncode, 0, r.stdout[-500:])
            outs[name] = K.sha256(w)
        self.assertEqual(outs["rec0"], outs["v92"])

    def test_2_recorder_does_not_change_play(self):
        for mp in MAPS:
            _, base = self.game("bots/v92", "bots/v92", mp, f"base-{mp}", True)
            _, rec = self.game(self.rec, "bots/v92", mp, f"recA-{mp}", False)
            self.assertEqual(scores(rec), scores(base), mp + " recorder as A")
            _, recb = self.game("bots/v92", self.rec, mp, f"recB-{mp}", False)
            self.assertEqual(scores(recb), scores(base), mp + " recorder as B")

    def test_3_deterministic_rows(self):
        mp = MAPS[0]
        b1, _ = self.game(self.rec, "bots/v92", mp, f"recA-{mp}", False)
        b2, _ = self.game(self.rec, "bots/v92", mp, f"recA2-{mp}", False)
        r1 = [l for l in team_file(b1, "team-a.stdout").decode("utf-8", "replace").splitlines() if l.startswith("CLR1 ")]
        r2 = [l for l in team_file(b2, "team-a.stdout").decode("utf-8", "replace").splitlines() if l.startswith("CLR1 ")]
        self.assertGreater(len(r1), 1000)
        self.assertEqual(r1, r2)

    def test_4_recorder_fuel_cost(self):
        def trace(bundle):
            d = team_file(bundle, "team-a.fuel")  # header (13 bytes: magic, version), then one u64 per turn
            n = (len(d) - 13) // 8
            return struct.unpack(f"<{n}Q", d[13:13 + 8 * n])
        for mp in MAPS:
            bd, _ = self.game("bots/v92", "bots/v92", mp, f"v92dbg-{mp}", False)
            br, _ = self.game(self.rec, "bots/v92", mp, f"recA-{mp}", False)
            a, r = trace(bd), trace(br)
            self.assertEqual(len(a), len(r), mp)
            diff = [y - x for x, y in zip(a, r)]
            same = sum(1 for d in diff if d == 0) / len(diff)
            print(f"\n  {mp}: {same:.1%} of {len(diff)} turns identical, max |delta| {max(abs(d) for d in diff)}")
            self.assertGreaterEqual(same, 0.95, mp)

    def test_5_visibility(self):
        mp = MAPS[0]
        bundle, _ = self.game(self.rec, "bots/v92", mp, f"recA-{mp}", False)
        rows = K.parse_rows(team_file(bundle, "team-a.stdout").replace(b"\0", b"").decode("utf-8", "replace"))
        last = {}  # (body, enemy row) -> (last-known dx+px, dy+py) while hidden
        checked = 0
        for r in sorted(rows, key=lambda r: (r["body"], r["round"])):
            x, px, py = r["x"], r["x"][LAY.offset("s") + 1], r["x"][LAY.offset("s") + 2]
            for k in range(LAY.count("e")):
                e = x[E_OFF + k * E_W: E_OFF + (k + 1) * E_W]
                if e[0] != 1:
                    continue
                vis, age, ax, ay = e[2], e[3], e[4] + px, e[5] + py
                if vis:
                    self.assertEqual(age, 0, f"visible enemy with age {age}")
                    last[(r["body"], k)] = (ax, ay)
                else:
                    self.assertGreater(age, 0, "hidden enemy with age 0")
                    if (r["body"], k) in last:
                        self.assertEqual((ax, ay), last[(r["body"], k)], "hidden enemy position changed")
                        checked += 1
        self.assertGreater(checked, 0, "no hidden-enemy rows to check")

    def test_6_lifecycle(self):
        mp = MAPS[0]
        bundle, summary = self.game(self.rec, "bots/v92", mp, f"recA-{mp}", False)
        st = os.path.join(WORK, f"recA-{mp}", "s.json")
        meta, cols, rows = K.episode_from(bundle, st, "A",
                                          dict(key="e0", map_file=mp, map_file_sha256="-", opponent={}, side="A"))
        self.assertEqual(meta["status"], "terminated")
        deaths = sum(len(e["entries"]) for e in summary["events"]  # a death event's owner is the champion that died
                     if e["kind"] == "death" and e["owner"].get("team") == "teamA")
        bodies = len({r["body"] for r in rows})
        resets = sum(r["reset"] for r in rows)
        self.assertLessEqual(resets, bodies + deaths)
        self.assertGreaterEqual(resets, bodies)
        man = dict(layout=10, action_schema="target13-cl1", sampling="teacher", stale_block=False, hidden_size=0,
                   prim_labels=True, rows=len(rows), episodes=[dict(meta, split="dev")])
        cols["episode"] = [0] * len(rows)
        self.assertEqual(C.validate(man, cols), [])
        self.assertEqual(sum(cols["terminated"]), bodies)  # exactly one terminal row per body, none at deaths


if __name__ == "__main__":
    unittest.main(verbosity=2 if "-v" in sys.argv else 1, argv=[sys.argv[0]])
