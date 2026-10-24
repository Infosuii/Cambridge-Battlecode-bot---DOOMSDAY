"""Canonical-frame tests (agent C): involutions, heading/vector consistency, team-A/B equivalence on mirrored synthetic
states, and ally/enemy swap through a synthetic two-team world. Synthetic data only."""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_obs_synth as synth  # noqa: E402
from nfs import obs, transforms as T  # noqa: E402


class TestTransforms(unittest.TestCase):
    def test_position_vector_heading_involutions(self):
        rng = random.Random(1)
        for sym in (0, 1, 2):
            for _ in range(500):
                w, h = rng.randint(1, 120), rng.randint(1, 120)
                p = (rng.randrange(w), rng.randrange(h))
                self.assertEqual(T.reflect_pos(sym, w, h, T.reflect_pos(sym, w, h, p)), p)
                v = (rng.randint(-50, 50), rng.randint(-50, 50))
                self.assertEqual(T.reflect_vec(sym, T.reflect_vec(sym, v)), v)
                q = (rng.randrange(w), rng.randrange(h))
                # T(q) - T(p) == L(q - p): relative vectors transform by the linear part.
                tp, tq = T.reflect_pos(sym, w, h, p), T.reflect_pos(sym, w, h, q)
                self.assertEqual((tq[0] - tp[0], tq[1] - tp[1]), T.reflect_vec(sym, (q[0] - p[0], q[1] - p[1])))
                # Positions stay on the board.
                self.assertTrue(0 <= tp[0] < w and 0 <= tp[1] < h)
            for d in range(8):
                self.assertEqual(T.reflect_dir(sym, T.reflect_dir(sym, d)), d)
                F = T.make_frame(40, 30, sym, 1000, 1000, 0)
                self.assertTrue(F.flip)
                self.assertEqual(F.canon_dir(d), T.reflect_dir(sym, d))
                self.assertEqual(T.DIRS[F.canon_dir(d)], F.canon_vec(T.DIRS[d]))

    def test_frame_matches_sdk_reflections(self):
        # cambc::vec2::reflect_horizontal = (-x, y), reflect_vertical = (x, -y), rotate_180 = (-x, -y).
        self.assertEqual(T.reflect_vec(T.HORIZONTAL, (3, 4)), (-3, 4))
        self.assertEqual(T.reflect_vec(T.VERTICAL, (3, 4)), (3, -4))
        self.assertEqual(T.reflect_vec(T.ROTATIONAL180, (3, 4)), (-3, -4))
        self.assertEqual(T.reflect_pos(T.HORIZONTAL, 10, 8, (0, 2)), (9, 2))
        self.assertEqual(T.reflect_pos(T.VERTICAL, 10, 8, (0, 2)), (0, 5))
        self.assertEqual(T.reflect_pos(T.ROTATIONAL180, 10, 8, (0, 2)), (9, 5))

    def test_flip_rule(self):
        # horizontal: our spawn on the right half flips; on the axis the absolute team decides.
        self.assertFalse(T.make_frame(20, 20, 0, 4, 30, 0).flip)
        self.assertTrue(T.make_frame(20, 20, 0, 34, 0, 0).flip)
        self.assertFalse(T.make_frame(20, 20, 0, 19, 0, 0).flip)
        self.assertTrue(T.make_frame(20, 20, 0, 19, 0, 1).flip)
        self.assertTrue(T.make_frame(20, 20, 1, 0, 30, 0).flip)
        self.assertTrue(T.make_frame(20, 20, 2, 19, 30, 0).flip)
        self.assertFalse(T.make_frame(20, 20, 2, 19, 8, 1).flip)
        self.assertFalse(T.make_frame(20, 20, 7, 99, 99, 1).flip)

    def test_mirrored_state_encodes_identically(self):
        rng = random.Random(2)
        for i in range(600):
            r = synth.plausible(rng, sym=i % 3)
            m = T.mirror_raw(r)
            self.assertFalse(obs.frame_of(r).flip)
            self.assertTrue(obs.frame_of(m).flip)
            a, b = obs.encode(r), obs.encode(m)
            self.assertEqual(a.tobytes(), b.tobytes(), f'case {i}')
            # The mirrored RawTurn really is different in world coordinates.
            self.assertNotEqual(obs.pack(r), obs.pack(m))

    def test_sector_of(self):
        self.assertEqual(T.sector_of(0, 5), 0)
        self.assertEqual(T.sector_of(5, 5), 1)
        self.assertEqual(T.sector_of(5, 0), 2)
        self.assertEqual(T.sector_of(0, -5), 4)
        self.assertEqual(T.sector_of(-5, 0), 6)
        self.assertEqual(T.sector_of(20, 0), 8)
        for d in range(8):  # sectors follow the frame like headings
            F = T.make_frame(40, 40, 2, 1000, 1000, 0)
            v = T.DIRS[d]
            self.assertEqual(T.sector_of(*F.canon_vec((4 * v[0], 4 * v[1]))), F.canon_dir(d))


# ---------------------------------------------------------------- ally/enemy swap through a synthetic world

def _world(rng: random.Random, sym: int) -> dict:
    W, H = rng.randint(24, 80), rng.randint(24, 80)
    boxes = {0: (1, 1, 3, 3)}
    a = T.reflect_pos(sym, W, H, (1, 1))
    b = T.reflect_pos(sym, W, H, (3, 3))
    boxes[1] = (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
    champs = {0: [], 1: []}
    for team in (0, 1):
        for k in range(rng.randint(3, 6)):
            mh = synth.f32(600 + 1500 * rng.random())
            champs[team].append(dict(handle=10 + 20 * team + k, type=rng.randint(0, 12),
                                     pos=(rng.randrange(W), rng.randrange(H)), hp=synth.f32(mh * rng.random()), max_hp=mh,
                                     strength=synth.f32(100 * rng.random()), focus=synth.f32(100 * rng.random()),
                                     range=rng.randint(1, 5), gems=rng.randint(0, 60)))
    return dict(W=W, H=H, sym=sym, boxes=boxes, champs=champs, scores={0: rng.randint(0, 900), 1: rng.randint(0, 900)},
                round=rng.randint(1, 1999))


def _mirror_world(w: dict) -> dict:
    """Swap the teams and reflect the board: team 1 of the result is team 0 of `w` seen through the symmetry."""
    out = dict(w)
    out['boxes'] = {}
    for team in (0, 1):
        x0, y0, x1, y1 = w['boxes'][1 - team]
        a = T.reflect_pos(w['sym'], w['W'], w['H'], (x0, y0))
        b = T.reflect_pos(w['sym'], w['W'], w['H'], (x1, y1))
        out['boxes'][team] = (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
    out['champs'] = {team: [dict(c, pos=T.reflect_pos(w['sym'], w['W'], w['H'], c['pos'])) for c in w['champs'][1 - team]]
                     for team in (0, 1)}
    out['scores'] = {0: w['scores'][1], 1: w['scores'][0]}
    return out


def _view(w: dict, team: int, idx: int, vision: int = 8) -> dict:
    """The RawTurn champion `idx` of `team` would capture: visibility by Chebyshev radius, no hidden state."""
    r = obs.empty_raw()
    me = w['champs'][team][idx]
    mine, theirs = w['boxes'][team], w['boxes'][1 - team]
    r.update(width=w['W'], height=w['H'], symmetry=w['sym'], abs_team=team, round=w['round'], max_rounds=2000,
             winning_gems=1000, slot=idx, team_size=len(w['champs'][team]), enemy_count=len(w['champs'][1 - team]),
             n_groups=10, own_spawn_x0=mine[0], own_spawn_y0=mine[1], own_spawn_x1=mine[2], own_spawn_y1=mine[3],
             enemy_spawn_x0=theirs[0], enemy_spawn_y0=theirs[1], enemy_spawn_x1=theirs[2], enemy_spawn_y1=theirs[3],
             alive=1, pos_x=me['pos'][0], pos_y=me['pos'][1], gems=me['gems'], attack_range=me['range'], type=me['type'],
             hp=me['hp'], max_hp=me['max_hp'], prev_hp=me['hp'], strength=me['strength'], focus=me['focus'],
             tribute_carry=40, target_group=-1, spawn_dist=-1, altar_dist=-1, enemy_spawn_walk=-1,
             ally_score=w['scores'][team], enemy_score=w['scores'][1 - team], alive_us=len(w['champs'][team]),
             alive_them=len(w['champs'][1 - team]), hist10_age=-1, hist50_age=-1, hist200_age=-1, sight_age=-1,
             distress_age=-1)
    allies = [(k, c) for k, c in enumerate(w['champs'][team]) if k != idx]
    for j, (k, c) in enumerate(allies):
        vis = int(max(abs(c['pos'][0] - me['pos'][0]), abs(c['pos'][1] - me['pos'][1])) <= vision)
        r['ally'][j].update(present=1, handle=c['handle'], slot=k, type=c['type'], alive=1, visible=vis, known=vis, x=c['pos'][0],
                            y=c['pos'][1], range=c['range'], gems=c['gems'] if vis else -1, claim_code=127, claim_dist=-1,
                            hp=c['hp'], max_hp=c['max_hp'], strength=c['strength'], focus=c['focus'])
    nvis = 0
    for j, c in enumerate(w['champs'][1 - team]):
        vis = int(max(abs(c['pos'][0] - me['pos'][0]), abs(c['pos'][1] - me['pos'][1])) <= vision)
        nvis += vis
        e = r['enemy'][j]
        e.update(present=1, handle=c['handle'], type=c['type'], alive=1, visible=vis, known=vis)
        if vis:  # hidden enemies contribute only public identity
            e.update(x=c['pos'][0], y=c['pos'][1], range=c['range'], gems=c['gems'], hp=c['hp'], max_hp=c['max_hp'],
                     strength=c['strength'], focus=c['focus'])
    r.update(vis_enemies=nvis, vis_allies=sum(r['ally'][j]['visible'] for j in range(len(allies))))
    return r


class TestTeamSwap(unittest.TestCase):
    def test_enemy_view_of_mirrored_world_equals_ours(self):
        rng = random.Random(3)
        checked = 0
        for i in range(300):
            w = _world(rng, sym=i % 3)
            m = _mirror_world(w)
            for idx in range(len(w['champs'][0])):
                ours = obs.encode(_view(w, 0, idx))
                theirs = obs.encode(_view(m, 1, idx))  # team 1 of the swapped world = team 0 of the original
                self.assertEqual(ours.tobytes(), theirs.tobytes(), f'world {i} champion {idx}')
                checked += 1
        self.assertGreater(checked, 900)

    def test_hidden_enemy_state_does_not_leak(self):
        rng = random.Random(4)
        for i in range(200):
            w = _world(rng, sym=i % 3)
            base = obs.encode(_view(w, 0, 0, vision=-1))  # nobody visible
            for c in w['champs'][1]:  # change every hidden enemy's private state
                c.update(hp=synth.f32(c['hp'] * 0.5), gems=c['gems'] + 7, pos=(0, 0), strength=0.0)
            again = obs.encode(_view(w, 0, 0, vision=-1))
            self.assertEqual(base.tobytes(), again.tobytes())

    def test_ally_and_enemy_rows_are_distinct_blocks(self):
        rng = random.Random(5)
        w = _world(rng, sym=2)
        x = obs.split(obs.encode(_view(w, 0, 0, vision=200)))
        self.assertEqual(int(x['ally_mask'].sum()), len(w['champs'][0]) - 1)
        self.assertEqual(int(x['enemy_mask'].sum()), len(w['champs'][1]))
        self.assertTrue(np.all(x['enemy'][:len(w['champs'][1]), 1] == 1.0))  # visible flag


if __name__ == '__main__':
    unittest.main()
