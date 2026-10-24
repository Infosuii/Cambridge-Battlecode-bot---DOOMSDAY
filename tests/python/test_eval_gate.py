"""Promotion-gate tests on synthetic cell results (labelled synthetic; no match data)."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'python'))
from nfs.evaluate import gate  # noqa: E402
from nfs.evaluate import protocol as proto  # noqa: E402

SHA = 'c' * 64
ORIG = 'o' * 64


def cells(opp, wins_per_map, fuel=0, faults=0):
    """wins_per_map: list of (win_A, win_B) per map index. Synthetic."""
    out = []
    for i, ws in enumerate(wins_per_map):
        for s, w in zip('AB', ws):
            out.append(dict(opponent=opp, map=f'map{i:02d}', side=s, win=float(w), gems=600 if w else 400,
                            opponent_gems=400 if w else 600, faults=faults, fuel_exhausted=fuel, engine='1.0.3',
                            diagnostics_codes=[]))
    return out


def doc(rows, schedule='final', sha=SHA):
    return dict(schedule=schedule, protocol_sha256='p' * 64, rows=rows,
                provenance=dict(candidate_sha256=sha, reference_sha256={}))


def split_wins(n_maps, total):
    """Distribute `total` wins over n_maps x 2 sides deterministically (both sides first)."""
    out = []
    for _ in range(n_maps):
        w = min(2, total)
        total -= w
        out.append((1, 1) if w == 2 else (1, 0) if w == 1 else (0, 0))
    return out


def cfg(opponents):
    c = copy.deepcopy(proto.GATE)
    c['required_opponents'] = list(opponents)
    c['n_boot'] = 4000
    return c


class TestPhase2Failure(unittest.TestCase):
    """The exact phase-2 selection failure: pooled 40/60 -> 45/60 while original fell 10/12 -> 6/12."""

    OPPS = ['original', 'v47', 'first-hour', 'proxy-0', 'proxy-1']
    INCUMBENT = {'original': 10, 'v47': 4, 'first-hour': 6, 'proxy-0': 9, 'proxy-1': 11}
    SELECTED = {'original': 6, 'v47': 7, 'first-hour': 9, 'proxy-0': 11, 'proxy-1': 12}

    def build(self):
        inc = sum((cells(o, split_wins(6, n)) for o, n in self.INCUMBENT.items()), [])
        cand = sum((cells(o, split_wins(6, n)) for o, n in self.SELECTED.items()), [])
        # teacher baseline: original in the candidate seat; vs itself exactly one win per map (6/12)
        teacher = cells('original', [(1, 0)] * 6) + sum((cells(o, split_wins(6, n)) for o, n in self.INCUMBENT.items()
                                                         if o != 'original'), [])
        return cand, teacher, inc

    def test_pooled_up_original_regressed_fails(self):
        cand, teacher, inc = self.build()
        self.assertEqual(sum(r['win'] for r in inc), 40)
        self.assertEqual(sum(r['win'] for r in cand), 45)
        res = gate.evaluate(doc(cand, 'selection'), doc(teacher, 'selection'), cfg(self.OPPS), doc(inc, 'selection'),
                            mode='selection')
        self.assertFalse(res.passed)
        failed = [c['name'] for c in res.checks if not c['passed']]
        self.assertIn('incumbent:original:d_win_point', failed)
        self.assertIn('incumbent:original:d_win_one_sided_lower', failed)
        self.assertIn('teacher:original:d_win_one_sided_lower', failed)
        # the pooled number really did go up - and it did not rescue the candidate
        pooled = res.tables['vs_incumbent']['win']['__pooled__']['point']
        self.assertAlmostEqual(pooled, 5 / 60, places=9)
        self.assertAlmostEqual(res.tables['vs_incumbent']['win']['original']['point'], -4 / 12, places=9)
        self.assertTrue(any('original' in r for r in res.reasons))

    def test_same_without_incumbent_still_fails_on_teacher_original(self):
        cand, teacher, _ = self.build()
        res = gate.evaluate(doc(cand, 'selection'), doc(teacher, 'selection'), cfg(self.OPPS), mode='selection')
        self.assertFalse(res.passed)
        self.assertIn('teacher:original:d_win_one_sided_lower', [c['name'] for c in res.checks if not c['passed']])


class TestGateCases(unittest.TestCase):
    OPPS = ['original', 'v47', 'first-hour', 'v50']

    def strong(self, **kw):
        cand = cells('original', [(1, 1)] * 9 + [(1, 0)] * 3, **kw)
        for o in self.OPPS[1:]:
            cand += cells(o, [(1, 1)] * 8 + [(1, 0)] * 4, **kw)
        return cand

    def teacher(self, fuel=0):
        base = cells('original', [(1, 0)] * 12, fuel=fuel)
        for o in self.OPPS[1:]:
            base += cells(o, [(1, 0)] * 12, fuel=fuel)
        return base

    def run_gate(self, cand, base, mode='final', entry='default', inc=None):
        if entry == 'default':
            entry = dict(event='final_reserved', seq=0, candidate_sha256=SHA)
        return gate.evaluate(doc(cand, mode), doc(base, mode, ORIG), cfg(self.OPPS), inc, mode=mode,
                             ledger_entry=entry, candidate_sha256=SHA)

    def test_clear_improvement_passes(self):
        res = self.run_gate(self.strong(), self.teacher())
        self.assertTrue(res.passed, res.reasons)
        self.assertEqual(res.as_dict()['verdict'], 'PASS')

    def test_final_without_ledger_reservation_fails(self):
        res = self.run_gate(self.strong(), self.teacher(), entry=None)
        self.assertFalse(res.passed)
        self.assertIn('final_ledger_reservation', [c['name'] for c in res.checks if not c['passed']])

    def test_identical_to_teacher_fails_only_on_benefit(self):
        res = self.run_gate(self.teacher(), self.teacher())
        failed = [c['name'] for c in res.checks if not c['passed']]
        self.assertEqual(failed, ['benefit_pooled_d_win_lower'])

    def test_bot_fault_fails(self):
        cand = self.strong()
        cand[0]['faults'] = 1
        res = self.run_gate(cand, self.teacher())
        self.assertIn('candidate_bot_faults', [c['name'] for c in res.checks if not c['passed']])

    def test_fuel_exhaustion_regression_fails(self):
        base = self.teacher()
        for r in base[:10]:
            r['fuel_exhausted'] = 2  # 20 entries in 10 games
        cand = self.strong()
        for r in cand[:20]:
            r['fuel_exhausted'] = 3  # 60 entries in 20 games > 1.25*20+4, > 1.25*10+2
        res = self.run_gate(cand, base)
        failed = [c['name'] for c in res.checks if not c['passed']]
        self.assertIn('fuel_exhausted_entries', failed)
        self.assertIn('games_with_fuel_exhaustion', failed)

    def test_one_reference_collapse_fails_despite_pooled_gain(self):
        cand = cells('original', [(1, 1)] * 12)
        cand += cells('v47', [(1, 1)] * 12) + cells('first-hour', [(1, 1)] * 12) + cells('v50', [(0, 0)] * 12)
        res = self.run_gate(cand, self.teacher())
        failed = [c['name'] for c in res.checks if not c['passed']]
        self.assertIn('teacher:v50:d_win_point', failed)
        self.assertTrue(res.tables['vs_teacher_baseline']['win']['__pooled__']['one_sided_lower'] > 0)
        self.assertFalse(res.passed)

    def test_missing_opponent_fails_early(self):
        cand = [r for r in self.strong() if r['opponent'] != 'v50']
        base = [r for r in self.teacher() if r['opponent'] != 'v50']
        res = self.run_gate(cand, base)
        self.assertFalse(res.passed)
        self.assertIn('all_required_opponents_present', [c['name'] for c in res.checks if not c['passed']])

    def test_wrong_schedule_fails(self):
        res = gate.evaluate(doc(self.strong(), 'selection'), doc(self.teacher(), 'selection', ORIG), cfg(self.OPPS),
                            mode='final', ledger_entry=dict(event='final_reserved', seq=0, candidate_sha256=SHA),
                            candidate_sha256=SHA)
        self.assertIn('schedule_matches_mode', [c['name'] for c in res.checks if not c['passed']])

    def test_unpaired_cells_fail(self):
        cand = self.strong()[:-1]
        res = self.run_gate(cand, self.teacher())
        self.assertFalse(res.passed)


class TestFileEntryPoint(unittest.TestCase):
    """gate.evaluate_files on the REAL frozen final schedule with synthetic rows and a temporary ledger
    (the path Agent G's `promote` uses)."""

    def test_end_to_end(self):
        import json
        import tempfile
        from nfs.evaluate import ledger as L
        if not proto.LOCK.exists():
            self.skipTest('protocol not frozen')
        p = proto.load()
        sched = proto.load_schedule('final')
        refs = {k: v['wasm_sha256'] for k, v in p['references'].items()}
        maps = sorted({c['map'] for c in sched['cells']})

        def rows(strong):
            out = []
            for c in sched['cells']:
                i = maps.index(c['map'])
                w = 1.0 if c['side'] == 'A' or (strong and i % 4 != 0) else 0.0
                out.append(dict(c, win=w, gems=600 if w else 400, opponent_gems=400 if w else 600, faults=0,
                                fuel_exhausted=0, engine='1.0.3', diagnostics_codes=[]))
            return out

        def results(r, sha):
            return dict(schedule='final', protocol_sha256=proto.protocol_sha256(), rows=r,
                        provenance=dict(candidate_sha256=sha, reference_sha256=refs))

        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / 'cand.json').write_text(json.dumps(results(rows(True), SHA)))
            (t / 'base.json').write_text(json.dumps(results(rows(False), refs['original'])))
            led = t / 'ledger.jsonl'
            res = gate.evaluate_files(t / 'cand.json', t / 'base.json', mode='final', ledger_path=led)
            self.assertFalse(res.passed)
            self.assertIn('final_ledger_reservation', [c['name'] for c in res.checks if not c['passed']])
            L.Ledger(led).reserve_final(SHA, 'synthetic-run', proto.protocol_sha256())
            res = gate.evaluate_files(t / 'cand.json', t / 'base.json', mode='final', ledger_path=led)
            self.assertTrue(res.passed, res.reasons)
            self.assertEqual(res.labels['protocol_sha256'], proto.protocol_sha256())


if __name__ == '__main__':
    unittest.main()
