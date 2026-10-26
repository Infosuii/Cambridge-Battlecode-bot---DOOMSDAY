"""Promotion gate for trained candidates (docs/neural-framework/EVALUATION_PROTOCOL.md section 5).

`evaluate(candidate, baseline, gate_cfg, incumbent=None, ...)` -> GateResult. A candidate passes only if EVERY check
passes; pooled improvement can never compensate for a per-opponent failure (the phase-2 failure mode: pooled 40/60 ->
45/60 while the original fell 10/12 -> 6/12).

Inputs are results documents written by tools/eval_run.py (`rows` = per-cell dicts with opponent/map/side/win/gems/
opponent_gems/faults/fuel_exhausted/...). `baseline` = the ORIGINAL in the candidate's seat on the identical cells
(teacher baseline). `incumbent` = the currently promoted candidate on the identical cells, if one exists.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from . import stats


@dataclass
class GateResult:
    passed: bool
    mode: str
    reasons: list[str] = field(default_factory=list)
    checks: list[dict] = field(default_factory=list)
    tables: dict = field(default_factory=dict)
    labels: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return dict(passed=self.passed, verdict='PASS' if self.passed else 'FAIL', mode=self.mode,
                    reasons=self.reasons, checks=self.checks, tables=self.tables, labels=self.labels)


class _Checks:
    def __init__(self):
        self.items: list[dict] = []

    def add(self, name: str, ok: bool, value=None, threshold=None, detail: str = ''):
        self.items.append(dict(name=name, passed=bool(ok), value=value, threshold=threshold, detail=detail))
        return ok

    def failures(self) -> list[str]:
        return [f"{c['name']}: value {c['value']!r} vs threshold {c['threshold']!r}" + (f" ({c['detail']})" if c['detail'] else '')
                for c in self.items if not c['passed']]


def _rows(doc) -> list[dict]:
    return doc['rows'] if isinstance(doc, dict) else list(doc)


def _keys(rows) -> set:
    return {stats.cell_key(r) for r in rows}


def _telemetry_invalid(rows) -> int:
    n = 0
    for r in rows:
        t = r.get('telemetry') or {}
        n += int(t.get('totals', {}).get('invalid', 0) or 0)
    return n


def evaluate(candidate, baseline, gate_cfg: dict, incumbent=None, mode: str = 'final',
             expected_cells: list[dict] | None = None, ledger_entry: dict | None = None,
             candidate_sha256: str | None = None, reference_shas: dict | None = None) -> GateResult:
    cfg = gate_cfg
    ck = _Checks()
    cand_rows, base_rows = _rows(candidate), _rows(baseline)
    inc_rows = _rows(incumbent) if incumbent is not None else None
    alpha, n_boot, seed = cfg['alpha_one_sided'], cfg['n_boot'], cfg['seed']
    primary = cfg['primary_reference']
    required = list(cfg['required_opponents'])

    # ---- provenance / procedure
    if isinstance(candidate, dict) and isinstance(baseline, dict):
        cs, bs = candidate.get('schedule'), baseline.get('schedule')
        ck.add('schedule_matches_mode', cs == mode and bs == mode, [cs, bs], mode,
               'candidate and teacher baseline must both come from the gate schedule')
        cp, bp = candidate.get('provenance', {}), baseline.get('provenance', {})
        if candidate_sha256:
            ck.add('candidate_identity', cp.get('candidate_sha256') == candidate_sha256, cp.get('candidate_sha256'),
                   candidate_sha256)
        if reference_shas:
            ck.add('teacher_baseline_is_original', bp.get('candidate_sha256') == reference_shas.get(primary),
                   bp.get('candidate_sha256'), reference_shas.get(primary))
            for doc_name, prov in (('candidate', cp), ('baseline', bp)):
                refs = prov.get('reference_sha256', {})
                ck.add(f'{doc_name}_reference_binaries_frozen',
                       all(refs.get(k) == v for k, v in reference_shas.items() if k in required),
                       {k: refs.get(k) for k in required}, 'protocol reference sha256')
        if candidate.get('protocol_sha256') and baseline.get('protocol_sha256'):
            ck.add('same_protocol', candidate['protocol_sha256'] == baseline['protocol_sha256'],
                   candidate['protocol_sha256'][:12], baseline['protocol_sha256'][:12])
    if mode == 'final':
        ok = ledger_entry is not None and ledger_entry.get('event') == 'final_reserved' and \
            (candidate_sha256 is None or ledger_entry.get('candidate_sha256') == candidate_sha256)
        ck.add('final_ledger_reservation', ok, ledger_entry.get('seq') if ledger_entry else None, 'reservation',
               'final benchmark must be reserved in evaluation/ledger.jsonl before it is run')
        if ledger_entry and ledger_entry.get('override'):
            ck.add('final_override_recorded', True, ledger_entry['override'].get('reason'), 'reported',
                   'this candidate/family had a previous final evaluation')

    # ---- completeness and identical cells
    if expected_cells is not None:
        exp = {(c['opponent'], c['map'], c['side']) for c in expected_cells}
        ck.add('candidate_cells_complete', _keys(cand_rows) == exp, len(_keys(cand_rows)), len(exp))
        ck.add('baseline_cells_complete', _keys(base_rows) == exp, len(_keys(base_rows)), len(exp))
    ck.add('paired_cells_identical', _keys(cand_rows) == _keys(base_rows), len(_keys(cand_rows)), len(_keys(base_rows)))
    opps = sorted({r['opponent'] for r in cand_rows})
    ck.add('all_required_opponents_present', all(o in opps for o in required), opps, required)
    if not all(c['passed'] for c in ck.items if c['name'] in ('paired_cells_identical', 'all_required_opponents_present')):
        return GateResult(False, mode, ck.failures(), ck.items, {}, _labels())

    # ---- validity
    ev = cfg.get('engine_version')
    if ev:
        bad = sorted({r.get('engine') for r in cand_rows + base_rows} - {ev})
        ck.add('engine_version', not bad, bad or ev, ev)
    faults = sum(int(r.get('faults', 0)) for r in cand_rows)
    ck.add('candidate_bot_faults', faults <= cfg['faults_max'], faults, cfg['faults_max'])
    codes = sum(len(r.get('diagnostics_codes', []) or []) for r in cand_rows)
    ck.add('engine_diagnostics_codes', codes == 0, codes, 0)
    inv = _telemetry_invalid(cand_rows)
    ck.add('invalid_actions_telemetry', inv <= cfg['invalid_actions_max'], inv, cfg['invalid_actions_max'],
           'release builds carry no telemetry; invalid actions are covered by the dev plumbing check')

    # ---- paired statistics vs the teacher baseline (original in the candidate seat)
    tab = stats.paired_table(cand_rows, base_rows, n_boot, seed, alpha)
    tables = dict(vs_teacher_baseline=tab, candidate=stats.opponent_table(cand_rows),
                  teacher_baseline=stats.opponent_table(base_rows))
    _opponent_rules(ck, tab, required, primary, cfg['original'], cfg['other_references'], 'teacher')
    pooled = tab['win']['__pooled__']
    ck.add('benefit_pooled_d_win_lower', pooled['one_sided_lower'] > cfg['benefit']['pooled_d_win_lower_gt'],
           round(pooled['one_sided_lower'], 4), f"> {cfg['benefit']['pooled_d_win_lower_gt']}",
           'equal-weight mean over opponents, joint map bootstrap; benefit must be established, never traded '
           'against a per-opponent failure')

    # ---- incumbent (previously promoted candidate), if any
    if inc_rows is not None:
        if _keys(inc_rows) != _keys(cand_rows):
            ck.add('incumbent_cells_identical', False, len(_keys(inc_rows)), len(_keys(cand_rows)))
        else:
            itab = stats.paired_table(cand_rows, inc_rows, n_boot, seed, alpha)
            tables['vs_incumbent'] = itab
            tables['incumbent'] = stats.opponent_table(inc_rows)
            _opponent_rules(ck, itab, required, primary, cfg['incumbent']['original'],
                            cfg['incumbent']['other_references'], 'incumbent', margin=False)

    # ---- fuel constraints (official fuelExhausted entries)
    fc = cfg['fuel']
    ce = sum(int(r.get('fuel_exhausted', 0)) for r in cand_rows)
    be = sum(int(r.get('fuel_exhausted', 0)) for r in base_rows)
    cg = sum(1 for r in cand_rows if int(r.get('fuel_exhausted', 0)) > 0)
    bg = sum(1 for r in base_rows if int(r.get('fuel_exhausted', 0)) > 0)
    lim_e = fc['entries_ratio_max'] * be + fc['entries_slack']
    lim_g = fc['games_ratio_max'] * bg + fc['games_slack']
    ck.add('fuel_exhausted_entries', ce <= lim_e, ce, round(lim_e, 2), f'teacher baseline {be}')
    ck.add('games_with_fuel_exhaustion', cg <= lim_g, cg, round(lim_g, 2), f'teacher baseline {bg}')
    tables['fuel_tail'] = _fuel_tail(cand_rows, base_rows)

    passed = all(c['passed'] for c in ck.items)
    return GateResult(passed, mode, ck.failures(), ck.items, tables, _labels())


def _opponent_rules(ck: _Checks, tab: dict, required, primary, primary_cfg, other_cfg, against: str,
                    margin: bool = True):
    for o in required:
        w = tab['win'][o]
        c = primary_cfg if o == primary else other_cfg
        ck.add(f'{against}:{o}:d_win_point', w['point'] >= c['d_win_point_min'], round(w['point'], 4),
               f">= {c['d_win_point_min']}")
        ck.add(f'{against}:{o}:d_win_one_sided_lower', w['one_sided_lower'] >= c['d_win_lower_min'],
               round(w['one_sided_lower'], 4), f">= {c['d_win_lower_min']}",
               f"{w['n_map_clusters']} map clusters, joint bootstrap")
        if margin and 'd_margin_lower_min' in c:
            m = tab['margin'][o]
            ck.add(f'{against}:{o}:d_margin_one_sided_lower', m['one_sided_lower'] >= c['d_margin_lower_min'],
                   round(m['one_sided_lower'], 2), f">= {c['d_margin_lower_min']}")


def _fuel_tail(cand_rows, base_rows) -> dict:
    """Report-only per-turn tail from the inferred .fuel member (see fuel.py)."""
    def agg(rows):
        p999 = [r['fuel_turns'].get('p999') for r in rows if isinstance(r.get('fuel_turns'), dict) and r['fuel_turns'].get('p999') is not None]
        mx = [r['fuel_turns'].get('max') for r in rows if isinstance(r.get('fuel_turns'), dict) and r['fuel_turns'].get('max') is not None]
        cap = [r['fuel_turns'].get('at_cap', 0) for r in rows if isinstance(r.get('fuel_turns'), dict)]
        return dict(cells=len(p999), median_p999=sorted(p999)[len(p999) // 2] if p999 else None,
                    max=max(mx) if mx else None, at_cap_turns=sum(c or 0 for c in cap))
    return dict(candidate=agg(cand_rows), teacher_baseline=agg(base_rows), note='report-only (inferred format)')


def _labels() -> dict:
    return dict(maps='reused_benchmark: every local map was used by previous experiments; results are local '
                     'deterministic benchmark evidence, not ladder strength',
                independence='maps are the resampling clusters; side/opponent cells are not independent; '
                             're-running a deterministic cell adds no sample')


def evaluate_files(candidate_results, baseline_results, incumbent_results=None, mode: str = 'final',
                   ledger_path=None, verify_protocol: bool = True) -> GateResult:
    """File-level entry point used by tools/eval_report.py --gate and by Agent G's `promote` command."""
    from . import ledger as ledger_mod
    from . import protocol as proto
    p = proto.load(verify=verify_protocol)
    cand = json.loads(Path(candidate_results).read_text(encoding='utf-8'))
    base = json.loads(Path(baseline_results).read_text(encoding='utf-8'))
    inc = json.loads(Path(incumbent_results).read_text(encoding='utf-8')) if incumbent_results else None
    sched = proto.load_schedule(mode, verify=verify_protocol)
    sha = cand.get('provenance', {}).get('candidate_sha256')
    entry = None
    if mode == 'final':
        led = ledger_mod.Ledger(ledger_path or proto.LEDGER, p['gate']['override_reason_min_chars'])
        led.verify()
        entry = led.reservation(sha) if sha else None
    res = evaluate(cand, base, p['gate'], inc, mode, sched['cells'], entry, sha,
                   {k: v['wasm_sha256'] for k, v in p['references'].items()})
    res.labels['protocol_sha256'] = proto.protocol_sha256()
    res.labels['candidate_results_sha256'] = hashlib.sha256(Path(candidate_results).read_bytes()).hexdigest()
    return res
