"""Ledger tests: one final evaluation per candidate and per family; overrides need a recorded reason; tamper-evident."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'python'))
from nfs.evaluate import ledger as L  # noqa: E402

A, B = 'a' * 64, 'b' * 64
P = 'p' * 64


class TestLedger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'ledger.jsonl'
        self.led = L.Ledger(self.path, 20)

    def tearDown(self):
        self.tmp.cleanup()

    def test_first_final_allowed_and_chained(self):
        e = self.led.reserve_final(A, 'run-1', P)
        self.assertEqual((e['seq'], e['prev']), (0, L.GENESIS))
        self.led.record_result(0, A, None, 'r' * 64)
        self.assertEqual(self.led.verify(), 2)

    def test_repeat_same_candidate_refused(self):
        self.led.reserve_final(A, 'run-1', P)
        with self.assertRaises(L.LedgerRefusal):
            self.led.reserve_final(A, 'run-1', P)
        with self.assertRaises(L.LedgerRefusal):
            self.led.reserve_final(A, 'run-other', P)  # same sha under another family name

    def test_reselected_family_member_refused(self):
        self.led.reserve_final(A, 'run-1', P)
        with self.assertRaises(L.LedgerRefusal):
            self.led.reserve_final(B, 'run-1', P)  # another checkpoint of the same run

    def test_short_reason_refused_long_reason_recorded(self):
        self.led.reserve_final(A, 'run-1', P)
        with self.assertRaises(L.LedgerRefusal):
            self.led.reserve_final(B, 'run-1', P, reason='retry')
        e = self.led.reserve_final(B, 'run-1', P, reason='engine crashed mid-run; infrastructure failure, no results')
        self.assertEqual(e['override']['prior_seq'], [0])
        self.assertEqual(e['nth_final_for_family'], 2)
        self.assertEqual(len(self.led.finals_for(family='run-1')), 2)

    def test_tampering_detected(self):
        self.led.reserve_final(A, 'run-1', P)
        self.led.reserve_final(B, 'run-2', P)
        lines = self.path.read_bytes().split(b'\n')
        first = json.loads(lines[0])
        first['family'] = 'edited'
        lines[0] = json.dumps(first, sort_keys=True).encode()
        self.path.write_bytes(b'\n'.join(lines))
        with self.assertRaises(L.LedgerCorrupt):
            self.led.verify()
        with self.assertRaises(L.LedgerCorrupt):
            self.led.reserve_final('c' * 64, 'run-3', P)

    def test_deletion_detected(self):
        self.led.reserve_final(A, 'run-1', P)
        self.led.reserve_final(B, 'run-2', P)
        lines = [x for x in self.path.read_bytes().split(b'\n') if x]
        self.path.write_bytes(lines[1] + b'\n')
        with self.assertRaises(L.LedgerCorrupt):
            self.led.verify()

    def test_result_requires_reservation(self):
        with self.assertRaises(L.LedgerRefusal):
            self.led.record_result(0, A, True, 'r' * 64)

    def test_requires_identity(self):
        with self.assertRaises(L.LedgerRefusal):
            self.led.reserve_final('short', 'run', P)
        with self.assertRaises(L.LedgerRefusal):
            self.led.reserve_final(A, '', P)


if __name__ == '__main__':
    unittest.main()
