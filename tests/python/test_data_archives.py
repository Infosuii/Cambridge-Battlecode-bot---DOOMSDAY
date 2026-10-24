"""Archive integrity, de-duplication and eligibility filters on SYNTHETIC zips (no historical data touched)."""
import json
import tempfile
import unittest
from pathlib import Path

import _fakes as F
from nfs.data import archives as ar


def entries(ids, engine='1.0.3', **kw):
    return {F.member_name(i): F.make_summary(engine=engine, **kw) for i in ids}


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def index(self, paths, n=50, **kw):
        return ar.build_index(paths, sample_per_part=n, converter=F.json_converter, workers=2, **kw)

    def test_member_name_parsing(self):
        p = ar.parse_member_name(F.member_name(F.uuid_n(5), kind='unranked'))
        self.assertEqual(p['match_id'], F.uuid_n(5))
        self.assertEqual(p['kind'], 'unranked')
        self.assertEqual(len(p['team_ids']), 2)
        self.assertIsNone(ar.parse_member_name('readme.txt'))
        self.assertEqual(ar.parse_archive_name('summaries-2026-10-21-part3 (1).zip'), dict(date='2026-10-21', part=3))

    def test_zero_byte_duplicate_part_skipped(self):
        good = F.synthetic_zip(self.d / 'a' / 'summaries-2026-10-21-part1.zip', entries([F.uuid_n(1)]))
        empty = self.d / 'b' / 'summaries-2026-10-21-part1.zip'
        empty.parent.mkdir()
        empty.write_bytes(b'')
        man = self.index([empty, good])
        src = {Path(s['path']).parent.name: s for s in man['sources']}
        self.assertEqual(src['b']['status'], 'zero_byte')
        self.assertFalse(src['b']['selected'])
        self.assertTrue(src['a']['selected'])
        self.assertEqual(man['accounting']['archive_entries'], 1)

    def test_truncated_archive_detected(self):
        p = F.synthetic_zip(self.d / 'summaries-2026-10-21-part2.zip', entries([F.uuid_n(i) for i in range(5)]))
        raw = p.read_bytes()
        p.write_bytes(raw[:len(raw) // 2])
        self.assertEqual(ar.inspect_zip_file(p)['status'], 'truncated')
        man = self.index([p])
        self.assertFalse(man['sources'][0]['selected'])
        self.assertEqual(man['accounting']['archive_entries'], 0)

    def test_not_zip(self):
        p = self.d / 'summaries-2026-10-21-part2.zip'
        p.write_bytes(b'hello world' * 10)
        self.assertEqual(ar.inspect_zip_file(p)['status'], 'not_zip')

    def test_bad_crc_rejected(self):
        ids = [F.uuid_n(i) for i in range(3)]
        p = F.synthetic_zip(self.d / 'summaries-2026-10-21-part1.zip', entries(ids))
        F.corrupt_member(p, F.member_name(ids[1]))
        man = self.index([p])
        self.assertEqual(man['accounting']['rejected_by_reason'].get('crc_error'), 1)
        self.assertEqual(man['accounting']['accepted_independent_matches'], 2)

    def test_duplicate_ids_across_parts(self):
        p1 = F.synthetic_zip(self.d / 'summaries-2026-10-21-part1.zip', entries([F.uuid_n(1), F.uuid_n(2)]))
        p2 = F.synthetic_zip(self.d / 'summaries-2026-10-21-part2.zip', entries([F.uuid_n(2), F.uuid_n(3)]))
        man = self.index([p2, p1])
        acc = man['accounting']
        self.assertEqual(acc['archive_entries'], 4)
        self.assertEqual(acc['unique_match_ids'], 3)
        self.assertEqual(acc['duplicate_entries_dropped'], 1)
        self.assertEqual(man['duplicates'][0]['first_part'], 1)   # deterministic: lower part number wins
        self.assertEqual(acc['accepted_independent_matches'], 3)

    def test_wrong_date_archives_rejected(self):
        old = F.synthetic_zip(self.d / 'summaries-2026-10-20-part1.zip', entries([F.uuid_n(1)]))
        noname = F.synthetic_zip(self.d / 'matches.zip', entries([F.uuid_n(2)]))
        new = F.synthetic_zip(self.d / 'summaries-2026-10-22-part1.zip', entries([F.uuid_n(3)]))
        man = self.index([old, noname, new])
        parts = {p['date']: p for p in man['parts']}
        self.assertFalse(parts['2026-10-20']['admitted'])
        self.assertEqual(parts['2026-10-20']['reject_reason'], 'date_before_floor')
        self.assertTrue(parts['2026-10-22']['admitted'])
        skipped = [s for s in man['sources'] if Path(s['path']).name == 'matches.zip'][0]
        self.assertEqual(skipped['skip_reason'], 'unrecognised_archive_name')
        self.assertEqual(man['accounting']['accepted_independent_matches'], 1)

    def test_listing_date_mismatch_rejected(self):
        p = F.synthetic_zip(self.d / 'summaries-2026-10-21-part1.zip', entries([F.uuid_n(1)]))
        man = self.index([p], platform_listing={'summaries-2026-10-21-part1.zip': '2026-10-20'})
        self.assertEqual(man['parts'][0]['reject_reason'], 'date_listing_mismatch')

    def test_engine_versions(self):
        e = {}
        e.update(entries([F.uuid_n(1)], engine='1.0.1'))
        e.update(entries([F.uuid_n(2)], engine='1.0.2'))
        e.update(entries([F.uuid_n(3)], engine='1.0.3'))
        e.update(entries([F.uuid_n(4)], engine='0.9'))
        p = F.synthetic_zip(self.d / 'summaries-2026-10-21-part1.zip', e)
        self.index([p], sample_out_dir=self.d / 'rows')
        rows = {json.loads(l)['match_id']: json.loads(l) for l in (self.d / 'rows/sample_rows.jsonl').read_text().splitlines()}
        self.assertEqual(rows[F.uuid_n(1)]['reason'], 'engine_1.0.1_excluded')
        self.assertEqual(rows[F.uuid_n(2)]['label_scope'], ar.SCOPE_DRAFT_OBS)
        self.assertIn('draft_observational', rows[F.uuid_n(2)]['flags'])
        self.assertEqual(rows[F.uuid_n(3)]['label_scope'], ar.SCOPE_GAMEPLAY)
        self.assertEqual(rows[F.uuid_n(4)]['reason'], 'engine_0.9_unknown')
        self.assertTrue(rows[F.uuid_n(3)]['rule_version'].startswith('1.0.3+'))

    def test_gameplay_refuses_1_0_2_without_adapter(self):
        r102 = dict(match_id='x', engine_version='1.0.2', label_scope=ar.SCOPE_DRAFT_OBS)
        r103 = dict(match_id='y', engine_version='1.0.3', label_scope=ar.SCOPE_GAMEPLAY)
        r101 = dict(match_id='z', engine_version='1.0.1', label_scope=None)
        self.assertEqual(len(ar.gameplay_label_records([r103])), 1)
        with self.assertRaises(ar.EngineCompatibilityError):
            ar.gameplay_label_records([r103, r102])
        untested = ar.EngineAdapter('a', '1.0.2', '1.0.3', tested=False, description='untested')
        with self.assertRaises(ar.EngineCompatibilityError):
            ar.gameplay_label_records([r102], adapter=untested)
        tested = ar.EngineAdapter('a', '1.0.2', '1.0.3', tested=True, description='synthetic test adapter')
        out = ar.gameplay_label_records([r103, r102], adapter=tested)
        self.assertEqual(out[1]['engine_adapter'], 'a')
        with self.assertRaises(ar.EngineCompatibilityError):
            ar.gameplay_label_records([r101], adapter=ar.EngineAdapter('b', '1.0.1', '1.0.3', True, 'x'))
        self.assertTrue(all(r['confounded'] for r in ar.draft_observational_records([r102, r103])))

    def test_status_completeness_rounds_filters(self):
        e = {}
        e.update(entries([F.uuid_n(1)], rounds=20))
        e.update(entries([F.uuid_n(2)], outcome='tie'))
        e.update(entries([F.uuid_n(3)], faults=(1, 0)))
        e.update(entries([F.uuid_n(4)], capture=False))
        e.update(entries([F.uuid_n(5)], gems=(0, 0)))
        e.update(entries([F.uuid_n(6)], picks={'teamA': ['Ryth', 'Ren'], 'teamB': ['Varg', 'Tavi']}))
        e.update(entries([F.uuid_n(7)], picks={'teamA': ['Ryth', 'Ren', 'Nobody'], 'teamB': ['Varg', 'Tavi', 'Ren']}))
        e.update(entries([F.uuid_n(8)]))
        p = F.synthetic_zip(self.d / 'summaries-2026-10-21-part1.zip', e)
        man = self.index([p])
        self.assertEqual(man['accounting']['rejected_by_reason'],
                         {'too_few_rounds': 1, 'outcome_not_decisive': 1, 'bot_fault': 1, 'incomplete_capture': 1,
                          'zero_score_tiebreak': 1, 'draft_size': 1, 'unknown_champion': 1})
        self.assertEqual(man['accounting']['accepted_gameplay_1_0_3'], 1)

    def test_experiment1_ids_labelled_and_excluded_from_fresh(self):
        ids = [F.uuid_n(i) for i in range(10)]
        p = F.synthetic_zip(self.d / 'summaries-2026-10-21-part1.zip', entries(ids))
        exp1 = {ids[0]: dict(part=1, accepted_v2=True, engine_version='1.0.3'),
                ids[1]: dict(part=1, accepted_v2=False, engine_version=None)}
        man = self.index([p], n=3, experiment1_ids=exp1, consistency_checks_per_part=2, sample_out_dir=self.d / 'r')
        rows = [json.loads(l) for l in (self.d / 'r/sample_rows.jsonl').read_text().splitlines()]
        fresh = [r for r in rows if r['sample_role'] == 'fresh']
        self.assertEqual(len(fresh), 3)
        self.assertFalse(any(r['used_by_experiment1'] for r in fresh))
        cons = [r for r in rows if r['sample_role'] == 'experiment1_consistency']
        self.assertEqual({r['match_id'] for r in cons}, {ids[0], ids[1]})
        self.assertTrue(all(r['used_by_experiment1'] for r in cons))
        self.assertEqual(man['experiment1']['ids_found_in_archives'], 2)

    def test_load_experiment1_ids(self):
        c = self.d / 'cache'
        c.mkdir()
        (c / 'part-01-v2.jsonl').write_text(json.dumps(dict(match_id='m1', engine_version='1.0.2')) + '\n'
                                            + json.dumps(dict(match_id='m2', rejected='engine_version_1.0.1')) + '\n')
        (c / 'part-01.jsonl').write_text(json.dumps(dict(match_id='m1', rejected='engine_version_1.0.2')) + '\n')
        ids = ar.load_experiment1_ids(c)
        self.assertTrue(ids['m1']['accepted_v2'])
        self.assertFalse(ids['m2']['accepted_v2'])
        self.assertEqual(len(ids['m1']['files']), 2)

    def test_sample_cap_and_accounting_fields(self):
        p = F.synthetic_zip(self.d / 'summaries-2026-10-21-part1.zip', entries([F.uuid_n(1)]))
        with self.assertRaises(ar.ArchiveError):
            ar.build_index([p], sample_per_part=150, consistency_checks_per_part=51, converter=F.json_converter)
        man = self.index([p])
        for k in ('archive_entries', 'sampled_entries', 'accepted_independent_matches', 'per_turn_observations',
                  'augmented_samples', 'epochs'):
            self.assertIn(k, man['accounting'])
        self.assertEqual(man['accounting']['per_turn_observations'], 0)
        self.assertEqual(man['accounting']['epochs'], 0)

    def test_sha256_cache(self):
        p = F.synthetic_zip(self.d / 'summaries-2026-10-21-part1.zip', entries([F.uuid_n(1)]))
        cache = self.d / 'h.json'
        h1 = ar.sha256_cached(p, cache)
        self.assertTrue(cache.exists())
        self.assertEqual(h1, ar.sha256_cached(p, cache))
        import hashlib
        self.assertEqual(h1, hashlib.sha256(p.read_bytes()).hexdigest())

    def test_sample_order_deterministic(self):
        ids = [F.uuid_n(i) for i in range(30)]
        p = F.synthetic_zip(self.d / 'summaries-2026-10-21-part1.zip', entries(ids))
        a = self.index([p], n=5, sample_out_dir=self.d / 'x')
        rows_a = (self.d / 'x/sample_rows.jsonl').read_text()
        self.index([p], n=5, sample_out_dir=self.d / 'y')
        self.assertEqual(rows_a, (self.d / 'y/sample_rows.jsonl').read_text())
        want = sorted(ids, key=ar.sample_order_key)[:5]
        self.assertEqual(sorted(json.loads(l)['match_id'] for l in rows_a.splitlines()), sorted(want))


if __name__ == '__main__':
    unittest.main()
