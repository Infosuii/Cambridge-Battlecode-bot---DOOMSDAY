"""Fuel member / NFT1 telemetry parser tests (synthetic bytes + real reference cells when present) and the
equivalence comparator on synthetic match folders."""
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'python'))
from nfs.evaluate import equivalence as eq  # noqa: E402
from nfs.evaluate import fuel  # noqa: E402

BUDGETS = (1000000, 100000, 200000, 100000, 1000000, 100000, 200000, 100000)


def fuel_member(used):
    return fuel.FUEL_TAG + b'\x00\x00\x01\x00\x00' + struct.pack(f'<{8 + len(used)}q', *BUDGETS, *used)


def summary(outcome='teamA', events=(), gems=(1000, 500), rounds=3, champs=2):
    roster = [dict(id=i, team='teamA' if i < champs else 'teamB', draftPick=i) for i in range(2 * champs)]
    return dict(match=dict(outcome=outcome, roundsStarted=rounds, engineVersion='1.0.3', mapHash='m'),
                teams=[dict(team='teamA', submittedGems=str(gems[0])), dict(team='teamB', submittedGems=str(gems[1]))],
                events=list(events), roster=dict(champions=roster), diagnostics=dict(botFaults=dict(teamA=0, teamB=0)))


def fe_event(team, cid, rnd):
    return dict(kind='fuelExhausted', owner=dict(team=team, id=cid),
                entries=[dict(timestamp=dict(round=rnd, ordinal=rnd * 10), value='1', x=0, y=0, target=0)])


def write_cell(folder: Path, summ: dict, replay=b'R', fa=(5, 5, 9, 9, 50, 100000, 60, 70), fb=(5, 5, 9, 9, 1, 2, 3, 4)):
    folder.mkdir(parents=True)
    (folder / 'summary.json').write_text(json.dumps(summ))
    with zipfile.ZipFile(folder / 'x-vs-y-1.repl26a', 'w') as z:
        z.writestr('replay.repl26a', replay)
        z.writestr('team-a.fuel', fuel_member(fa))
        z.writestr('team-b.fuel', fuel_member(fb))
        z.writestr('team-a.stdout', b'')
        z.writestr('team-b.stdout', b'')
    return folder


class TestFuelMember(unittest.TestCase):
    def test_parse_and_profile(self):
        p = fuel.parse_fuel_member(fuel_member([5, 5, 150000, 140000] + [50000] * 99 + [100000]))
        self.assertEqual(p['budgets'][:3], [1000000, 100000, 200000])
        prof = fuel.turn_profile(p, n_draft=2, n_champions=2, rounds=51)
        self.assertEqual(prof['regular_turns'], 100)
        self.assertEqual(prof['at_cap'], 1)
        self.assertEqual(prof['max'], 100000)
        self.assertEqual(prof['first_turn_max'], 150000)
        self.assertTrue(prof['layout_consistent'])

    def test_bad_tag_and_length(self):
        with self.assertRaises(ValueError):
            fuel.parse_fuel_member(b'xxxx')
        with self.assertRaises(ValueError):
            fuel.parse_fuel_member(fuel_member([1, 2])[:-3])

    def test_cell_cross_check_with_events(self):
        with tempfile.TemporaryDirectory() as t:
            f = write_cell(Path(t) / 'c', summary(events=[fe_event('teamA', 0, 2)]))
            c = fuel.cell_fuel(f)
            self.assertEqual(c['events']['teamA']['entries'], 1)
            self.assertEqual(c['teams']['teamA']['at_cap'], 1)
            self.assertTrue(fuel.check_against_events(c))

    def test_real_reference_cells_cross_check(self):
        """Real engine data (reference runs written by tools/eval_run.py): cap turns == fuelExhausted entries."""
        root = ROOT / 'evaluation/results/reference/matches'
        folders = sorted(p for p in root.glob('*') if (p / 'summary.json').exists())[:12] if root.exists() else []
        if not folders:
            self.skipTest('reference cells not recorded yet')
        for f in folders:
            c = fuel.cell_fuel(f)
            self.assertTrue(fuel.check_against_events(c), f)
            self.assertTrue(all(t['layout_consistent'] for t in c['teams'].values()), f)


class TestTelemetry(unittest.TestCase):
    def test_tolerant_formats(self):
        self.assertIsNone(fuel.parse_nft1_line('fuellog round 3'))
        self.assertEqual(fuel.parse_nft1_line('NFT1 {"head":"move","calls":3}'), {'head': 'move', 'calls': 3})
        r = fuel.parse_nft1_line('NFT1 head head=bank calls=4 fallback=1 reason=budget fuel=812.5 ok=true')
        self.assertEqual(r, dict(kind='head', head='bank', calls=4, fallback=1, reason='budget', fuel=812.5, ok=True))
        self.assertEqual(fuel.parse_nft1_line('NFT1 calls=2 invalid=0'), {'calls': 2, 'invalid': 0})
        import base64
        b = base64.b64encode(b'{"head":"shop","refused":2}').decode()
        self.assertEqual(fuel.parse_nft1_line('\0\0NFT1 b64:' + b), {'head': 'shop', 'refused': 2})
        self.assertIn('_raw', fuel.parse_nft1_line('NFT1 ???'))

    def test_aggregate(self):
        out = '\n'.join(['NFT1 head=move calls=3 neural=2 fallback=1 fuel=100', 'noise',
                         'NFT1 head=move calls=1 fallback=1 reason=nan', 'NFT1 head=bank calls=2 invalid=1 fuel=50',
                         'NFT1 {broken'])
        t = fuel.parse_telemetry(out)
        self.assertEqual(t['records'], 4)
        self.assertEqual(t['malformed'], 1)
        self.assertEqual(t['per_head']['move'], {'calls': 4, 'neural': 2, 'fallback': 2})
        self.assertEqual(t['totals']['invalid'], 1)
        self.assertEqual(t['reasons']['move'], {'nan': 1})
        self.assertEqual(t['fuel']['move']['mean'], 100.0)


class TestEquivalence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_identical(self):
        a = write_cell(self.d / 'a', summary())
        b = write_cell(self.d / 'b', summary())
        c = eq.compare(a, b, 'teamA')
        self.assertTrue(c['actions_identical'] and c['summary_identical'] and c['fuel_identical'])
        self.assertIsNone(c['first_divergent_round'])

    def test_fuel_only_difference_keeps_actions(self):
        a = write_cell(self.d / 'a', summary(), fa=(5, 5, 9, 9, 80, 100000, 90, 99))
        b = write_cell(self.d / 'b', summary())
        c = eq.compare(a, b, 'teamA')
        self.assertTrue(c['actions_identical'])
        self.assertFalse(c['fuel_identical'])
        self.assertEqual(c['candidate_fuel_overhead']['max'], 30)
        self.assertEqual(c['candidate_fuel_overhead']['mean'], (30 + 30 + 29) / 8)

    def test_divergence_round_reported(self):
        ev_a = [fe_event('teamA', 0, 2), fe_event('teamB', 2, 7)]
        ev_b = [fe_event('teamA', 0, 2), fe_event('teamB', 3, 5)]
        a = write_cell(self.d / 'a', summary(events=ev_a, outcome='teamB'), replay=b'R1')
        b = write_cell(self.d / 'b', summary(events=ev_b), replay=b'R2')
        c = eq.compare(a, b, 'teamA')
        self.assertFalse(c['actions_identical'])
        self.assertFalse(c['outcome_same'])
        self.assertEqual(c['first_divergent_round'], 5)
        self.assertNotIn('candidate_fuel_overhead', c)
        s = eq.summarize([c])
        self.assertEqual((s['divergent_cells'], s['outcome_flips'], s['all_actions_identical']), (1, 1, False))


if __name__ == '__main__':
    unittest.main()
