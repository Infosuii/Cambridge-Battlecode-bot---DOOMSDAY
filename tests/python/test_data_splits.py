"""Grouped split invariants and generalisation splits (synthetic records)."""
import random
import unittest

import _fakes as F  # noqa: F401 - sets sys.path
from nfs.data import splits as sp


def recs(n=400, teams=40, maps=10, seed=0):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        a, b = rng.sample(range(teams), 2)
        out.append(dict(match_id=f'm{i:04d}', team_ids=[f't{a:02d}', f't{b:02d}'], map_hash=f'map{rng.randrange(maps)}'))
    return out


class SplitTests(unittest.TestCase):
    def test_team_pair_never_split(self):
        r = recs()
        s = sp.grouped_split(r)
        by_pair = {}
        for x in r:
            k = '|'.join(sorted(x['team_ids']))
            by_pair.setdefault(k, set()).add(s['assignment'][x['match_id']])
        self.assertTrue(all(len(v) == 1 for v in by_pair.values()))
        self.assertEqual(set(s['counts']), set(sp.PARTITIONS))

    def test_order_independent_and_deterministic(self):
        r = recs()
        a = sp.grouped_split(r)['assignment']
        r2 = list(r)
        random.Random(5).shuffle(r2)
        self.assertEqual(a, sp.grouped_split(r2)['assignment'])
        b = sp.grouped_split(r, sp.SplitConfig(seed='other'))['assignment']
        self.assertNotEqual(a, b)

    def test_group_id_and_determinism_key_merge(self):
        r = [dict(match_id='a', group_id='g1', team_ids=['x', 'y']),
             dict(match_id='b', group_id='g1', team_ids=['p', 'q']),
             dict(match_id='c', team_ids=['p', 'q']),
             dict(match_id='d', determinism_key=['w1', 'w2', 'm'], team_ids=['u', 'v']),
             dict(match_id='e', determinism_key=['w1', 'w2', 'm'], team_ids=['s', 't'])]
        comp = sp.components(r, sp.SplitConfig().keys)
        self.assertEqual(comp['a'], comp['b'])
        self.assertEqual(comp['b'], comp['c'])          # transitively via team pair p|q
        self.assertEqual(comp['d'], comp['e'])          # identical deterministic game
        self.assertNotEqual(comp['a'], comp['d'])
        for seed in range(20):
            s = sp.grouped_split(r, sp.SplitConfig(seed=f's{seed}'))['assignment']
            self.assertEqual(len({s['a'], s['b'], s['c']}), 1)
            self.assertEqual(s['d'], s['e'])

    def test_verify_grouping_detects_violation(self):
        r = [dict(match_id='a', team_ids=['x', 'y']), dict(match_id='b', team_ids=['y', 'x'])]
        with self.assertRaises(AssertionError):
            sp.verify_grouping(r, {'a': 'train', 'b': 'final_eval'}, ('match_id', 'team_pair'))

    def test_experiment1_never_final_eval(self):
        r = recs(600)
        for x in r[::3]:
            x['used_by_experiment1'] = True
        s = sp.grouped_split(r)
        for x in r:
            if x.get('used_by_experiment1'):
                self.assertNotEqual(s['assignment'][x['match_id']], 'final_eval')

    def test_map_split_clean(self):
        r = recs()
        s = sp.map_split(r, holdout_fraction=0.3)
        held = set(s['held_out_entities'])
        for x in r:
            part = s['assignment'][x['match_id']]
            self.assertEqual(part == 'final_eval', x['map_hash'] in held)
        self.assertFalse(any(v == 'excluded_mixed' for v in s['assignment'].values()))

    def test_opponent_split_excludes_mixed(self):
        r = recs()
        s = sp.opponent_split(r, holdout_fraction=0.3)
        held = set(s['held_out_entities'])
        for x in r:
            part, ts = s['assignment'][x['match_id']], set(x['team_ids'])
            if part == 'final_eval':
                self.assertTrue(ts <= held)
            elif part in ('train', 'validation'):
                self.assertFalse(ts & held)
            else:
                self.assertEqual(part, 'excluded_mixed')
        own = [dict(match_id=f'o{i}', team_ids=['me', f'opp{i % 5}']) for i in range(50)]
        so = sp.opponent_split(own, 0.4, own_identity='me')
        self.assertNotIn('excluded_mixed', so['counts'])  # only the opponent is an entity

    def test_local_maps_are_reused_benchmarks(self):
        local = {'h1': '00alpha', 'h2': '01beta'}
        prov = sp.map_provenance(['h1', 'h2', 'h3', 'h4'], local, inspected=['h3'])
        self.assertEqual(prov['h1']['label'], sp.REUSED)
        self.assertEqual(prov['h2']['label'], sp.REUSED)
        self.assertEqual(prov['h3']['label'], sp.REUSED)
        self.assertEqual(prov['h4']['label'], sp.FRESH)
        labels = sp.local_map_labels(local)
        self.assertTrue(all(v['label'] == sp.REUSED for v in labels.values()))
        r = [dict(match_id=f'm{i}', team_ids=[f'a{i}', f'b{i}'], map_hash='h1' if i % 2 else 'h2') for i in range(50)]
        man = sp.split_manifest(r, local=local)
        for k in ('grouped', 'map_generalisation', 'opponent_generalisation'):
            self.assertNotIn(sp.FRESH, man[k]['final_eval_map_labels'])

    def test_real_local_maps_all_reused(self):
        from nfs import engine
        local = sp.local_map_hashes(engine.MAPS)
        self.assertEqual(len(local), 40)
        prov = sp.map_provenance(list(local), local)
        self.assertTrue(all(v['label'] == sp.REUSED for v in prov.values()))


if __name__ == '__main__':
    unittest.main()
