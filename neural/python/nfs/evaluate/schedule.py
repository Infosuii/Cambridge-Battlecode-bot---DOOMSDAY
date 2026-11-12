"""Run a frozen schedule for a candidate wasm against the frozen reference builds.

* Jobs are built from evaluation/schedules/<name>.json and run with nfs.engine.run_jobs (official CLI, --release,
  default fuel). Concurrency is capped at 4 engine matches.
* Match folders are content-addressed inside a results label: `<map>__<sha(A)[:12]>__<sha(B)[:12]>[__r<k>]`. The
  same (wasm A, wasm B, map) is one deterministic match, so e.g. original-vs-original side A and side B share one
  folder and are never run or counted twice. A completed folder (summary.json) is a cache hit.
* Every cell row is labelled `reused_benchmark` (all local maps were used before).
"""
from __future__ import annotations

import json
from pathlib import Path

from .. import engine
from . import fuel as fuel_mod
from . import protocol as proto

MAX_WORKERS = 4


class ScheduleError(RuntimeError):
    pass


def reference_wasm(name: str) -> Path:
    return engine.ROOT / 'references' / 'builds' / f'{name}.wasm'


def check_references(protocol: dict, names=None) -> dict[str, str]:
    """Reference binary preservation: current sha256 must equal the frozen protocol value."""
    out = {}
    for name, ref in protocol['references'].items():
        if names and name not in names:
            continue
        sha = engine.sha256(engine.ROOT / ref['wasm'])
        if sha != ref['wasm_sha256']:
            raise ScheduleError(f'reference {name} changed: {sha} != frozen {ref["wasm_sha256"]}')
        out[name] = sha
    return out


def map_path(name: str) -> Path:
    p = engine.MAPS / f'{name}.map26a'
    if not p.exists():
        raise ScheduleError(f'map not found: {p}')
    return p


def match_folder(match_root: Path, map_name: str, wasm_a_sha: str, wasm_b_sha: str, rep: int | None) -> Path:
    tail = f'__r{rep}' if rep is not None else ''
    return Path(match_root) / f'{map_name}__{wasm_a_sha[:12]}__{wasm_b_sha[:12]}{tail}'


def plan(schedule: dict, candidate_wasm, match_root, ref_shas: dict[str, str]) -> list[dict]:
    """Expand cells -> list of {cell..., job...}. Jobs with identical folders are deduplicated at run time."""
    cand = Path(candidate_wasm).resolve()
    cand_sha = engine.sha256(cand)
    repeats = int(schedule.get('repeats', 1))
    cells = []
    for c in schedule['cells']:
        opp = reference_wasm(c['opponent'])
        opp_sha = ref_shas[c['opponent']]
        a, b, sa, sb = (cand, opp, cand_sha, opp_sha) if c['side'] == 'A' else (opp, cand, opp_sha, cand_sha)
        for rep in range(repeats):
            folder = match_folder(match_root, c['map'], sa, sb, rep if repeats > 1 else None)
            cells.append(dict(cell=dict(c, rep=rep if repeats > 1 else None),
                              job=dict(a=a, b=b, map_path=map_path(c['map']), folder=folder, candidate_side=c['side'])))
    return cells


def run(schedule: dict, candidate_wasm, match_root, protocol: dict, workers: int = MAX_WORKERS) -> list[dict]:
    """Run (or reuse cached) matches for every cell and return per-cell rows."""
    ref_shas = check_references(protocol, {c['opponent'] for c in schedule['cells']})
    cells = plan(schedule, candidate_wasm, match_root, ref_shas)
    unique = {}
    for c in cells:
        unique.setdefault(str(c['job']['folder']), c['job'])
    pending = [j for f, j in unique.items() if not (Path(f) / 'summary.json').exists()]
    workers = max(1, min(MAX_WORKERS, int(workers)))
    if pending:
        engine.run_jobs(pending, workers)
    for f, j in unique.items():
        meta = Path(f) / 'cell.json'
        if not meta.exists():
            engine.write_json(meta, dict(a=str(j['a']), b=str(j['b']), a_sha256=engine.sha256(j['a']),
                                         b_sha256=engine.sha256(j['b']), map=Path(j['map_path']).stem))
        else:  # a cached folder must belong to the same wasm pair (content-addressed names make this a hard check)
            m = json.loads(meta.read_text(encoding='utf-8'))
            if m['a_sha256'] != engine.sha256(j['a']) or m['b_sha256'] != engine.sha256(j['b']):
                raise ScheduleError(f'cached match folder {f} belongs to a different wasm pair')
    newly = {str(p['folder']) for p in pending}
    return [row(c, ran=str(c['job']['folder']) in newly) for c in cells]


def row(c: dict, ran: bool = False) -> dict:
    j, cell = c['job'], c['cell']
    folder = Path(j['folder'])
    summary = json.loads((folder / 'summary.json').read_text(encoding='utf-8'))
    m = engine.parse_summary(summary, folder, cell['map'], cell['side'])
    meta = json.loads((folder / 'cell.json').read_text(encoding='utf-8')) if (folder / 'cell.json').exists() else {}
    team = 'team' + cell['side']
    r = m.row()
    r.update(opponent=cell['opponent'], cluster=cell['map'], rep=cell.get('rep'), map_label=proto.MAP_LABEL,
             margin=m.gems - m.opponent_gems, diagnostics_codes=summary['diagnostics'].get('codes', []),
             opponent_faults=int(summary['diagnostics']['botFaults']['teamB' if cell['side'] == 'A' else 'teamA']),
             engine_build_hash=summary['match'].get('engineBuildHash'), map_hash=summary['match'].get('mapHash'),
             folder=str(folder.relative_to(engine.ROOT)) if folder.is_relative_to(engine.ROOT) else str(folder),
             match_wasm=meta, newly_run=ran)
    try:
        fc = fuel_mod.cell_fuel(folder)
        t = fc['teams'].get(team, {})
        r['fuel_turns'] = {k: t.get(k) for k in ('regular_turns', 'mean', 'p99', 'p999', 'max', 'at_cap', 'over_95pct',
                                                 'layout_consistent', 'cap_turns_match_events') if k in t}
        r['fuel_turns']['first_turn_max'] = t.get('first_turn_max')
        r['fuel_exhausted_rounds'] = fc['events'].get(team, {}).get('rounds', [])
    except Exception as exc:  # noqa: BLE001 - recorded
        r['fuel_turns'] = dict(error=str(exc))
    out = engine.team_stdout(folder, cell['side'])
    if 'NFT1' in out:
        r['telemetry'] = fuel_mod.parse_telemetry(out)
    return r


def summarize(rows: list[dict]) -> dict:
    from . import stats
    engines = sorted({r['engine'] for r in rows})
    return dict(cells=len(rows), engine_matches=len({r['folder'] for r in rows}), engine_versions=engines,
                faults=sum(r['faults'] for r in rows), opponent_faults=sum(r['opponent_faults'] for r in rows),
                diagnostics_codes=sum(len(r['diagnostics_codes']) for r in rows),
                fuel_exhausted_entries=sum(r['fuel_exhausted'] for r in rows),
                games_with_fuel_exhaustion=sum(1 for r in rows if r['fuel_exhausted'] > 0),
                per_opponent=stats.opponent_table(rows), map_label=proto.MAP_LABEL,
                independent_units=f"{len({r['map'] for r in rows})} map clusters (cells are not independent samples)")
