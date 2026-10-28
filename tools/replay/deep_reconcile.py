"""Audit downloaded study pairs. Never report held-out trajectories or detector rates.

Run deep_download_ingest.py first, then decode_replays.mjs with engine 2.0.0
and all three partition directories to a local-only JSONL; pass that file here.
"""
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from deep_preflight import ROOT, save
from deep_native_audit import audit

STUDY = 'deep-2026-10-28'
BUILD = '85aa7167b44db7cea97509f55e997750520e33d644e9f4f90d6128c50eba1d21'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decoded', type=Path)
    args = parser.parse_args()
    out = ROOT / 'research' / STUDY
    manifest = json.loads((out / 'CANDIDATE_MANIFEST.json').read_text(encoding='utf-8'))
    candidates = {r['match_id']: r for r in manifest['rows']}
    downloads = json.loads((out / 'DOWNLOADS.json').read_text(encoding='utf-8'))
    files = {r['match_id']: r for r in downloads['games']}
    wave = {r['match_id']: r for r in json.loads((out / 'WAVE1_METADATA.json').read_text(encoding='utf-8'))['rows']}
    top = {r['match_id']: r for r in json.loads((out / 'TOP_V_TOP_METADATA.json').read_text(encoding='utf-8'))['rows']}
    records = []
    seen = set()
    for line in args.decoded.read_text(encoding='utf-8').splitlines():
        decoded = json.loads(line)
        mid = Path(decoded['replay']).stem
        if mid in seen or mid not in candidates or mid not in files:
            raise ValueError('Duplicate or unregistered decoded match')
        seen.add(mid)
        candidate = candidates[mid]
        native_path = ROOT / files[mid]['replay_path'].replace('.repl26a', '.summary.json')
        native = json.loads(native_path.read_text(encoding='utf-8'))
        # Reuse the native conservation/roster auditor, retaining only genuinely
        # internal identities; do not present self-derived values as metadata checks.
        side = 'a' if candidate['side'] not in ('a', 'b') else candidate['side']
        own = 'teamA' if side == 'a' else 'teamB'
        fake_metadata = {'own_side': side, 'rounds': native['match']['roundsStarted'],
                         'our_score': next(t['submittedGems'] for t in native['teams'] if t['team'] == own),
                         'opponent_score': next(t['submittedGems'] for t in native['teams'] if t['team'] != own),
                         'result': 'win' if native['match']['outcome'] == own else 'loss'}
        internal = audit(native, fake_metadata)
        keep = ('engine_2_0_0', 'draft_roster_internal', 'gem_identity_native',
                'gold_identity_native', 'team_bank_equals_champion_sum')
        checks = {k: internal['checks'][k] for k in keep}
        checks['engine_build'] = native['match']['engineBuildHash'] == BUILD
        checks['metric_semantics'] = native['match']['metricSemanticsVersion'] == 1
        checks['replay_decoded'] = decoded.get('ok') is True
        sc = decoded.get('summary_check') or {}
        checks['replay_native_final_state'] = sc.get('passed') is True
        checks['replay_native_draft'] = sc.get('checks', {}).get('draft_picks') is True
        checks['replay_native_physical_roster'] = sc.get('checks', {}).get('physical_roster') is True
        if candidate['source'] != 'top-v-top':
            checks['outcome_candidate_metadata'] = fake_metadata['result'] == candidate['result']
        if mid in wave:
            checks.update({f'wave_metadata_{k}': v for k,v in audit(native, wave[mid])['checks'].items()
                           if k not in keep})
        if mid in top:
            checks['top_metadata_scores'] = all(
                int(t['score']) == int(next(n['submittedGems'] for n in native['teams']
                    if n['team'] == ('teamA' if t['side'] == 'a' else 'teamB')))
                for t in top[mid]['teams'])
        records.append({'match_id': mid, 'partition': candidate['partition'],
                        'passed': all(checks.values()), 'checks': checks,
                        'champions': len(native['champions'])})
    report = {'evidence_label': 'measured', 'updated_at': datetime.now(timezone.utc).isoformat(),
              'engine': '2.0.0', 'decoded_pairs': len(records),
              'passed': sum(r['passed'] for r in records), 'failed': sum(not r['passed'] for r in records),
              'calibration_passed': sum(r['passed'] and r['partition'] == 'calibration-excluded' for r in records),
              'accepted_study_games': sum(r['passed'] and r['partition'] != 'calibration-excluded' for r in records),
              'passed_by_partition': dict(Counter(r['partition'] for r in records if r['passed'])),
              'champion_body_equations_checked': sum(r['champions'] for r in records),
              'hands_off_trajectories_reviewed': False, 'hands_off_detector_rates_reviewed': False,
              'existing_catalog_score_metadata_limit': 'Existing raw catalog was not in Git. Outcome checked against frozen manifest; exact native final state independently checked against replay. Wave/top metadata scores additionally checked.',
              'games': records}
    save(out / 'RECONCILIATION.json', report)
    print(json.dumps({k:v for k,v in report.items() if k != 'games'}))
    if report['failed']:
        print(json.dumps([{'match_id': r['match_id'], 'failed': [k for k,v in r['checks'].items() if not v]}
                          for r in records if not r['passed']]))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
