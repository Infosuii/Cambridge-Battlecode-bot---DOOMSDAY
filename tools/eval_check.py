"""Build-time framework checks (EVALUATION_PROTOCOL.md section 3). Not strength claims.

  python tools/eval_check.py refs
  python tools/eval_check.py repro --results reference/repro
  python tools/eval_check.py equivalence --results <label> --reference reference/equivalence --profile teacher_exact
  python tools/eval_check.py plumbing --results <label>                 # dev_untrained: faults/invalid/counters
  python tools/eval_check.py fuel --results <label> [--baseline reference/fuel_profile]
  python tools/eval_check.py smoke --results <label>

Each writes evaluation/results/<label>/check-<name>.json (refs -> evaluation/results/check-refs.json) and exits 0 on
PASS, 2 on FAIL, 0 for pure measurements (neutral_real).
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from nfs import engine  # noqa: E402
from nfs.evaluate import equivalence as eq  # noqa: E402
from nfs.evaluate import fuel as fuel_mod  # noqa: E402
from nfs.evaluate import protocol as proto  # noqa: E402
from nfs.evaluate import stats  # noqa: E402

STRICT_PROFILES = ('teacher_exact', 'neutral_credit')  # every other profile: divergence is measured and reported


def load(label):
    return json.loads((proto.RESULTS / label / 'results.json').read_text(encoding='utf-8'))


def folder(row) -> Path:
    f = Path(row['folder'])
    return f if f.is_absolute() else engine.ROOT / f


def emit(path: Path, doc: dict, passed):
    engine.write_json(path, doc)
    print(json.dumps({k: v for k, v in doc.items() if k not in ('cells', 'per_cell')}, indent=2, default=str))
    print('wrote', path)
    sys.exit(0 if passed in (True, None) else 2)


def cmd_refs(_a):
    p = proto.load(verify=True)
    man = json.loads((engine.ROOT / 'references/builds/manifest.json').read_text(encoding='utf-8'))['opponents']
    rows, ok = {}, True
    for k, ref in p['references'].items():
        w = engine.ROOT / ref['wasm']
        sha = engine.sha256(w)
        code = engine.code_section_sha(w)
        good = sha == ref['wasm_sha256'] == man[k]['wasm_sha256'] and code == ref['code_section_sha256']
        ok &= good
        rows[k] = dict(sha256=sha, frozen=ref['wasm_sha256'], manifest=man[k]['wasm_sha256'], code_section=code,
                       preserved=good)
    emit(proto.RESULTS / 'check-refs.json', dict(check='reference_preservation', passed=ok, references=rows), ok)


def cmd_repro(a):
    doc = load(a.results)
    groups = defaultdict(dict)
    for r in doc['rows']:
        groups[(r['opponent'], r['map'], r['side'])][r['rep']] = folder(r)
    cells, ok = [], True
    for k, reps in sorted(groups.items()):
        fps = [eq.fingerprint(reps[i]) for i in sorted(reps)]
        same = all(f['members'] == fps[0]['members'] and f.get('summary_sha256') == fps[0].get('summary_sha256')
                   for f in fps[1:]) and len(fps) >= 2 and bool(fps[0]['members'])
        ok &= same
        cells.append(dict(opponent=k[0], map=k[1], side=k[2], repeats=len(fps), identical=same,
                          members=sorted(fps[0]['members']), summary_sha256=fps[0].get('summary_sha256')))
    emit(proto.RESULTS / a.results / 'check-repro.json',
         dict(check='reproducibility', passed=ok and bool(cells), cells=cells,
              note='identical = every replay-bundle member (replay, .fuel, stdout, debug) and summary.json '
                   'byte-identical across repeats; deterministic engine, so repeats are NOT extra samples'),
         ok and bool(cells))


def cmd_equivalence(a):
    cand, ref = load(a.results), load(a.reference)
    if ref['provenance']['candidate_sha256'] != proto.load()['references']['original']['wasm_sha256']:
        sys.exit('reference results must be the original in the candidate seat')
    rmap = {stats.cell_key(r): r for r in ref['rows']}
    per_cell = []
    for r in cand['rows']:
        k = stats.cell_key(r)
        if k not in rmap:
            sys.exit(f'reference has no cell {k}')
        c = eq.compare(folder(r), folder(rmap[k]), 'team' + r['side'])
        c.update(opponent=k[0], map=k[1], side=k[2])
        per_cell.append(c)
    s = eq.summarize(per_cell)
    profile = a.profile or cand['provenance'].get('profile')
    strict = profile in STRICT_PROFILES
    passed = s['all_actions_identical'] and s['summary_identical'] == s['cells'] if strict else None
    over = [c['candidate_fuel_overhead'] for c in per_cell if isinstance(c.get('candidate_fuel_overhead'), dict)
            and 'mean' in c['candidate_fuel_overhead']]
    s['candidate_fuel_overhead_mean_per_turn'] = (sum(o['mean'] for o in over) / len(over)) if over else 0.0
    s['candidate_fuel_overhead_p99_max'] = max((o['p99'] for o in over), default=0.0)
    emit(proto.RESULTS / a.results / f'check-equivalence-{profile}.json',
         dict(check='equivalence', profile=profile, rule='identical replay+summary on every cell' if strict else
              'measurement only (divergence reported, never hidden)', passed=passed, summary=s, per_cell=per_cell,
              candidate_sha256=cand['provenance']['candidate_sha256'],
              candidate_code_section_sha256=cand['provenance'].get('candidate_code_section_sha256'),
              original_code_section_sha256=proto.load()['references']['original']['code_section_sha256']), passed)


def cmd_plumbing(a):
    doc = load(a.results)
    rows = doc['rows']
    tel = [r.get('telemetry') for r in rows]
    present = [t for t in tel if t and t.get('records')]
    heads = sorted({h for t in present for h in t.get('per_head', {})})
    totals = defaultdict(float)
    for t in present:
        for k, v in t.get('totals', {}).items():
            totals[k] += v
    faults = sum(r['faults'] for r in rows)
    codes = sum(len(r['diagnostics_codes']) for r in rows)
    checks = dict(no_faults=faults == 0, no_engine_codes=codes == 0, telemetry_present=len(present) == len(rows),
                  no_invalid=totals.get('invalid', 0) == 0, no_nan=totals.get('nan', 0) == 0,
                  counters_present=any(k in totals for k in ('fallback', 'refused', 'budget_refused')))
    passed = all(checks.values())
    emit(proto.RESULTS / a.results / 'check-plumbing.json',
         dict(check='dev_untrained_plumbing', profile=doc['provenance'].get('profile'), passed=passed, checks=checks,
              faults=faults, engine_codes=codes, telemetry_cells=len(present), cells=len(rows), heads_seen=heads,
              totals=dict(totals), claim='plumbing only; untrained heads; win rates not evaluated'), passed)


def _fuel_rows(rows):
    return dict(cells=len(rows), fuel_exhausted_entries=sum(r['fuel_exhausted'] for r in rows),
                games_with_fuel_exhaustion=sum(1 for r in rows if r['fuel_exhausted'] > 0),
                per_game_entries=[r['fuel_exhausted'] for r in rows],
                turn_p99_max=max((r['fuel_turns'].get('p99') or 0 for r in rows), default=0),
                turn_p999_max=max((r['fuel_turns'].get('p999') or 0 for r in rows), default=0),
                turn_max=max((r['fuel_turns'].get('max') or 0 for r in rows), default=0),
                turns_over_95pct=sum(r['fuel_turns'].get('over_95pct') or 0 for r in rows),
                cap_turns_match_events=all(r['fuel_turns'].get('cap_turns_match_events') for r in rows))


def cmd_fuel(a):
    doc = load(a.results)
    sched = proto.load_schedule(doc['schedule'])
    scen = sched.get('scenarios') or {'all': dict(maps=sorted({r['map'] for r in doc['rows']}))}
    base = load(a.baseline) if a.baseline else None
    out, ok = {}, True
    g = proto.load()['gate']['fuel']
    for name, s in scen.items():
        rs = [r for r in doc['rows'] if r['map'] in s['maps']]
        out[name] = dict(maps=s['maps'], candidate=_fuel_rows(rs))
        if base:
            bs = [r for r in base['rows'] if r['map'] in s['maps']]
            out[name]['baseline'] = _fuel_rows(bs)
            lim = g['entries_ratio_max'] * out[name]['baseline']['fuel_exhausted_entries'] + g['entries_slack']
            out[name]['entries_limit'] = lim
            out[name]['passed'] = out[name]['candidate']['fuel_exhausted_entries'] <= lim
            ok &= out[name]['passed']
    emit(proto.RESULTS / a.results / 'check-fuel.json',
         dict(check='fuel_profile', profile=doc['provenance'].get('profile'), passed=ok if base else None,
              scenarios=out, all_cells=_fuel_rows(doc['rows'])), ok if base else None)


def cmd_smoke(a):
    doc = load(a.results)
    rows = doc['rows']
    exp = {(c['opponent'], c['map'], c['side']) for c in proto.load_schedule(doc['schedule'])['cells']}
    complete = {stats.cell_key(r) for r in rows} == exp
    faults = sum(r['faults'] for r in rows)
    passed = complete and faults == 0 and sum(len(r['diagnostics_codes']) for r in rows) == 0
    emit(proto.RESULTS / a.results / 'check-smoke.json',
         dict(check='smoke', label='untrained framework check', passed=passed, complete=complete, faults=faults,
              per_opponent=stats.opponent_table(rows),
              claim='untrained framework check: buildable, runs both sides, no faults. NOT learning or strength '
                    'evidence'), passed)


def cmd_baseline(_a):
    """Aggregate the reference-only baseline measurements (original in the candidate seat) into one file."""
    out = dict(claim='reference-only measurements (no candidate exists); maps are reused benchmarks', parts={})
    for lab in ('reference/repro', 'reference/equivalence', 'reference/smoke', 'reference/fuel_profile'):
        p = proto.RESULTS / lab / 'results.json'
        if not p.exists():
            continue
        doc = json.loads(p.read_text(encoding='utf-8'))
        per = defaultdict(list)
        for r in doc['rows']:
            per[r['opponent']].append(r)
        out['parts'][lab] = dict(
            schedule=doc['schedule'], cells=doc['summary']['cells'], engine_matches=doc['summary']['engine_matches'],
            candidate_sha256=doc['provenance']['candidate_sha256'], engine_versions=doc['provenance']['engine_versions'],
            per_opponent={o: dict(games=len(rs), wins=sum(r['win'] for r in rs),
                                  fuel_exhausted_entries=sum(r['fuel_exhausted'] for r in rs),
                                  fuel_exhausted_per_game=round(sum(r['fuel_exhausted'] for r in rs) / len(rs), 4),
                                  games_with_fuel_exhaustion=sum(1 for r in rs if r['fuel_exhausted'] > 0),
                                  per_game=[dict(map=r['map'], side=r['side'], entries=r['fuel_exhausted'],
                                                 rounds=r['fuel_exhausted_rounds']) for r in rs if r['fuel_exhausted']],
                                  turn_p99_max=max(r['fuel_turns'].get('p99') or 0 for r in rs),
                                  turn_max=max(r['fuel_turns'].get('max') or 0 for r in rs),
                                  turns_over_95pct=sum(r['fuel_turns'].get('over_95pct') or 0 for r in rs),
                                  faults=sum(r['faults'] for r in rs))
                          for o, rs in sorted(per.items())})
        chk = proto.RESULTS / lab / 'check-repro.json'
        if chk.exists():
            out['parts'][lab]['reproducible'] = json.loads(chk.read_text(encoding='utf-8'))['passed']
    emit(proto.RESULTS / 'reference' / 'baseline.json', out, None)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['refs', 'repro', 'equivalence', 'plumbing', 'fuel', 'smoke', 'baseline'])
    ap.add_argument('--results')
    ap.add_argument('--reference')
    ap.add_argument('--baseline')
    ap.add_argument('--profile')
    a = ap.parse_args()
    {'refs': cmd_refs, 'repro': cmd_repro, 'equivalence': cmd_equivalence, 'plumbing': cmd_plumbing,
     'fuel': cmd_fuel, 'smoke': cmd_smoke, 'baseline': cmd_baseline}[a.command](a)


if __name__ == '__main__':
    main()
