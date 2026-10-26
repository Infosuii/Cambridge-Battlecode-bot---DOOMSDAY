"""Collect v58 round2 strategy evidence without selecting, enabling or submitting a candidate.

Usage: python tools/report_v58_r2.py
All listed runs must be complete and validated. Writes V58_R2_RESULTS.json and V58_R2_RESULTS.md.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / 'artifacts/claude_ops'
RUNS = ['r2-m1', 'r2-t1', 'r2-h1', 'r2-c1', 'r2-n1', 'r2-c1-confirm', 'r2-f1', 'r2-p1',
        'r2-c2', 'r2-c3b', 'r2-c3b-confirm', 'r2-c4', 'r2-c4b']
DESCRIPTIONS = {
    'r2-m1': 'Marcella camp-resistance/attack build', 'r2-t1': 'Tavi attack-stat farming build',
    'r2-h1': 'Heart early universal damage reduction', 'r2-c1': 'Hold safe cleared captures under contact',
    'r2-n1': 'Immediate supported capture denial', 'r2-f1': 'Bounded finish before gold-only shopping',
    'r2-p1': 'Finish an engaged camp before chasing distant contact',
    'r2-c2': 'Capture holding with urgent-race and conservative burst guards',
    'r2-c3b': 'One visible safe capture anchor; other bodies retain combat',
    'r2-c4': 'Prototype sole-anchor movement inside the capture region',
    'r2-c4b': 'Capture movement with explicit board-edge bounds',
}


def read(name):
    return json.loads((OPS / name).read_text(encoding='utf8'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    manifest = read('V58_EXPERIMENTS.json')
    rows = []
    slots = set()
    for label in RUNS:
        source_label = label.removesuffix('-confirm')
        stem = 'results/v58-' + label
        valid, bayes, cluster = (read(stem + '-' + s + '.json') for s in ('validation', 'bayes', 'cluster'))
        assert valid['passed'] and sum(valid['faults'].values()) == 0
        assert valid['games'] == bayes['games'] == cluster['games']
        build = ROOT / ('artifacts/evaluations/v58-' + label + '-build')
        actual = {p.name: sha(p) for p in (build / 'src-cand-s1/src').iterdir() if p.is_file()}
        assert actual == manifest[source_label]['files'], (label, 'seed1 source mismatch')
        seeds = bayes['seeds']
        for map_row in cluster['per_map']:
            for side in ('A', 'B'):
                for seed in seeds:
                    slots.add((source_label, map_row['map'], side, seed))
        row = dict(label=label, configuration=source_label, description=DESCRIPTIONS[source_label],
                   source_sha256=manifest[source_label]['source_sha256'], games=valid['games'], wins=valid['wins'],
                   win_rate=valid['win_rate'], raw_margin=valid['mean_margin'], bayesian_mean=bayes['gems_mean'],
                   p_gain=bayes['p_gain'], p_gain_neg50=bayes['p_gain_neg50'], cluster_ci95=cluster['gem_ci95'],
                   faults=valid['faults'], fuel_per_game={s: v / valid['games'] for s, v in valid['fuel'].items()},
                   bayes_accept=bayes['gems_mean'] >= 25 and bayes['p_gain'] >= .95,
                   positive_cluster_interval=cluster['gem_ci95'][0] > 0,
                   incomplete_noninferiority=bayes['gems_mean'] >= -25 and bayes['p_gain_neg50'] >= .9,
                   evidence_stem='artifacts/claude_ops/' + stem,
                   wasm_sha256={side: {str(seed): sha(build / f'{file}-s{seed}.wasm') for seed in seeds}
                                for side, file in [('candidate', 'cand'), ('baseline', 'opp')]})
        for suffix in ('pressure', 'observables'):
            if (OPS / (stem + '-' + suffix + '.json')).is_file():
                row[suffix + '_report'] = 'artifacts/claude_ops/' + stem + '-' + suffix + '.json'
        rows.append(row)
    data = dict(round=2, sdk_cli='3.0.5', engine='1.0.3', sprint3_patch_applied=False,
                completed_runs=len(rows), actual_games=sum(r['games'] for r in rows),
                distinct_configuration_game_slots=len(slots), invalid_builds=['r2-c3'],
                note='C1 and C3b screen seeds recur in confirmation. Variants share development maps; these are not independent confirmations.',
                variants=rows)
    (OPS / 'V58_R2_RESULTS.json').write_text(json.dumps(data, indent=1) + '\n', encoding='utf8')
    lines = ['# v58 round2 strategy results', '',
             'Frozen v57 opponent,28 development maps, both sides. SDK/CLI3.0.5, engine1.0.3; no Sprint3 changes.',
             f"{data['completed_runs']} valid runs, {data['actual_games']} played games; {len(slots)} distinct configuration/map/side/seed slots.",
             data['note'], 'All completed runs exited0, had exact coverage and zero native faults on both teams. C3 preflight failed with0games.', '',
             '| Run | Games | Wins | Raw gems | Bayes mean | P(>0) | Map-cluster95% | Fuel/game |',
             '|---|---:|---:|---:|---:|---:|---|---:|']
    for r in rows:
        lo, hi = r['cluster_ci95']
        lines.append(f"| {r['label']} | {r['games']} | {r['wins']:.0f} | {r['raw_margin']:+.1f} | "
                     f"{r['bayesian_mean']:+.1f} | {r['p_gain']:.3f} | [{lo:+.1f}, {hi:+.1f}] | {r['fuel_per_game']['candidate']:.4f} |")
    lines += ['', 'Fuel is not rounded before applying the≤2 gate. Bayesian acceptance alone does not satisfy the clustered-interval rule.', '',
              '## Configurations', '']
    for name, description in DESCRIPTIONS.items():
        lines.append(f'* **{name}**: {description}.')
    lines += ['', '## Reproduction', '',
              '`python tools/reproduce_v58.py <configuration> <new repo-local directory>` reconstructs the exact frozen source.',
              'Use `bench3.sh` with absolute candidate/opponent/output paths and the recorded seeds; compare with both',
              '`bench_bayes.py` and `bench_compare.py`. `check_bench_run.py --seeds <list>` verifies coverage and native faults.',
              'Built-source and candidate/opponent wasm hashes for every seed are in V58_R2_RESULTS.json. Raw data remain local-only.', '']
    (OPS / 'V58_R2_RESULTS.md').write_text('\n'.join(lines), encoding='utf8')
    print(data['completed_runs'], 'runs;', data['actual_games'], 'played;', len(slots), 'distinct configuration slots')


if __name__ == '__main__':
    main()
