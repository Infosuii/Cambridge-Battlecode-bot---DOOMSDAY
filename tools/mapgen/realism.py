"""Compare a generated map set with the official maps: layout features, gameplay profile and a classifier test.

Usage: python tools/mapgen/realism.py --official-layout research/maps/official_maps.json
          --official-profile <profile.json> --gen-layout <layout.json> --gen-profile <profile.json>
          [--exclude names...] [--out report.json]
Layout JSON comes from extract_official.py (it reads any map directory); profiles from profile_maps.py.
Needs numpy and scikit-learn. Reports per-feature official vs generated quartiles and the two-sample KS statistic,
and the cross-validated AUC of a logistic regression separating official from generated layouts (0.5 = cannot tell).
"""
import argparse
import collections
import json

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

SYMS = ['horizontal', 'vertical', 'rotational']


def layout_features(m):
    a = m['w'] * m['h']
    types = collections.Counter(c['type'] for c in m['camps'])
    n = max(1, len(m['camps']))
    sx0, sy0, sx1, sy1 = m['spawn']
    f = {
        'area': a, 'aspect': max(m['w'], m['h']) / min(m['w'], m['h']), 'team': m['team'],
        'wall_d': len(m['walls']) / a, 'bush_d': len(m['bushes']) / a, 'hole_d': len(m['holes']) / a,
        'altars': len(m['altars']), 'groups_half': len(m['groups']), 'camps_half': len(m['camps']),
        'gems': sum(g['gems'] for g in m['groups']), 'gold': sum(g['gold'] for g in m['groups']),
        'gems_per_area': sum(g['gems'] for g in m['groups']) / a * 1000,
        'spawn_area': (sx1 - sx0 + 1) * (sy1 - sy0 + 1),
    }
    for i, k in enumerate(['wolf', 'elk', 'gem', 'gold', 'monolith', 'golem']):
        f['share_' + k] = types[i] / n
    for s in SYMS:
        f['sym_' + s] = 1.0 if m['symmetry'] == s else 0.0
    return f


def profile_features(profile):
    by = collections.defaultdict(list)
    for g in profile['games']:
        if 'error' not in g:
            by[g['map']].append(g)
    out = {}
    for m, gs in by.items():
        out[m] = {
            'rounds': np.mean([g['rounds'] for g in gs]),
            'capped': np.mean([g['rounds'] >= 2000 for g in gs]),
            'winner_gems': np.mean([max(g['gems'], g['opponent_gems']) for g in gs]),
            'total_banked': np.mean([g['gems'] + g['opponent_gems'] for g in gs]),
            'deaths': np.mean([g['deaths'] for g in gs]),
            'fuel_outs': np.mean([g['fuel_exhausted'] + g['opponent_fuel_exhausted'] for g in gs]),
            'faults': sum(g['faults'] for g in gs),
        }
    return out


def ks(a, b):
    a, b = np.sort(a), np.sort(b)
    xs = np.concatenate([a, b])
    return float(np.max(np.abs(np.searchsorted(a, xs, 'right') / len(a) - np.searchsorted(b, xs, 'right') / len(b))))


def q(v):
    return [round(float(x), 3) for x in np.percentile(v, [25, 50, 75])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--official-layout', required=True)
    ap.add_argument('--official-profile', required=True)
    ap.add_argument('--gen-layout', required=True)
    ap.add_argument('--gen-profile', required=True)
    ap.add_argument('--exclude', nargs='*', default=[])
    ap.add_argument('--out')
    a = ap.parse_args()
    off = {k: v for k, v in json.load(open(a.official_layout)).items() if k not in a.exclude}
    gen = json.load(open(a.gen_layout))
    fo = {k: layout_features(v) for k, v in off.items()}
    fg = {k: layout_features(v) for k, v in gen.items()}
    po = {k: v for k, v in profile_features(json.load(open(a.official_profile))).items() if k in off}
    pg = profile_features(json.load(open(a.gen_profile)))
    report = {'n_official': len(fo), 'n_generated': len(fg), 'layout': {}, 'gameplay': {}}
    keys = list(next(iter(fo.values())).keys())
    for k in keys:
        x, y = [f[k] for f in fo.values()], [f[k] for f in fg.values()]
        report['layout'][k] = {'official_q': q(x), 'generated_q': q(y), 'ks': round(ks(x, y), 3)}
    for k in ['rounds', 'capped', 'winner_gems', 'total_banked', 'deaths', 'fuel_outs']:
        x, y = [v[k] for v in po.values()], [v[k] for v in pg.values()]
        report['gameplay'][k] = {'official_q': q(x), 'generated_q': q(y), 'ks': round(ks(x, y), 3),
                                 'official_range': [round(float(min(x)), 2), round(float(max(x)), 2)]}
    report['gameplay']['faults'] = {'official': int(sum(v['faults'] for v in po.values())),
                                    'generated': int(sum(v['faults'] for v in pg.values()))}
    # Classifier two-sample test on layout features (balanced by class weight).
    X = np.array([[f[k] for k in keys] for f in list(fo.values()) + list(fg.values())])
    yv = np.array([1] * len(fo) + [0] * len(fg))
    clf = make_pipeline(StandardScaler(), LogisticRegression(C=0.3, class_weight='balanced', max_iter=2000))
    p = cross_val_predict(clf, X, yv, cv=StratifiedKFold(5, shuffle=True, random_state=0), method='predict_proba')[:, 1]
    report['classifier_auc'] = round(float(roc_auc_score(yv, p)), 3)
    clf.fit(X, yv)
    coef = clf[-1].coef_[0]
    report['classifier_top_features'] = [(keys[i], round(float(coef[i]), 2)) for i in np.argsort(-np.abs(coef))[:6]]
    if a.out:
        json.dump(report, open(a.out, 'w'), indent=1)
    print(f"official {report['n_official']} vs generated {report['n_generated']}; classifier AUC {report['classifier_auc']}"
          f" (0.5 = indistinguishable); top separating features {report['classifier_top_features']}")
    for sec in ('layout', 'gameplay'):
        print(f'-- {sec}: feature  official_q  generated_q  KS')
        for k, v in report[sec].items():
            if 'ks' in v:
                print(f"   {k:16s} {str(v['official_q']):28s} {str(v['generated_q']):28s} {v['ks']}")
    print('faults', report['gameplay']['faults'])


if __name__ == '__main__':
    main()
