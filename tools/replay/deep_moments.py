"""Freeze model-selected windows before exposing the action windows for cards."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import numpy as np
from deep_preflight import ROOT
from deep_detector_report import save
from winprob import features, sigmoid, NAMES

STUDY = ROOT / 'research/deep-2026-10-28'
LOCAL = ROOT / 'artifacts/local-only/deep-2026-10-28'


def windows(game, own, beta):
    x = features(game)
    ps = sigmoid(x @ beta)
    if own:
        ps = 1 - ps
    rounds = np.array([r['r'] for r in game['rows']])
    candidates = []
    for i, row in enumerate(game['rows']):
        if row['terminal'] or row['initial'] or row['r'] < 15:
            continue
        before = max(0, int(np.searchsorted(rounds, row['r'] - 5, side='right')) - 1)
        after = int(np.searchsorted(rounds, row['r'] + 5))
        if after >= len(rounds) or game['rows'][after]['terminal']:
            continue
        drop = float(ps[before] - ps[after])
        if drop <= 0:
            continue
        dz = (x[after] - x[before]) * beta * (-1 if own else 1)
        denominator = dz.sum()
        factor = -drop / denominator if abs(denominator) > 1e-12 else float(ps[before] * (1 - ps[before]))
        contribution = dz * factor
        assert abs(contribution.sum() + drop) < 1e-8
        candidates.append({'center': row['r'], 'start': int(rounds[before]), 'end': int(rounds[after]),
                           'p_before': float(ps[before]), 'p_after': float(ps[after]), 'drop': drop,
                           'feature_probability_change': dict(zip(NAMES, contribution.tolist())),
                           'own_side': own, 'start_features': (x[before] * (-1 if own else 1)).tolist()})
    chosen = []
    for c in sorted(candidates, key=lambda c: (-c['drop'], c['center'])):
        if not any(c['start'] <= a['end'] and a['start'] <= c['end'] for a in chosen):
            chosen.append(c)
            if len(chosen) == 5:
                break
    return chosen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True, type=Path)
    args = ap.parse_args()
    model = json.loads((STUDY / 'WINPROB_MODEL.json').read_text(encoding='utf-8'))
    beta = np.array([model['coefficients'][n] for n in NAMES])
    catalog = [r for r in json.loads((LOCAL / 'restored-catalog.json').read_text(encoding='utf-8')) if r['partition'] == 'examined']
    byid, all_windows, losses, wins = {}, [], [], []
    for meta in catalog:
        if meta['source'] == 'top-v-top':
            continue
        mid = meta['match_id']
        game = json.loads((args.run / (mid + '.json')).read_text(encoding='utf-8'))
        own = 0 if meta['side'] == 'a' else 1
        values = windows(game, own, beta)
        base = {k: meta[k] for k in ('match_id', 'map', 'cohort', 'opponent', 'result')}
        values = [dict(base, **c, rank=i + 1) for i, c in enumerate(values)]
        byid[mid] = values
        if meta['result'] == 'loss':
            losses.append(meta)
            all_windows.extend(values)
        else:
            wins.append(meta)
    # Cohort quotas fixed before action-window exposure. Spread first picks over maps.
    def balanced(pool, n, token):
        used, selected = Counter(), []
        pool = [r for r in pool if byid[r['match_id']]]
        while pool and len(selected) < n:
            pool.sort(key=lambda r: (used[r['map']], hashlib.sha256((token + r['match_id']).encode()).hexdigest()))
            row = pool.pop(0)
            selected.append(row)
            used[row['map']] += 1
        return selected
    picked = []
    for cohort, count in [('Learn', 20), ('Climb', 30), ('Other', 15)]:
        picked.extend(balanced([r for r in losses if r['cohort'] == cohort], count, 'loss20261028'))
    assert len(picked) == 65
    sample = [dict(byid[r['match_id']][0], kind='loss') for r in picked]
    extra = sorted((byid[r['match_id']][1] for r in picked if len(byid[r['match_id']]) > 1), key=lambda r: (-r['drop'], r['match_id']))[:25]
    sample += [dict(r, kind='loss') for r in extra]
    controls = []
    for cohort, count in [('Learn', 2), ('Climb', 9), ('Other', 4)]:
        controls.extend(balanced([r for r in wins if r['cohort'] == cohort], count, 'win20261028'))
    assert len(controls) == 15
    sample += [dict(byid[r['match_id']][0], kind='win_control') for r in controls]
    sample.sort(key=lambda r: (r['kind'], r['cohort'], r['match_id'], r['center']))
    for i, row in enumerate(sample):
        row['card_id'] = f'C{i+1:03}'
    result = {'model_version': model['version'], 'evidence': 'model-associated selected drops, not causal regret',
              'hands_off_used': 0, 'loss_games': len(losses), 'loss_moments': len(all_windows),
              'selection': 'five largest disjoint positive ~10-round model drops per loss; no terminal after-state',
              'rows': all_windows}
    save(STUDY / 'moments.json', result)
    selection = {'prediction_first_stage': 'windows fixed before exact actor observations and actual action windows are exposed',
                 'cards': len(sample), 'loss_cards': sum(r['kind'] == 'loss' for r in sample),
                 'distinct_losses': len(picked), 'control_win_games': len(controls),
                 'cohort_game_quotas': {'Learn_loss': 20, 'Climb_loss': 30, 'Other_loss': 15,
                                       'Learn_win': 2, 'Climb_win': 9, 'Other_win': 4},
                 'rows': sample}
    target = STUDY / 'MOMENT_SAMPLE.json'
    raw = (json.dumps(selection, indent=2) + '\n').encode()
    if target.exists():
        assert target.read_bytes() == raw, 'Moment sample immutable after predictions/action review'
    target.write_bytes(raw)
    print(json.dumps({k: v for k, v in selection.items() if k != 'rows'}))


if __name__ == '__main__':
    main()
