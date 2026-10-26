"""Teacher-equivalence fixtures (Agent A): run a candidate bot on a fixed schedule and compare every cell with the
original-reference result for the same (map, side, opponent).

    # reference digests (original.wasm as the candidate); writes tests/fixtures/teacher/reference_digests.json
    python tools/audit_equivalence.py reference [--workers 4]
    # compare a candidate wasm (or a bot dir, built with the official CLI) with the reference digests
    python tools/audit_equivalence.py compare --candidate X.wasm --label NAME [--opponents original] [--maps 6] [--out R.json]
    python tools/audit_equivalence.py compare --bot-dir artifacts/tmp/A/x/bot --label NAME ...

Comparison levels per cell (strongest first), all exact:
  replay   sha256 of the bundle's replay.repl26a (verified to contain no bot names, paths or timestamps; see
           archive/agents/A/REPORT.md) - every engine-visible action of both teams.
  summary  sha256 of the canonical (sort_keys) summary JSON: outcome, rounds, scores, per-champion metrics, timelines,
           events (including fuelExhausted).
  fuel     sha256 of the candidate team's per-turn fuel trace (team-<x>.fuel): identical fuel use on every turn.
  stdout   sha256 of the candidate team's stdout.
A cell is `equal` when replay and summary are equal; the other levels are reported for diagnosis (a candidate that
legitimately differs in fuel use, e.g. a stripped lab build, can be behaviour-identical with a different fuel trace).
Matches are official CLI, --release, default fuel (python/nfs/engine.py). Completed cells are cached by folder.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from nfs import engine  # noqa: E402

FIX = ROOT / 'tests/fixtures/teacher'
SCHEDULE = FIX / 'schedule.json'
REFERENCE = FIX / 'reference_digests.json'
RUNS = ROOT / 'artifacts/tmp/A/eq'
BUILDS = ROOT / 'references/builds'
MAX_WORKERS = 4  # CONTRACTS / lead instruction: at most 4 concurrent engine matches


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def default_schedule() -> dict:
    """12 maps chosen deterministically from engine.maps() (sorted names, evenly spaced indices), both sides,
    opponents original and v47."""
    names = [m.stem for m in engine.maps()]
    n = len(names)
    idx = [i * n // 12 for i in range(12)]
    return {
        '_doc': 'Teacher-equivalence fixture schedule (Agent A). Maps = sorted engine.maps() names at indices i*n//12, '
                'i=0..11. Cell = (map, candidate side, opponent). Official CLI, --release, default fuel.',
        'version': 1,
        'n_maps_available': n,
        'map_indices': idx,
        'maps': [names[i] for i in idx],
        'sides': ['A', 'B'],
        'opponents': {'original': 'references/builds/original.wasm', 'v47': 'references/builds/v47.wasm'},
        'reference_candidate': 'references/builds/original.wasm',
    }


def load_schedule() -> dict:
    if not SCHEDULE.exists():
        engine.write_json(SCHEDULE, default_schedule())
    return json.loads(SCHEDULE.read_text(encoding='utf-8'))


def cells(schedule: dict, opponents=None, n_maps=None) -> list[dict]:
    out = []
    maps = schedule['maps'][: n_maps or None]
    for m in maps:
        for opp in (opponents or list(schedule['opponents'])):
            for side in schedule['sides']:
                out.append({'map': m, 'side': side, 'opponent': opp, 'key': f'{m}|{side}|{opp}'})
    return out


def digest(folder: Path, side: str) -> dict:
    folder = Path(folder)
    me, them = side.lower(), ('b' if side == 'A' else 'a')
    summ = json.loads((folder / 'summary.json').read_text(encoding='utf-8'))
    replay = engine.read_bundle_member(folder, 'replay.repl26a')
    if not replay:
        raise RuntimeError(f'no replay in {folder}')
    res = engine.parse_summary(summ, folder, folder.name, side)
    teams = {t['team']: int(t['submittedGems']) for t in summ['teams']}
    return {
        'replay_sha256': _sha(replay),
        'replay_bytes': len(replay),
        'summary_sha256': _sha(json.dumps(summ, sort_keys=True, separators=(',', ':')).encode()),
        'fuel_candidate_sha256': _sha(engine.read_bundle_member(folder, f'team-{me}.fuel')),
        'fuel_opponent_sha256': _sha(engine.read_bundle_member(folder, f'team-{them}.fuel')),
        'stdout_candidate_sha256': _sha(engine.read_bundle_member(folder, f'team-{me}.stdout')),
        'core': {'outcome': summ['match']['outcome'], 'rounds_started': int(summ['match']['roundsStarted']),
                 'rounds_completed': int(summ['match']['roundsCompleted']), 'seed': summ['match']['seed'],
                 'map_hash': summ['match']['mapHash'], 'engine': summ['match']['engineVersion'],
                 'submitted': teams, 'candidate_win': res.win, 'candidate_gems': res.gems,
                 'opponent_gems': res.opponent_gems, 'candidate_faults': res.faults,
                 'candidate_fuel_exhausted': res.fuel_exhausted, 'opponent_fuel_exhausted': res.opponent_fuel_exhausted,
                 'candidate_deaths': res.deaths},
    }


def run_cells(candidate: Path, label: str, todo: list[dict], schedule: dict, workers: int) -> dict:
    run_dir = RUNS / label
    run_dir.mkdir(parents=True, exist_ok=True)
    cand = run_dir / 'candidate.wasm'  # fixed name: the bundle file name carries the wasm stem
    if not cand.exists() or engine.sha256(cand) != engine.sha256(candidate):
        shutil.copyfile(candidate, cand)
    maps = {m.stem: m for m in engine.maps()}

    def one(c):
        opp = ROOT / schedule['opponents'][c['opponent']]
        folder = run_dir / f"{c['map']}-{c['side']}-{c['opponent']}"
        a, b = (cand, opp) if c['side'] == 'A' else (opp, cand)
        if not (folder / 'summary.json').exists() and folder.exists():
            shutil.rmtree(folder)  # incomplete earlier attempt
        engine.run_match(a, b, maps[c['map']], folder, c['side'])
        return c['key'], digest(folder, c['side'])

    out = {}
    with cf.ThreadPoolExecutor(max_workers=max(1, min(workers, MAX_WORKERS))) as ex:
        for key, d in ex.map(one, todo):
            out[key] = d
    return out


LEVELS = [('replay', 'replay_sha256'), ('summary', 'summary_sha256'), ('fuel', 'fuel_candidate_sha256'),
          ('fuel_opponent', 'fuel_opponent_sha256'), ('stdout', 'stdout_candidate_sha256')]


def compare_digests(got: dict, ref: dict) -> dict:
    per = {}
    for key, d in got.items():
        r = ref.get(key)
        if r is None:
            per[key] = {'equal': None, 'reason': 'no reference digest'}
            continue
        lv = {name: d[k] == r[k] for name, k in LEVELS}
        per[key] = {'equal': lv['replay'] and lv['summary'], 'levels': lv, 'core': d['core'], 'reference_core': r['core']}
    n = [v for v in per.values() if v['equal'] is not None]
    return {
        'cells': per,
        'n_cells': len(n),
        'n_equal': sum(1 for v in n if v['equal']),
        'n_different': sum(1 for v in n if not v['equal']),
        'level_counts': {name: sum(1 for v in n if v['levels'][name]) for name, _ in LEVELS},
        'outcome_changes': sum(1 for v in n if v['core']['outcome'] != v['reference_core']['outcome']),
        'candidate_wins': sum(v['core']['candidate_win'] for v in n),
        'reference_wins': sum(v['reference_core']['candidate_win'] for v in n),
    }


def cmd_reference(a) -> int:
    sch = load_schedule()
    ref_wasm = ROOT / sch['reference_candidate']
    todo = cells(sch)
    got = run_cells(ref_wasm, a.label, todo, sch, a.workers)
    data = {'_doc': 'Reference digests: references/builds/original.wasm as the candidate on every schedule cell '
                    '(tools/audit_equivalence.py reference). Keys: map|candidate side|opponent.',
            'cli': engine.cli_version(), 'candidate_wasm_sha256': engine.sha256(ref_wasm),
            'candidate_code_sha256': engine.code_section_sha(ref_wasm),
            'opponents': {k: {'path': v, 'wasm_sha256': engine.sha256(ROOT / v)} for k, v in sch['opponents'].items()},
            'schedule_sha256': engine.sha256(SCHEDULE), 'run_label': a.label, 'cells': got}
    engine.write_json(REFERENCE, data)
    print(f'wrote {REFERENCE} ({len(got)} cells)')
    return 0


def cmd_compare(a) -> int:
    sch = load_schedule()
    ref = json.loads(REFERENCE.read_text(encoding='utf-8'))
    if a.bot_dir:
        cand = engine.official_build(ROOT / a.bot_dir, RUNS / a.label / 'built.wasm')
    else:
        cand = Path(a.candidate).resolve()
    todo = cells(sch, a.opponents.split(',') if a.opponents else None, a.maps)
    got = run_cells(cand, a.label, todo, sch, a.workers)
    rep = compare_digests(got, ref['cells'])
    rep.update({'label': a.label, 'candidate': str(cand), 'candidate_wasm_sha256': engine.sha256(cand),
                'candidate_code_sha256': engine.code_section_sha(cand),
                'candidate_code_identical_to_reference': engine.code_section_sha(cand) == ref['candidate_code_sha256'],
                'reference_run_label': ref.get('run_label')})
    out = Path(a.out) if a.out else RUNS / a.label / 'equivalence_report.json'
    engine.write_json(ROOT / out if not out.is_absolute() else out, rep)
    print(json.dumps({k: rep[k] for k in ('label', 'n_cells', 'n_equal', 'n_different', 'level_counts', 'outcome_changes',
                                         'candidate_wins', 'reference_wins', 'candidate_code_identical_to_reference')}, indent=1))
    print('report:', out)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('reference')
    r.add_argument('--label', default='reference')
    r.add_argument('--workers', type=int, default=MAX_WORKERS)
    c = sub.add_parser('compare')
    g = c.add_mutually_exclusive_group(required=True)
    g.add_argument('--candidate')
    g.add_argument('--bot-dir')
    c.add_argument('--label', required=True)
    c.add_argument('--opponents', help='comma-separated subset of schedule opponents')
    c.add_argument('--maps', type=int, help='first N schedule maps only')
    c.add_argument('--workers', type=int, default=MAX_WORKERS)
    c.add_argument('--out')
    sub.add_parser('schedule')
    a = ap.parse_args(argv)
    if a.cmd == 'reference':
        return cmd_reference(a)
    if a.cmd == 'compare':
        return cmd_compare(a)
    print(json.dumps(load_schedule(), indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
