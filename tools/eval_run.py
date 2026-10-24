"""Run a frozen evaluation schedule for a candidate against the frozen references (Agent H).

Examples (PowerShell, from ROOT, PYTHONPATH not needed):
  python tools/eval_run.py --schedule smoke --label untrained-release --bot-dir bot
  python tools/eval_run.py --schedule equivalence --label teacher-exact --wasm artifacts/x.wasm --profile teacher_exact
  python tools/eval_run.py --schedule final --label ref-original-final --reference original      # teacher baseline
  python tools/eval_run.py --schedule final --label cand-123 --wasm c.wasm --family run-2026-11-01  # once (ledger)

Writes evaluation/results/<label>/results.json: per-cell rows + summary + provenance (candidate sha256, reference
sha256s, CLI version, engine versions/build hashes from the summaries, profile, protocol sha256). Official CLI only,
`--release`, default fuel; at most 4 concurrent matches. A final-schedule run of a non-reference candidate reserves
the final benchmark in evaluation/ledger.jsonl BEFORE any match is run and refuses a repeat (see --final-reason).
"""
import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from nfs import engine  # noqa: E402
from nfs.evaluate import ledger as ledger_mod  # noqa: E402
from nfs.evaluate import protocol as proto  # noqa: E402
from nfs.evaluate import release as release_mod  # noqa: E402
from nfs.evaluate import schedule as sched_mod  # noqa: E402


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--schedule', required=True)
    ap.add_argument('--label', required=True, help='results folder name under evaluation/results/ (may contain /)')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--wasm')
    g.add_argument('--bot-dir', help='bot directory containing src/; built with the official CLI (--release)')
    g.add_argument('--reference', choices=proto.REFERENCE_NAMES, help='run a frozen reference in the candidate seat')
    ap.add_argument('--profile', help='nn_config profile of the candidate (read from src/nn_config.h with --bot-dir)')
    ap.add_argument('--family', help='candidate family / training-run id (required for the final schedule)')
    ap.add_argument('--final-reason', help='recorded reason for a repeated final evaluation (ledger override)')
    ap.add_argument('--match-cache', help='shared match folder root (default: <results>/<label>/matches)')
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()

    p = proto.load(verify=True)
    sched = proto.load_schedule(a.schedule, verify=True)
    out_dir = proto.RESULTS / a.label
    out_dir.mkdir(parents=True, exist_ok=True)
    profile = a.profile
    if a.reference:
        cand = sched_mod.reference_wasm(a.reference)
        profile = profile or f'reference:{a.reference}'
    elif a.bot_dir:
        bot = Path(a.bot_dir).resolve()
        cfg = bot / 'src' / 'nn_config.h'
        if cfg.exists():
            parsed = release_mod.parse_nn_config(cfg.read_text(encoding='utf-8'))
            if profile and parsed['profile'] and profile != parsed['profile']:
                sys.exit(f'--profile {profile} contradicts {cfg} ({parsed["profile"]})')
            profile = parsed['profile'] or profile
        cand = engine.official_build(bot, out_dir / 'candidate.wasm', release=True)
    else:
        cand = Path(a.wasm).resolve()
    cand_sha = engine.sha256(cand)
    ref_shas = {k: v['wasm_sha256'] for k, v in p['references'].items()}
    is_reference = cand_sha in ref_shas.values()
    if a.reference and ref_shas[a.reference] != cand_sha:
        sys.exit(f'reference {a.reference} changed on disk; refusing')

    res_path = out_dir / 'results.json'
    if res_path.exists():
        old = json.loads(res_path.read_text(encoding='utf-8'))
        if old['provenance']['candidate_sha256'] != cand_sha or old['schedule'] != a.schedule:
            sys.exit(f'{res_path} holds a different candidate/schedule; use a new --label')

    reservation = None
    if sched['kind'] == 'final' and not is_reference:
        if not a.family:
            sys.exit('final schedule requires --family (training run / lineage id)')
        led = ledger_mod.Ledger(proto.LEDGER, p['gate']['override_reason_min_chars'])
        prior = led.reservation(cand_sha)
        if prior and res_path.exists():
            reservation = prior  # resume the same reserved evaluation (cached cells; no new final use)
        else:
            try:
                reservation = led.reserve_final(cand_sha, a.family, proto.protocol_sha256(), 'final', a.final_reason,
                                                a.label)
            except ledger_mod.LedgerRefusal as exc:
                sys.exit(f'LEDGER REFUSED: {exc}')
        print('final benchmark reserved: ledger seq', reservation['seq'], flush=True)

    started = now()
    match_root = Path(a.match_cache).resolve() if a.match_cache else out_dir / 'matches'
    rows = sched_mod.run(sched, cand, match_root, p, a.workers)
    summary = sched_mod.summarize(rows)
    labels = dict(maps=proto.MAP_LABEL, schedule_kind=sched['kind'])
    if sched.get('label'):
        labels['schedule_label'] = sched['label']
    if sched['kind'] == 'framework':
        labels['claim'] = 'framework check only; not strength or learning evidence'
    doc = dict(schedule=a.schedule, schedule_sha256=p['schedules'][a.schedule]['sha256'],
               protocol_sha256=proto.protocol_sha256(), label=a.label, labels=labels,
               provenance=dict(candidate_path=str(cand), candidate_sha256=cand_sha,
                               candidate_code_section_sha256=engine.code_section_sha(cand),
                               candidate_is_reference=is_reference, profile=profile,
                               reference_sha256=sched_mod.check_references(p),
                               cli_version=engine.cli_version(), engine_versions=summary['engine_versions'],
                               engine_build_hashes=sorted({r.get('engine_build_hash') for r in rows if r.get('engine_build_hash')}),
                               started_utc=started, finished_utc=now(), release=True,
                               fuel='official default (no override)', workers=min(4, a.workers),
                               ledger_seq=reservation['seq'] if reservation else None),
               summary=summary, rows=rows)
    engine.write_json(res_path, doc)
    if reservation is not None:
        led = ledger_mod.Ledger(proto.LEDGER, p['gate']['override_reason_min_chars'])
        if not any(e.get('event') == 'final_result' and e.get('reservation_seq') == reservation['seq'] for e in led.entries()):
            led.record_result(reservation['seq'], cand_sha, None, hashlib.sha256(res_path.read_bytes()).hexdigest(),
                              dict(cells=summary['cells'], faults=summary['faults']))
    print(json.dumps({k: v for k, v in summary.items() if k != 'per_opponent'}, indent=2))
    for o, t in summary['per_opponent'].items():
        print(f"  {o:11s} games {t['games']:3d} wins {t['wins']:5.1f} margin {t['mean_margin']:8.1f} "
              f"fuelEx {t['fuel_exhausted_entries']:3d} faults {t['faults']}")
    print('wrote', res_path)


if __name__ == '__main__':
    main()
