"""Screen generated maps for quality against the official envelope and write the suite partitions.

Usage: python tools/mapgen/screen_maps.py --official-profile <profile.json> --gen-dirs <dir>... \
          --gen-profiles <profile.json>... --out-dir maps/generated --partitions evaluation/schedules/map_suite_500.json \
          --target N [--exclude names...]

A generated map is accepted only if both v58-mirror games completed without error or faults and every gameplay
measure (rounds, winner's gems, total banked gems, deaths, fuel-outs) lies inside the official maps' observed range.
Rejected maps are listed with reasons. From the accepted maps, --target maps are drawn without replacement by
importance resampling: a logistic regression on gameplay (rounds, winner's gems, total banked, deaths) separates
official from accepted generated maps, and each generated map is weighted by p/(1-p), the estimated density ratio
official/generated, so the selected set follows the official gameplay distribution (seeded, reproducible).
Partition: a generated map inherits the split of the official map whose style it copied (its template): templates in
the registered training + selection partitions -> 'gen-dev'; registered final maps and the unregistered fresh pool maps ->
'gen-holdout'. Official maps keep their existing labels.
"""
import argparse
import collections
import json
import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
METRICS = ['rounds', 'winner_gems', 'total_banked', 'deaths', 'fuel_outs']


def per_map(profile):
    by = collections.defaultdict(list)
    for g in profile['games']:
        by[g['map']].append(g)
    out = {}
    for m, gs in by.items():
        if any('error' in g for g in gs) or len(gs) != 2:
            out[m] = None
            continue
        out[m] = {
            'rounds': sum(g['rounds'] for g in gs) / 2,
            'winner_gems': sum(max(g['gems'], g['opponent_gems']) for g in gs) / 2,
            'total_banked': sum(g['gems'] + g['opponent_gems'] for g in gs) / 2,
            'deaths': sum(g['deaths'] for g in gs) / 2,
            'fuel_outs': sum(g['fuel_exhausted'] + g['opponent_fuel_exhausted'] for g in gs) / 2,
            'faults': sum(g['faults'] for g in gs),
        }
    return out


def importance_select(names, prof, official, n, seed):
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    keys = ['rounds', 'winner_gems', 'total_banked', 'deaths']
    if len(names) <= n:
        return names
    X = np.array([[official[m][k] for k in keys] for m in official] + [[prof[m][k] for k in keys] for m in names])
    y = np.array([1] * len(official) + [0] * len(names))
    clf = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, class_weight='balanced', max_iter=2000)).fit(X, y)
    p = clf.predict_proba(X[len(official):])[:, 1]
    w = np.clip(p / (1 - p), 1e-3, None)
    rng = np.random.default_rng(seed)
    pick = rng.choice(len(names), size=n, replace=False, p=w / w.sum())
    return [names[i] for i in sorted(pick)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--official-profile', required=True)
    ap.add_argument('--gen-dirs', nargs='+', required=True)
    ap.add_argument('--gen-profiles', nargs='+', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--partitions', required=True)
    ap.add_argument('--target', type=int, required=True)
    ap.add_argument('--exclude', nargs='*', default=[])
    ap.add_argument('--seed', type=int, default=120)
    a = ap.parse_args()

    official = {k: v for k, v in per_map(json.load(open(a.official_profile))).items() if k not in a.exclude and v}
    env = {k: (min(v[k] for v in official.values()), max(v[k] for v in official.values())) for k in METRICS}
    reg = json.load(open(os.path.join(ROOT, 'evaluation', 'schedules', 'map_partitions.json')))
    # The 28 development maps are the registered training + selection partitions; 'final' is the 12-map holdout.
    dev = set(reg['partitions']['training']) | set(reg['partitions']['selection'])

    gen = {}
    meta = {}
    for d in a.gen_dirs:
        for f in os.listdir(d):
            if f.endswith('_meta.json'):
                meta.update(json.load(open(os.path.join(d, f)))['maps'])
            elif f.endswith('.map26a'):
                gen[f[:-7]] = os.path.join(d, f)
    prof = {}
    for p in a.gen_profiles:
        prof.update(per_map(json.load(open(p))))

    accepted, rejected = [], {}
    for name in sorted(gen):
        v = prof.get(name)
        if v is None:
            rejected[name] = 'not profiled or game error'
            continue
        if v['faults']:
            rejected[name] = 'bot fault'
            continue
        bad = [k for k in METRICS if not (env[k][0] <= v[k] <= env[k][1])]
        if bad:
            rejected[name] = 'outside official range: ' + ', '.join(f'{k}={v[k]:g}' for k in bad)
            continue
        accepted.append(name)
    accepted = importance_select(accepted, prof, official, a.target, a.seed)

    os.makedirs(a.out_dir, exist_ok=True)
    labels = {}
    for name in accepted:
        shutil.copyfile(gen[name], os.path.join(a.out_dir, name + '.map26a'))
        tmpl = meta.get(name, {}).get('template')
        labels[name] = 'gen-dev' if tmpl in dev else 'gen-holdout'
    suite = {
        'kind': 'map_suite', 'engine': '2.0.0',
        'method': 'tools/mapgen (structured resampling of official components; see tools/mapgen/README.md)',
        'official_excluded': a.exclude,
        'acceptance_envelope_from_official_v58_mirror': {k: list(v) for k, v in env.items()},
        'generated': {n: {'split': labels[n], **meta.get(n, {})} for n in accepted},
        'rejected': rejected,
        'counts': dict(collections.Counter(labels.values())),
        'selection': f'importance resampling of {len(accepted)} from the accepted maps, seed {a.seed}',
    }
    json.dump(suite, open(a.partitions, 'w'), indent=1)
    print(f"accepted {len(accepted)} (target {a.target}); rejected {len(rejected)}; splits {suite['counts']}")
    reasons = collections.Counter(r.split(':')[0] for r in rejected.values())
    print('rejection reasons', dict(reasons))


if __name__ == '__main__':
    main()
