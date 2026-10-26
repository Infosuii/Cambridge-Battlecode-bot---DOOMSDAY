"""Append-only, hash-chained ledger of final-benchmark use (evaluation/ledger.jsonl).

Rules (docs/neural-framework/EVALUATION_PROTOCOL.md 5.4):
* A candidate (wasm sha256) gets ONE final evaluation; a candidate family (training run / lineage id) gets ONE final
  evaluation. A second final evaluation of the same sha256 or of any member of an already-evaluated family is
  refused unless a reason (>= min chars) is supplied; the override and its reason are recorded and reported.
* Lines are never rewritten. Each line carries `prev` = sha256 of the previous line's bytes; `verify()` detects edits,
  deletions and reordering.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

GENESIS = '0' * 64


class LedgerRefusal(RuntimeError):
    pass


class LedgerCorrupt(RuntimeError):
    pass


class Ledger:
    def __init__(self, path, min_reason_chars: int = 20):
        self.path = Path(path)
        self.min_reason_chars = min_reason_chars

    def _lines(self) -> list[bytes]:
        if not self.path.exists():
            return []
        return [x for x in self.path.read_bytes().split(b'\n') if x.strip()]

    def entries(self) -> list[dict]:
        return [json.loads(x) for x in self._lines()]

    def verify(self) -> int:
        prev = GENESIS
        for i, raw in enumerate(self._lines()):
            e = json.loads(raw)
            if e.get('seq') != i or e.get('prev') != prev:
                raise LedgerCorrupt(f'ledger chain broken at line {i}')
            prev = hashlib.sha256(raw).hexdigest()
        return len(self._lines())

    def _append(self, entry: dict) -> dict:
        lines = self._lines()
        self.verify()
        entry = dict(seq=len(lines), prev=hashlib.sha256(lines[-1]).hexdigest() if lines else GENESIS,
                     ts=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), **entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, 'ab') as f:
            f.write(json.dumps(entry, sort_keys=True, ensure_ascii=False).encode('utf-8') + b'\n')
        return entry

    def finals_for(self, candidate_sha256: str | None = None, family: str | None = None) -> list[dict]:
        out = []
        for e in self.entries():
            if e.get('event') != 'final_reserved':
                continue
            if (candidate_sha256 and e.get('candidate_sha256') == candidate_sha256) or (family and e.get('family') == family):
                out.append(e)
        return out

    def reserve_final(self, candidate_sha256: str, family: str, protocol_sha256: str, schedule: str = 'final',
                      reason: str | None = None, label: str = '') -> dict:
        """Reserve the final benchmark for a candidate BEFORE any final match runs. Raises LedgerRefusal."""
        if not candidate_sha256 or len(candidate_sha256) != 64:
            raise LedgerRefusal('candidate sha256 required')
        if not family:
            raise LedgerRefusal('candidate family (training run / lineage id) required')
        prior = self.finals_for(candidate_sha256, family)
        override = None
        if prior:
            why = ', '.join(f"seq {p['seq']} ({'same candidate' if p['candidate_sha256'] == candidate_sha256 else 'same family'})"
                            for p in prior)
            if not reason or len(reason.strip()) < self.min_reason_chars:
                raise LedgerRefusal(f'final benchmark already used: {why}; a second final evaluation requires a '
                                    f'recorded reason of >= {self.min_reason_chars} characters')
            override = dict(prior_seq=[p['seq'] for p in prior], reason=reason.strip())
        return self._append(dict(event='final_reserved', candidate_sha256=candidate_sha256, family=family,
                                 schedule=schedule, protocol_sha256=protocol_sha256, label=label,
                                 override=override, nth_final_for_family=len([p for p in prior if p['family'] == family]) + 1))

    def record_result(self, reservation_seq: int, candidate_sha256: str, passed: bool | None, results_sha256: str,
                      summary: dict | None = None) -> dict:
        res = [e for e in self.entries() if e.get('seq') == reservation_seq and e.get('event') == 'final_reserved']
        if not res or res[0]['candidate_sha256'] != candidate_sha256:
            raise LedgerRefusal('no matching final reservation')
        return self._append(dict(event='final_result', reservation_seq=reservation_seq,
                                 candidate_sha256=candidate_sha256, passed=passed, results_sha256=results_sha256,
                                 summary=summary or {}))

    def record_verdict(self, reservation_seq: int, candidate_sha256: str, passed: bool, gate_sha256: str,
                       reasons: list[str]) -> dict:
        res = [e for e in self.entries() if e.get('seq') == reservation_seq and e.get('event') == 'final_reserved']
        if not res or res[0]['candidate_sha256'] != candidate_sha256:
            raise LedgerRefusal('no matching final reservation')
        return self._append(dict(event='gate_verdict', reservation_seq=reservation_seq,
                                 candidate_sha256=candidate_sha256, passed=bool(passed), gate_sha256=gate_sha256,
                                 reasons=reasons[:20]))

    def reservation(self, candidate_sha256: str) -> dict | None:
        r = [e for e in self.entries() if e.get('event') == 'final_reserved' and e['candidate_sha256'] == candidate_sha256]
        return r[-1] if r else None
