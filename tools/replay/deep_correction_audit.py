"""Prove the step-label correction changes only the intended measurements."""
import hashlib
import json
from collections import Counter
from deep_preflight import ROOT
from deep_detector_report import save
from winprob import features
import numpy as np

STUDY = ROOT / 'research/deep-2026-10-28'
LOCAL = ROOT / 'artifacts/local-only/deep-2026-10-28'


def main():
    catalog = {r['match_id']: r for r in json.loads((LOCAL / 'restored-catalog.json').read_text(encoding='utf-8')) if r['partition'] == 'examined'}
    runs = {}
    for label in ('timeline-examined-v2', 'timeline-examined-v3', 'detector-examined-v2', 'detector-examined-v3'):
        r = json.loads((LOCAL / label / 'run.json').read_text(encoding='utf-8'))
        assert r['partition'] == 'examined' and r['passed'] == 385 and r['failed'] == 0
        runs[label] = r
    feature_hash = hashlib.sha256()
    unchanged = ('D2', 'D3', 'D5', 'D7', 'D8', 'D10', 'D11')
    changed = Counter()
    records = []
    blocked, blocked_different_endpoints = 0, 0
    for mid, meta in sorted(catalog.items()):
        old = json.loads((LOCAL / 'timeline-examined-v2' / (mid + '.json')).read_text(encoding='utf-8'))
        new = json.loads((LOCAL / 'timeline-examined-v3' / (mid + '.json')).read_text(encoding='utf-8'))
        np.testing.assert_array_equal(features(old), features(new))
        feature_hash.update(mid.encode() + features(new).astype('<f8').tobytes())
        assert [(r['r'], r['terminal'], r['initial']) for r in old['rows']] == [(r['r'], r['terminal'], r['initial']) for r in new['rows']]
        assert old['events'] == new['events'] and old['credits'] == new['credits'] and old['opening'] == new['opening']
        for a, b in zip(old['rows'], new['rows']):
            for x, y in zip(a['teams'], b['teams']):
                assert {k: v for k, v in x.items() if k != 'round_actions'} == {k: v for k, v in y.items() if k != 'round_actions'}
        for a in new['actions']:
            if a['kind'] == 23:
                blocked += 1
                blocked_different_endpoints += a['from'] != a['to']
                assert a['successful'] is False
        da = json.loads((LOCAL / 'detector-examined-v2' / (mid + '.json')).read_text(encoding='utf-8'))
        db = json.loads((LOCAL / 'detector-examined-v3' / (mid + '.json')).read_text(encoding='utf-8'))
        aa, bb = {r['id']: r for r in da['actors']}, {r['id']: r for r in db['actors']}
        for actor in aa:
            for detector in unchanged:
                assert aa[actor]['detectors'][detector]['events'] == bb[actor]['detectors'][detector]['events'], (mid, actor, detector)
            for detector in ('D1', 'D4', 'D6', 'D9'):
                if aa[actor]['detectors'][detector] != bb[actor]['detectors'][detector]:
                    changed[detector] += 1
        records.append({'match_id': mid, 'all_model_features_identical': True, 'all_non_action_team_fields_identical': True,
                        'native_dependent_detector_events_identical': True})
    result = {'passed': 385, 'failed': 0, 'hands_off_used': 0,
              'old_timeline_code': runs['timeline-examined-v2']['code_sha256'],
              'corrected_timeline_code': runs['timeline-examined-v3']['code_sha256'],
              'corrected_detector_code': runs['detector-examined-v3']['code_sha256'],
              'ordered_game_feature_matrix_sha256': feature_hash.hexdigest(), 'model_refit': False, 'test_retuning': False,
              'unchanged_native_event_detectors': list(unchanged), 'changed_actor_detector_outputs': dict(changed),
              'movement_blocked_steps': blocked, 'movement_blocked_with_different_endpoints': blocked_different_endpoints,
              'records': records}
    save(STUDY / 'CORRECTION_VALIDATION.json', result)
    model_path = STUDY / 'WINPROB_MODEL.json'
    model = json.loads(model_path.read_text(encoding='utf-8'))
    model['compatible_action_log_revision'] = {'timeline_code_sha256': result['corrected_timeline_code'],
        'proof': 'CORRECTION_VALIDATION.json', 'all_385_feature_matrices_identical': True, 'refit': False, 'test_retuning': False}
    save(model_path, model)
    print(json.dumps({k: v for k, v in result.items() if k != 'records'}))


if __name__ == '__main__':
    main()
