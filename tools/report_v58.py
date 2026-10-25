"""Collect completed v58 development screens, evidence and immutable source/build identities.

Usage: python tools/report_v58.py
Writes V58_RESULTS.json and V58_RESULTS.md under artifacts/claude_ops; does not select or submit a bot.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / 'artifacts/claude_ops'
LABELS = ['d1', 'd2b', 'd3', 'd4', 'd5', 'd6', 'd7', 'a1', 'd8', 'a2', 'd9', 's1', 'd10',
          'a3', 'd11', 'd12', 'v1', 'l1', 'd13', 'd14']
DESCRIPTIONS = {
    'd1': 'Repeated primary jobs and bounded capture routing; original draft',
    'd2b': 'Capture lifecycle, visible crew readiness and public roster',
    'd3': 'Coupled carry draft and Treasure shopping',
    'd4': 'Physically release the carry capture region',
    'd5': 'Price team-rounds and release capable satellites',
    'd6': 'Elect one reward owner and preserve carry delivery',
    'd7': 'Preposition ranged carry before the clear finishes',
    'a1': 'Stationary camp and enemy damaging casts before movement',
    'd8': 'D6 plus stationary casts',
    'a2': 'Post-walk attack reset',
    'd9': 'D6 plus post-walk attack reset',
    's1': 'Visible-power disengagement and risk-sensitive banking',
    'd10': 'D6 plus disengagement and banking',
    'a3': 'Use legal remaining basic attack after a dash',
    'd11': 'D6 plus legal post-dash basic attack',
    'd12': 'Parallel nearby second clearing pair',
    'v1': 'Objective and banking-route personal wards',
    'l1': 'Time existing altar-lock consumables against visible threats',
    'd13': 'Hoist repeated crew and claim calculations out of candidate loop',
    'd14': 'Allow middle camps with an enemy-side travel cost',
}
BASES = {'d2b': 'd1', 'd3': 'd2b', 'd4': 'd3', 'd5': 'd4', 'd6': 'd5', 'd7': 'd6',
         'd8': 'd6', 'd9': 'd6', 'd10': 'd6', 'd11': 'd6', 'd12': 'd6', 'd13': 'd12', 'd14': 'd13'}


def read(name):
    return json.loads((OPS / name).read_text(encoding='utf8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = read('V58_EXPERIMENTS.json')
    rows = []
    for label in LABELS:
        stem = 'results/v58-' + label
        valid, bayes, cluster = (read(stem + '-' + kind + '.json') for kind in ('validation', 'bayes', 'cluster'))
        assert valid['passed'] and valid['games'] == 224 and not any(valid['faults'].values())
        assert bayes['games'] == cluster['games'] == valid['games']
        build = ROOT / ('artifacts/evaluations/v58-' + label + '-build')
        seed1 = {p.name: sha(p) for p in (build / 'src-cand-s1/src').iterdir() if p.is_file()}
        assert seed1 == manifest[label]['files'], (label, 'benchmark seed1 differs from preserved snapshot')
        row = dict(label=label, description=DESCRIPTIONS[label], source_sha256=manifest[label]['source_sha256'],
                   games=valid['games'], wins=valid['wins'], raw_margin=valid['mean_margin'],
                   win_rate=valid['win_rate'], bayesian_mean=bayes['gems_mean'], p_gain=bayes['p_gain'],
                   p_gain_neg50=bayes.get('p_gain_neg50'), cluster_ci95=cluster['gem_ci95'],
                   faults=valid['faults'], fuel_per_game={s: v / valid['games'] for s, v in valid['fuel'].items()},
                   bayes_accept=bayes['gems_mean'] >= 25 and bayes['p_gain'] >= .95,
                   positive_cluster_interval=cluster['gem_ci95'][0] > 0,
                   incomplete_noninferiority=bayes['gems_mean'] >= -25 and bayes.get('p_gain_neg50', 0) >= .9,
                   state='not retained', evidence_stem='artifacts/claude_ops/' + stem,
                   wasm_sha256={side: {str(seed): sha(build / f'{file}-s{seed}.wasm') for seed in range(1, 5)}
                                for side, file in [('candidate', 'cand'), ('baseline', 'opp')]})
        if label in BASES:
            base = BASES[label]
            row['incremental_base'] = base
            pair = 'results/v58-' + label + '-vs-' + base
            cb, cc = read(pair + '-bayes.json'), read(pair + '-cluster.json')
            row['incremental'] = dict(bayesian_mean=cb['gems_mean'], p_gain=cb['p_gain'],
                                      cluster_ci95=cc['gem_ci95'], raw_margin=cc['gem_mean'])
        for suffix in ('mechanisms', 'actions', 'locks'):
            if (OPS / (stem + '-' + suffix + '.json')).exists():
                row[suffix + '_report'] = 'artifacts/claude_ops/' + stem + '-' + suffix + '.json'
        rows.append(row)
    result = dict(status='not submitted', sdk='3.0.5', engine='1.0.3',
                  development_maps=28, seeds=[1, 2, 3, 4], completed_screens=len(rows),
                  total_screen_games=sum(r['games'] for r in rows), invalid_builds=['d2'],
                  diagnostic_games_excluded=8, accepted_mechanisms=[],
                  note='Twenty repeated screens are development research, not independent confirmation. No holdouts were opened.',
                  variants=rows)
    (OPS / 'V58_RESULTS.json').write_text(json.dumps(result, indent=1) + '\n', encoding='utf8')
    lines = ['# v58 development screens — not submitted', '',
             '28 development maps × both sides × seeds1–4 =224 games per screen;20 screens =4480 games.',
             'Every completed screen has exact coverage and zero native faults on both teams. D2 failed to build and is excluded.',
             'Eight diagnostic games are excluded. All results use SDK3.0.5 / engine1.0.3; Sprint3 changes were not applied.', '',
             '| Variant | Wins/224 | Raw gems | Bayes mean | P(>0) | Map-cluster95% | Fuel/game |',
             '|---|---:|---:|---:|---:|---|---:|']
    for r in rows:
        lo, hi = r['cluster_ci95']
        lines.append(f"| {r['label']} | {r['wins']:.0f} | {r['raw_margin']:+.1f} | {r['bayesian_mean']:+.1f} | "
                     f"{r['p_gain']:.3f} | [{lo:+.1f}, {hi:+.1f}] | {r['fuel_per_game']['candidate']:.3f} |")
    lines += ['', 'No screen reaches mechanism acceptance (Bayes mean≥25, P(>0)≥.95); none has a positive clustered lower bound.',
              'No screen passes incomplete-loop non-inferiority. No12-seed confirmation or once-only holdout was justified.', '',
              '## Incremental comparisons', '',
              'These compare each revision with the prototype it modifies, using paired map/side/seed observations.', '',
              '| Change vs base | Raw gain | Bayes mean | P(>0) | Map-cluster95% |', '|---|---:|---:|---:|---|']
    assert not any(r['bayes_accept'] or r['positive_cluster_interval'] or r['incomplete_noninferiority'] for r in rows)
    for r in rows:
        if 'incremental' not in r:
            continue
        v = r['incremental']; lo, hi = v['cluster_ci95']
        lines.append(f"| {r['label']} vs {r['incremental_base']} | {v['raw_margin']:+.1f} | {v['bayesian_mean']:+.1f} | "
                     f"{v['p_gain']:.3f} | [{lo:+.1f}, {hi:+.1f}] |")
    lines += ['', 'An incremental improvement inside a losing loop does not make the complete loop acceptable.', '',
              '## Reproduction', '',
              'Use `python tools/reproduce_v58.py <variant> <new repo-local directory>`; it verifies every source-file hash.',
              'Then run `bash artifacts/claude_ops/bench3.sh "$PWD/<directory>" "$PWD/bots/v57" "$PWD/artifacts/evaluations/<new-prefix>" 1 2 3 4`.',
              'Use the same pinned SDK/engine. Every normal run returned0; `check_bench_run.py` verifies exact224-game coverage and both fault counts.',
              'Run `bench_bayes.py <prefix> --json <out>` and `bench_compare.py <prefix> [base-prefix] --json <out>`.',
              'Use the optional replay-report tools listed in V58_BUILD_LOG.md for mechanism audits. Raw replays remain local-only.', '']
    (OPS / 'V58_RESULTS.md').write_text('\n'.join(lines), encoding='utf8')
    print(result['completed_screens'], 'screens;', result['total_screen_games'], 'games; no accepted mechanism')


if __name__ == '__main__':
    main()
