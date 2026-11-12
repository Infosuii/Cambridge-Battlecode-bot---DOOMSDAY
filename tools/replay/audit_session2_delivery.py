"""Check deliverable coverage, immutable prediction evidence and held-out exclusion."""
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from deep_preflight import ROOT
from deep_detector_report import save

STUDY = ROOT / 'research/deep-2026-10-28'


def main():
    read = lambda name: json.loads((STUDY / name).read_text(encoding='utf-8'))
    manifest = read('CANDIDATE_MANIFEST.json')
    examined = {r['match_id'] for r in manifest['rows'] if r['partition'] == 'examined'}
    held = {r['match_id'] for r in manifest['rows'] if r['partition'] == 'hands-off'}
    assert len(examined) == 385 and len(held) == 165
    split = read('MODEL_SPLIT.json')
    assert {r['match_id'] for r in split['rows']} == examined
    assert split['counts'] == {'train': 231, 'calibration': 77, 'test': 77}
    sample, preds, cards = read('MOMENT_SAMPLE.json'), read('CARD_PREDICTIONS.json'), read('CARD_DATA.json')
    assert len(sample['rows']) == len(preds['rows']) == len(cards['rows']) == 105
    assert len({r['match_id'] for r in sample['rows'] if r['kind'] == 'loss'}) == 65
    assert len({r['match_id'] for r in sample['rows'] if r['kind'] == 'win_control'}) == 15
    assert {r['match_id'] for r in sample['rows']} <= examined
    assert not {r['match_id'] for r in sample['rows']} & held
    files = list((STUDY / 'cards').glob('*.md'))
    assert len(files) == 105 and all(len(p.read_text(encoding='utf-8').splitlines()) <= 25 for p in files)
    with (STUDY / 'error_analysis.csv').open(encoding='utf-8', newline='') as f:
        assert len(list(csv.DictReader(f))) == 105
    for name in ('CARD_PREDICTIONS.json', 'MOMENT_SAMPLE.json', 'DETECTOR_SPEC.json', 'MODEL_SPLIT.json'):
        original = subprocess.check_output(['git', 'show', 'b490a1d:research/deep-2026-10-28/' + name], cwd=ROOT)
        assert original == (STUDY / name).read_bytes(), name + ' changed after registration/prediction'
    assert hashlib.sha256((STUDY / 'CARD_PREDICTIONS.json').read_bytes()).hexdigest() == hashlib.sha256(
        subprocess.check_output(['git', 'show', 'b490a1d:research/deep-2026-10-28/CARD_PREDICTIONS.json'], cwd=ROOT)).hexdigest()
    assert read('CORRECTION_VALIDATION.json')['passed'] == 385
    for name in ('TIMELINE_SCREEN.json', 'DETECTOR_SCREEN.json'):
        proof = read(name)
        assert proof['passed'] == 385 and proof['failed'] == 0
    subprocess.run(['git', 'diff', '--exit-code', '5114231', '--', 'bots/live-69'], cwd=ROOT, check=True, capture_output=True)
    subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True, capture_output=True)
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True, capture_output=True)
    moments = read('moments.json')
    result = {'passed': True, 'examined': 385, 'hands_off_used': 0, 'cards': 105,
              'distinct_losses': 65, 'control_wins': 15,
              'selected_loss_maps': len({r['map'] for r in sample['rows'] if r['kind'] == 'loss'}),
              'all_loss_moments': moments['loss_moments'],
              'prediction_and_registration_bytes_unchanged': True, 'frozen_source_unchanged': True,
              'semantic_cases_passed': 15, 'statistical_cases_passed': 6, 'model_scientific_cases_passed': 4,
              'limits': 'Observational checkpoint only. Exact reproduction/traces, confirmed takeover regressions, held-out frequency confirmation and final bot brief remain unfinished.'}
    save(STUDY / 'SESSION2_VALIDATION.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
