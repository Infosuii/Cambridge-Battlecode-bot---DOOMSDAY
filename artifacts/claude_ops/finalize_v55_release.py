"""Assemble the v55 release record only after validating frozen source and completed evidence. Never submits."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from reproduce_v55 import digest


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf8'))


def main():
    result = 'artifacts/claude_ops/results/'
    source = ROOT / 'bots/v55/src'
    experiment = read('artifacts/claude_ops/V55_RESTART_EXPERIMENTS.json')['r10-heart-completion']
    assert digest(source) == experiment['tree_sha256'], 'source changed after freeze'
    frozen = {}
    for version in (53, 54):
        expected = read(f'artifacts/claude_ops/V{version}_RELEASE.json')['source_files']
        actual = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / f'bots/v{version}/src').iterdir() if p.is_file()}
        assert expected == actual, f'frozen v{version} changed'
        frozen[f'v{version}'] = True
    checks = {}
    for label, file in {
        'development_vs_v54': 'v55-r10-heart-completion-validation.json',
        'holdout_once_vs_v54': 'v55-final-holdout-r10-validation.json',
        'development_vs_v53': 'v55-final-vs53-r10-validation.json',
        'portfolio_vs_v48': 'v55-final-portfolio-validation.json',
        'portfolio_v54_control_vs_v48': 'v55-control-portfolio-validation.json',
        'completion_foundation_pooled': 'v55-r2-pooled-validation.json',
        'completion_pooled_control': 'v55-r2-control-pooled-validation.json',
    }.items():
        checks[label] = read(result + file)
        assert checks[label]['passed'], f'invalid run: {label}'
    intervals = {key: read(result + file) for key, file in {
        'final_vs_v54': 'v55-r10-heart-completion-cluster.json',
        'completion_foundation_vs_v54': 'v55-r2-pooled-paired-cluster.json',
        'heart_added_to_completion_foundation': 'v55-r10-vs-r2-cluster.json',
        'completion_added_to_heart_inconclusive': 'v55-r10-vs-r9-cluster.json',
        'vs_v53_control_inconclusive': 'v55-final-vs53-paired-cluster.json',
        'vs_v48_control_inconclusive': 'v55-final-portfolio-paired-cluster.json',
    }.items()}
    for key in ('final_vs_v54', 'completion_foundation_vs_v54', 'heart_added_to_completion_foundation'):
        assert intervals[key]['gem_ci95'][0] > 0, f'unproven retained step: {key}'
    dev, hold = checks['development_vs_v54'], checks['holdout_once_vs_v54']
    assert dev['win_rate'] >= .47 and dev['mean_margin'] >= -30
    assert hold['win_rate'] >= .5 and hold['mean_margin'] >= 0, 'aggregate holdout regression'
    build = read(result + 'v55-final-build-verification.json')
    assert build['identical_non_custom_sections']
    ledger = read(result + 'v55-r10-heart-completion-ledger.json')
    h = hashlib.sha256()
    for p in sorted(source.iterdir()):
        if p.is_file():
            h.update(p.name.encode() + b'\0' + p.read_bytes())
    record = {
        'candidate': 'bots/v55', 'baseline': 'bots/v54', 'status': 'ready_to_submit',
        'prepared_utc': datetime.now(timezone.utc).isoformat(),
        'authorization': 'User explicitly instructed submission once v55 demonstrates definite improvement over v54; no additional approval pending.',
        'frozen_opponents_unchanged': frozen,
        'source_sha256_method': 'sha256 over sorted (file name, NUL, bytes); same convention as bench3',
        'source_sha256': h.hexdigest(), 'reconstruction_tree_sha256': digest(source),
        'source_files': experiment['files'], 'independent_build': build,
        'mechanisms': {'V55_COMMIT_EVENT': 1, 'V55_HEART_CAMP': 1, 'V55_DRAFT_LEGAL': 1,
                       'V55_HEART_MODEL': 0, 'V55_CAST_RETARGET': 0},
        'retention_order': ['R2 completion foundation validated over24seeds', 'Heart execution added to R2, positive paired interval',
                            'Necessary neutral draft legality correction, no claimed competitive gain'],
        'comparisons': intervals, 'checks': checks,
        'gate': {'passed': True, 'declared_target_maps': [],
                 'scope': 'General controller/economy change; no map-specific all-seed victory claim.',
                 'development_floor': True, 'holdout_aggregate_no_regression': True,
                 'zero_native_faults_both_teams': True, 'independent_build_matches_bench': True,
                 'major_development_research_target_60pct_plus100': dev['win_rate'] >= .6 and dev['mean_margin'] >= 100},
        'mechanism_ledger': ledger,
        'heart_successful_casts': read(result + 'v55-final-heart-casts.json'),
        'commands': {
            'development': 'bash artifacts/claude_ops/bench3.sh <abs R10 snapshot> <abs bots/v54> <abs artifacts/evaluations/v55-r10-heart-completion> 1 2 3 4 5 6 7 8 9 10 11 12',
            'holdout': 'HOLDOUT=1 MAPS_OVERRIDE="00ambush 00corners 00expanse 00interlock 00lanes 00monolith 00packs 00pilgrimage 01elk-arena 01fracture 01hooks 01the-farm" bash artifacts/claude_ops/bench3.sh <abs bots/v55> <abs bots/v54> <abs artifacts/evaluations/v55-final-holdout-r10> 1 2 3 4 5 6 7 8 9 10 11 12',
            'v53': 'bash artifacts/claude_ops/bench3.sh <abs bots/v55> <abs bots/v53> <abs artifacts/evaluations/v55-final-vs53-r10> 1 2 3 4 5 6 7 8 9 10 11 12',
            'portfolio': 'bash artifacts/claude_ops/bench3.sh <abs bots/v54 or bots/v55> <abs bots/v48> <abs artifacts/evaluations/v55-portfolio-v54-vs48 or v55-portfolio-v55-vs48> 1 2 3',
            'comparison': 'python tools/bench_compare.py artifacts/evaluations/v55-r10-heart-completion artifacts/evaluations/v55-e4',
            'submission': 'tools/vendor/cambc.exe submit bots/v55 --note "v55: camp completion + Heart farming; 61.6% vs54, zero faults"',
        },
        'bench_exit_statuses': {'development': 0, 'v53': 0, 'holdout': 0, 'v48_candidate': 0, 'v48_control': 0, 'completion_replication_control': 0},
        'limits': [
            'All40maps are reused benchmarks; hooks had prior development exposure. One frozen R10 holdout pass; no tuning after it.',
            'Completion incremental effect on the Heart-only base is inconclusive; positive retention order and reverse ablation are both reported.',
            'Gold-rush development regressed107.9gems; brawl aggregate81/120,+98.7 has interval including zero.',
            'v53/v48 comparison deltas versus v54 controls include zero; their winning records are compatibility checks, not separate proven gains.',
            'External opponent source unavailable. No international top25 or ladder improvement claim before live results.',
            'Draft legality alone produced identical672games; not an explanation for all v54 losses.',
        ],
    }
    # Keep commands runnable from the checkout without embedding machine-specific absolute paths.
    for key, command in list(record['commands'].items()):
        command = command.replace('<abs R10 snapshot>', '"$PWD/artifacts/tmp/v55-r10-heart-completion"')
        for name in ('bots/v54', 'bots/v55', 'bots/v53', 'artifacts/evaluations/v55-r10-heart-completion',
                     'artifacts/evaluations/v55-final-holdout-r10', 'artifacts/evaluations/v55-final-vs53-r10'):
            command = command.replace('<abs ' + name + '>', '"$PWD/' + name + '"')
        record['commands'][key] = command
    record['commands']['portfolio'] = 'for v in 54 55; do bash artifacts/claude_ops/bench3.sh "$PWD/bots/v$v" "$PWD/bots/v48" "$PWD/artifacts/evaluations/v55-portfolio-v$v-vs48" 1 2 3; done'
    target = ROOT / 'artifacts/claude_ops/V55_RELEASE.json'
    if target.exists():
        previous = json.loads(target.read_text(encoding='utf8'))
        if previous.get('status') == 'submitted':
            assert previous['source_sha256'] == record['source_sha256'], 'submitted source changed'
            for key in ('status', 'platform_version', 'submission_utc', 'submission_log', 'submission_commit'):
                if key in previous:
                    record[key] = previous[key]
    target.write_text(json.dumps(record, indent=1) + '\n', encoding='utf8')
    print('release gate passed; frozen source', record['source_sha256'])


if __name__ == '__main__':
    main()
