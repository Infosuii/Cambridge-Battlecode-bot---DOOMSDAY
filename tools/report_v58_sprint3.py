"""Rebuild the Sprint3 v58 release evidence from completed immutable runs, without running or submitting games."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / 'research/v58'


def read(name):
    return json.loads((OPS / name).read_text(encoding='utf8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    names = ['core', 'economy', 'economy-confirm', 'fastgroups', 'fastgroups-confirm', 'holdout12', 'fresh15', 'new02']
    runs = {}
    for label in names:
        prefix = 'v58-s3-' + label
        validation = read('results/' + prefix + '-validation.json')
        assert validation['passed'] and validation['engine_versions'] == ['2.0.0']
        runs[label] = dict(prefix='artifacts/evaluations/' + prefix, **validation)
        runs[label]['candidate_fuel_per_game'] = validation['fuel']['candidate'] / validation['games']
        for kind in ['cluster', 'bayes']:
            path = OPS / ('results/' + prefix + '-' + kind + '.json')
            if path.exists():
                runs[label][kind] = json.loads(path.read_text())
    final = runs['fastgroups-confirm']
    assert final['games'] == 672 and final['win_rate'] >= .53
    assert final['bayes']['p_gain'] >= .95 and final['bayes']['gems_mean'] >= 50
    assert final['cluster']['gem_ci95'][0] > 0 and final['candidate_fuel_per_game'] <= 2
    for label in ['holdout12', 'fresh15', 'new02']:
        assert runs[label]['win_rate'] >= .5 and runs[label]['mean_margin'] >= 0 and runs[label]['candidate_fuel_per_game'] <= 2
    src = ROOT / 'bots/v58/src'
    files = {p.name: sha(p) for p in sorted(src.iterdir()) if p.is_file()}
    source_hash = hashlib.sha256(b''.join(p.name.encode() + b'\0' + p.read_bytes() for p in sorted(src.iterdir()) if p.is_file())).hexdigest()
    proof = read('results/v58-s3-clean-build.json')
    assert proof['source_sha256'] == source_hash and proof['byte_identical'] and proof['bundle_source_exact']
    seeds = {}
    for seed in range(1, 13):
        build = ROOT / 'artifacts/evaluations/v58-s3-fastgroups-confirm-build'
        seeded_src = build / f'src-cand-s{seed}/src'
        for name in files:
            expected = (src / name).read_bytes()
            if name == 'common.h':
                expected = expected.replace(b'#define NOVA_SEED 1\n', f'#define NOVA_SEED {seed}\n'.encode())
            assert (seeded_src / name).read_bytes() == expected
        seeds[str(seed)] = dict(candidate=sha(build / f'cand-s{seed}.wasm'), opponent=sha(build / f'opp-s{seed}.wasm'))
    facts = read('results/v58-s3-native-progress.json')
    mechanisms = read('results/v58-s3-final-mechanisms.json')
    assert facts['games'] == 672 and mechanisms['games'] == 56 and mechanisms['analysis_seeds'] == ['1']
    metrics = mechanisms['metrics']
    shortfalls = dict(capture_gold_R250=dict(candidate=metrics['capture_gold_R250']['candidate']['mean'], baseline=metrics['capture_gold_R250']['opponent']['mean'], target=900),
                      elk_captures_R250=dict(candidate=metrics['elk_captures_R250']['candidate']['mean'], target=3.5),
                      carry_share=dict(candidate=metrics['carry_capture_share_R250']['candidate']['mean'], target=.4),
                      deaths_reduction=1-facts['candidate']['deaths_final']/facts['opponent']['deaths_final'],
                      explanation='The user requested the whole combined package and then Sprint3 support. Dedicated carry/director packages lost strength and remain off. This package improves distributed economy and legal capture retention. Prospector replaces nerfed Treasure; Capture follows mitigation and is mostly a mid-game purchase. Capture/elk/carry targets and30% death reduction were not reached; CHANGES.md explains them. No Claudus proxy qualified.')
    summary = dict(engine='2.0.0', sdk_cli='4.0.0', source_sha256=source_hash, competitive_games_played=sum(x['games'] for x in runs.values()),
                   distinct_configuration_slots=1904, duplicate_note='Screen seeds1-4 overlap the confirmation sets; they are not additional independent observations.',
                   runs=runs, mechanisms=shortfalls, native_progress=facts, all_release_checks_passed=True)
    (OPS / 'V58_SPRINT3_RESULTS.json').write_text(json.dumps(summary, indent=1) + '\n', encoding='utf8')
    lines = ['# v58 Sprint3 combined package', '', 'All runs use official CLI/SDK4.0.0, engine2.0.0 and default fuel. Frozen v57 is rebuilt with the same SDK. No bot source was changed during or after the final checks.', '',
             '| Run | Games | Wins | Margin | Candidate fuel/game |', '|---|---:|---:|---:|---:|']
    for label, data in runs.items():
        lines.append(f"| {label} | {data['games']} | {data['wins']:.0f} ({data['win_rate']:.1%}) | {data['mean_margin']:+.1f} | {data['candidate_fuel_per_game']:.3f} |")
    lines += ['', f"Final map-cluster95%[{final['cluster']['gem_ci95'][0]:+.1f},{final['cluster']['gem_ci95'][1]:+.1f}]; Bayes mean{final['bayes']['gems_mean']:+.1f}, P(gain)={final['bayes']['p_gain']:.4f}. All native faults0 on both teams. All three final pools exceed50% wins/nonnegative margin, with candidate fuel<=2/game.", '',
              'The fast camp-contact path was checked against the original calculation on every observation of six diagnostic games, with zero assertion faults. A separate profiling build and a discarded optimization for an inactive belief feature are excluded from strength evidence. Four smoke games are also excluded.', '',
              '2352 competitive games were played, with1904 distinct configuration/map/side/seed slots. Screening and confirmation overlap. Reused old fresh maps have historical exposure; the new02 pool had recent-loss analysis exposure. These are local lineage comparisons, not a claim of rank25 or measured superiority to Claudus.', '',
              f"Mechanism audit:56 seed1 games, all28 development maps/both sides. R250 capture gold{shortfalls['capture_gold_R250']['candidate']:.1f} vs{shortfalls['capture_gold_R250']['baseline']:.1f}, elk captures{shortfalls['elk_captures_R250']['candidate']:.2f}, carry share{shortfalls['carry_share']['candidate']:.1%}. Full672-game deaths down{shortfalls['deaths_reduction']:.1%}. Original900/3.5/40%/30% targets remain unmet and explained in CHANGES.md; no proxy qualifies.", '',
              f"Native672-game R250 income{facts['candidate']['earnedGold']:.1f} vs{facts['opponent']['earnedGold']:.1f}, including kills/bonuses; do not label this capture income. Prospector is acquired in every candidate game; Capture in618 games and Greed in387. Timing is conditional on acquisition.", '',
              'Clean source-only build matches benchmark seed1 byte for byte. Official bundle has33 source files,279034 bytes, exact per-file source identity. Full proof and hashes are in results/v58-s3-clean-build.json.']
    (OPS / 'V58_SPRINT3_RESULTS.md').write_text('\n'.join(lines) + '\n', encoding='utf8')
    release = dict(candidate='bots/v58', baseline='bots/v57 (frozen source, rebuilt with SDK4.0.0)', status='validated; not submitted yet', submitted=False,
                   authorization='User authorized submission once definite improvement; strict v58 final gate retained. Whole-package evaluation and Sprint3 migration explicitly requested. No match groups queued.',
                   sdk_cli_version='4.0.0', engine_version='2.0.0', fuel='Official CLI default100000 per turn; official opening budget doubled. No --fuel override.',
                   source_sha256_method='sha256 over sorted file name + NUL + raw source bytes, same as bench3', source_sha256=source_hash, source_files=files,
                   switches=dict(re.findall(r'^#define (V58_\w+) (\S+)', (src / 'common.h').read_text(encoding='utf8'), re.M)), additional_enabled_switches={'A2_FASTGRP': 1},
                   wasm_sha256_by_seed=seeds, clean_build=proof, build_environment=json.loads((ROOT / 'artifacts/evaluations/v58-s3-fastgroups-confirm-environment.json').read_text(encoding='utf8')),
                   gate=dict(passed=True, development=final, original_holdout=runs['holdout12'], previous_fresh_holdout=runs['fresh15'], additional_new02_check=runs['new02'],
                             proxy='not created: capture income/carry concentration targets were not reached', mechanism_shortfalls=shortfalls, shortfalls_explained_in='bots/v58/CHANGES.md', independent_build=True, exact_source_bundle=True),
                   results='research/v58/V58_SPRINT3_RESULTS.json', loss_review='research/v57/V57_SPRINT3_LOSS_REVIEW.json',
                   platform_version=None, submitted_at_utc=None, upload_bytes=None, source_commit=None,
                   provenance_limit='The CLI provides no platform read-back of source content/hash. Submission verification will check exact local source/bundle and reported upload size, then compilation/active selection.')
    existing = read('V58_RELEASE.json')
    if existing.get('submitted'):
        raise SystemExit('Refusing to overwrite a completed submission record')
    (OPS / 'V58_RELEASE.json').write_text(json.dumps(release, indent=1) + '\n', encoding='utf8')
    print('Release checks PASS; source', source_hash)


if __name__ == '__main__':
    main()
