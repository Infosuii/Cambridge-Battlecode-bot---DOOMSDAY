"""Freeze development-only draft overrides against the actual incumbent table.

Candidate 0 is the global prior, not the incumbent map-conditioned policy.
Both sides are paired. Best-of-eight gains are optimistic, not confirmation.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def choose(baseline, candidates, incumbent, development, margin):
    if not math.isfinite(margin) or margin < 0:
        raise ValueError('margin must be finite and nonnegative')
    if set(candidates) != set(range(8)) or not development or not development <= set(baseline):
        raise ValueError('need all eight variants and an incumbent for every development map')
    if any(set(scores) != development for scores in candidates.values()):
        raise ValueError('candidate maps must be exactly the development set; no held-out rows')
    table, detail, noops = {}, {}, {}
    gain = 0
    for m in sorted(development):
        current = incumbent.get(m, 0)
        if candidates[current][m] != baseline[m]:
            noops[m] = dict(variant=current, incumbent=baseline[m], global_trial=candidates[current][m])
        # An unchanged lineup cannot be selected for compiler/layout variation.
        options = [(baseline[m], current)] + [(s[m], v) for v, s in candidates.items() if v != current]
        score, variant = max(options, key=lambda pair: (pair[0], pair[1] == current, -pair[1]))
        selected = variant != current and score - baseline[m] >= margin
        if selected:
            table[m] = variant
            gain += score - baseline[m]
        detail[m] = dict(incumbent_variant=current, incumbent_margin=baseline[m],
                         global_margins={str(v): s[m] for v, s in candidates.items()},
                         selected_variant=variant if selected else current,
                         selected_margin=score if selected else baseline[m])
    return dict(table=table, maps_changed=len(table), development_maps=len(development),
                in_sample_gain_per_game=gain / (2 * len(development)),
                same_lineup_differences=noops, per_map=detail,
                caution='Best-of-eight deterministic development gains are optimistic. Confirm frozen overrides against another opponent.')


def load_run(name):
    folder = ROOT / 'research/dz/runs' / name
    provenance = json.loads((folder / 'provenance.json').read_text(encoding='utf-8'))
    results = json.loads((folder / 'results.json').read_text(encoding='utf-8'))
    if not provenance['release'] or provenance['trace'] or provenance['diagnostic']:
        raise ValueError('draft selection requires release strength matches')
    cells, scores = {}, {}
    for row in results['per_game']:
        cell = row['map'], row['side']
        if cell in cells or cell[1] not in ('A', 'B'):
            raise ValueError('duplicate or invalid map-side cell')
        if any(row[k] for k in ('faults', 'fuel_outs', 'opponent_faults')):
            raise ValueError('runtime failure is not selectable')
        if (row['candidate_sha256'] != provenance['candidate_sha256'] or
                row['opponent_sha256'] != provenance['opponent_sha256'] or
                row['map_sha256'] != provenance['maps'][cell[0]]):
            raise ValueError('cell/provenance identity mismatch')
        cells[cell] = row
        scores[cell[0]] = scores.get(cell[0], 0) + row['banked'] - row['opponent_banked']
    if not cells or any((m, side) not in cells for m in scores for side in ('A', 'B')):
        raise ValueError('both sides are required for every map')
    if len(cells) != results['games']:
        raise ValueError('incomplete result count')
    return provenance, cells, scores


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', required=True)
    p.add_argument('--candidates', nargs=8, required=True, help='eight ID=RUN pairs')
    p.add_argument('--incumbent', type=Path, default=ROOT / 'bots/dz/src/map_drafts.inc')
    p.add_argument('--margin', type=float, default=100)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError('refuse to overwrite a frozen selection')
    pairs = [s.split('=', 1) for s in a.candidates]
    if any(len(pair) != 2 for pair in pairs):
        p.error('provide ID=RUN pairs')
    runs = {int(v): run for v, run in pairs}
    if len(runs) != 8 or set(runs) != set(range(8)):
        p.error('provide each variant 0..7 exactly once')
    pool = sorted(x.stem for x in (ROOT / 'maps/local-benchmarks').glob('*.map26a'))
    if len(pool) != 70:
        raise ValueError('expected the registered 70-map pool')
    heldout = set(pool[4::5])
    development = set(pool) - heldout
    rows = re.findall(r'\{\s*\d+u,\s*(\d+)\s*\},\s*//\s*(\S+)', a.incumbent.read_text(encoding='utf-8'))
    incumbent = {name: int(v) for v, name in rows}
    if len(incumbent) != len(rows) or not set(incumbent) <= set(pool) or any(v not in range(8) for v in incumbent.values()):
        raise ValueError('invalid incumbent table')
    bp, bcells, baseline = load_run(a.baseline)
    if set(baseline) != set(pool):
        raise ValueError('incumbent needs the complete registered pool')
    candidates, evidence = {}, {}
    for variant, run in sorted(runs.items()):
        cp, cells, scores = load_run(run)
        if any(cp[k] != bp[k] for k in ('opponent_sha256', 'sdk', 'cli_sha256')):
            raise ValueError('opponent, SDK and CLI must match the incumbent')
        for cell, row in cells.items():
            if cell not in bcells or any(row[k] != bcells[cell][k] for k in ('map_sha256', 'engine', 'engine_hash')):
                raise ValueError('map/engine mismatch')
        capsule = ROOT / 'research/dz/runs' / run / 'evidence.zip'
        with zipfile.ZipFile(capsule) as z:
            config = z.read('build/candidate/src/config.h').decode('utf-8')
        required = dict(DZ_DRAFT_VARIANT=variant, DZ_MAP_DRAFT_TABLE=0, DZ_CARRIER_BANK_PRIORITY=1,
                        DZ_TRACE=0, DZ_MAP_DRAFT_EXTRA=0, DZ_MAP_DRAFT_MATRIX=0, DZ_JOB_GEAR=0,
                        DZ_CLEAR_TIME_CLOCK=0, DZ_CLEAR_TIME_WORK_ONLY=0, DZ_BANK_AWARE_RATE=0,
                        DZ_ENGAGE_IN_RANGE=0, DZ_GEM_TARGET_PRIORITY=0, DZ_CAPTURE_GEAR=0, DZ_CAPTURE_FOURTH=0)
        for key, value in required.items():
            match = re.search(r'^#define\s+' + key + r'\s+(\d+)\b', config, re.M)
            if not match or int(match[1]) != value:
                raise ValueError(f'{run}: unexpected frozen {key}')
        candidates[variant] = scores
        evidence[str(variant)] = dict(run=run, capsule_sha256=hashlib.sha256(capsule.read_bytes()).hexdigest(),
                                      candidate_sha256=cp['candidate_sha256'])
    report = choose(baseline, candidates, incumbent, development, a.margin)
    report.update(created_utc=dt.datetime.now(dt.timezone.utc).isoformat(), baseline=a.baseline,
                  baseline_sha256=bp['candidate_sha256'], opponent_sha256=bp['opponent_sha256'],
                  incumbent_table_sha256=hashlib.sha256(a.incumbent.read_bytes()).hexdigest(),
                  held_out_maps=sorted(heldout), selection_margin=a.margin, evidence=evidence)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: report[k] for k in ('table', 'maps_changed', 'in_sample_gain_per_game', 'caution')}, indent=2))


if __name__ == '__main__':
    main()
