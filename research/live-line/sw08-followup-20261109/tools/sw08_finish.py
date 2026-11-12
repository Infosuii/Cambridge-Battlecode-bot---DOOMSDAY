"""Select weights on development data, qualify once, and package the exact bot."""
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from local_panel import artifact, run
from project import ARENA, ROOT, ENGINE, ENGINE_HASH, check_stop, digest, save, sha
from qualify_campaign import comparison, fuel_rate, package
from retune_campaign import aggregate
from stall_campaign import analyze
from sw08_followup import PARENT, STYLES, WORK, build_from, freeze_plan, load

TRAIN = ROOT / 'training/sw08-followup-masked'
HANDOFF_TRAIN = ROOT / 'training/sw08-followup-handoff'
DIRECT_BASE = [PARENT, 'sf06', 'sf07', 'sfs000', 'sfs002']


def early_controls():
    maps = [Path(p) for p in freeze_plan()['maps']['dev']]
    run('sw08-followup-development-direct-controls', DIRECT_BASE, maps, ['b113', 'b114'], 8)
    run('sw08-followup-development-reference-control', [PARENT], maps, STYLES, 8)


def pick():
    receipt = WORK / 'selection.json'
    if receipt.exists():
        selected = load(receipt)['selected']
        assert selected['source_sha256'] == digest(ARENA/'bots'/selected['name']/'src')
        assert selected['wasm_sha256'] == sha(artifact(selected['name']))
        return
    data = load(TRAIN / 'complete.json')
    repair = load(WORK / 'training-parent.json')['parent']
    assert data['base_source'] == repair
    plan = freeze_plan()
    retry = load(WORK / 'handoff-retry.json')
    os.environ['TRAIN_SOURCE'] = repair
    os.environ['TRAIN_CAMPAIGN_NAME'] = TRAIN.name
    from train_campaign import actor, LAB
    import torch
    base = torch.load(plan['initial_checkpoint'], weights_only=True, map_location='cpu')
    checkpoints = [load(TRAIN / f'eval_{i}.json') for i in (0, 2, 4)]
    def utility(row):
        return row['score'] + .35 * row['opponents']['b111']
    chosen = max(checkpoints[1:], key=utility)
    trained = torch.load(TRAIN / f'student_{chosen["iteration"]}.pt', weights_only=True, map_location='cpu')
    labels = {r['actor']: {'alpha': 1.0 if r['iteration'] else 0.0,
                          'weight_checkpoint': str(TRAIN / f'student_{r["iteration"]}.pt'),
                          'trained_iteration': r['iteration']} for r in checkpoints}
    def blend_weights(n, alpha, updated):
        path = TRAIN / (n + '.pt')
        header = TRAIN / (n + '.h')
        for k, t in base.items():
            if not t.is_floating_point():
                assert torch.equal(t, updated[k])
        torch.save({k: t.lerp(updated[k], alpha) if t.is_floating_point() else t
                    for k, t in base.items()}, path)
        subprocess.run([sys.executable, '-P', str(LAB / 'nn_export.py'), str(path), 'student', str(header)],
                       check=True, capture_output=True)
        return path, header
    def make_blend(alpha):
        n = f'sfd{round(alpha * 100):02}'
        path, header = blend_weights(n, alpha, trained)
        actor(n, header)
        return n, {'alpha': alpha, 'weight_checkpoint': str(path), 'trained_iteration': chosen['iteration']}
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        labels.update(pool.map(make_blend, (.25, .50)))
    # Test whether the learned update survives the independently screened
    # capture preference, while retaining its unchanged-weight control.
    alternative = max(retry, key=lambda n: utility(retry[n]))
    header = TRAIN / 'sfd50.h'
    build_from('sfm50', alternative, lambda files: files.update({'nn_weights.h': header.read_bytes()}))
    labels['sfm50'] = {**labels['sfd50'], 'source_parent': alternative}
    deadline = time.monotonic() + 600
    while not (HANDOFF_TRAIN/'complete.json').exists():
        check_stop()
        assert time.monotonic() < deadline, 'Handoff training did not finish'
        time.sleep(2)
    assert load(HANDOFF_TRAIN/'complete.json')['base_source'] == alternative
    handoff_model = load(HANDOFF_TRAIN/'eval_2.json')
    labels[handoff_model['actor']] = {'alpha': 1.0, 'weight_checkpoint': str(HANDOFF_TRAIN/'student_2.pt'),
                                     'trained_iteration': 2, 'source_parent': alternative}
    handoff_weights = torch.load(HANDOFF_TRAIN/'student_2.pt', weights_only=True, map_location='cpu')
    path, header = blend_weights('sfhd50', .50, handoff_weights)
    build_from('sfhd50', alternative, lambda files: files.update({'nn_weights.h': header.read_bytes()}))
    labels['sfhd50'] = {'alpha': .50, 'weight_checkpoint': str(path), 'trained_iteration': 2,
                        'source_parent': alternative}
    maps = [Path(p) for p in plan['maps']['dev']]
    blends = ['sfd25', 'sfd50', 'sfm50', 'sfhd50']
    rows = run('sw08-followup-weight-blends', blends, maps, STYLES, 12)
    prior = ROOT/'panels/sw08-followup-development-reference-control/results.json'
    if not prior.exists():
        early_controls()
    rows += load(prior)
    pooled = {**aggregate(rows), **retry, **{r['actor']: r for r in [*checkpoints, handoff_model]}}
    variants = [PARENT, *blends, *retry, *(r['actor'] for r in [*checkpoints, handoff_model])]
    h2h = run('sw08-followup-development-direct', [n for n in variants if n not in DIRECT_BASE],
              maps, ['b113', 'b114'], 12)
    h2h += load(ROOT/'panels/sw08-followup-development-direct-controls/results.json')
    direct = aggregate(h2h)
    incumbent = pooled[PARENT]
    rankings = []
    for n in variants:
        p = pooled[n]
        score113 = direct[n]['opponents']['b113']
        score114 = direct[n]['opponents']['b114']
        rank = utility(p) + .40 * score113 + .10 * score114
        valid = (not p.get('faults', 0) and not direct[n]['faults'] and
                 p['fuel'] <= incumbent['fuel'] * 1.15 and p['score'] >= incumbent['score'] - .03 and n != PARENT)
        rankings.append({'name': n, 'valid': valid, 'rank': rank, 'pooled': p, 'head_to_head': direct[n],
                         'weights': labels.get(n)})
    rankings.sort(key=lambda r: (r['valid'], r['rank']), reverse=True)
    selected = rankings[0]
    assert selected['valid'], 'No runnable candidate met the development floor'
    n = selected['name']
    selected = {**selected, 'source_sha256': digest(ARENA / 'bots' / n / 'src'), 'wasm_sha256': sha(artifact(n))}
    save(receipt, {'selected': selected, 'ranking': rankings, 'parent': repair, 'trained_checkpoint': chosen,
                   'head_to_head_b113_weight': .4, 'head_to_head_b114_weight': .1,
                   'qualification_data_used': False})
    print(json.dumps({'selected': n, 'score': selected['pooled']['score'],
                      'b113': selected['head_to_head']['opponents']['b113']}), flush=True)


def qualify():
    chosen = load(WORK / 'selection.json')['selected']
    plan = freeze_plan()
    name = chosen['name']
    assert chosen['source_sha256'] == digest(ARENA / 'bots' / name / 'src')
    assert chosen['wasm_sha256'] == sha(artifact(name))
    controls = [PARENT, 'b113', 'b114']
    public = load(ROOT/'campaign.json')['maps']['dev']
    fixtures = {p: h for p, h in public.items() if Path(p).stem in ('01islands', '03homonoliths')}
    assert len(fixtures) == 2 and all(sha(p) == h for p, h in fixtures.items())
    published_direct = {p: h for p, h in load(ROOT/'campaign.json')['maps']['final'].items()
                        if Path(p).parent.name != 'maps_generated_v113'}
    assert len(published_direct) == 24 and all(sha(p) == h for p, h in published_direct.items())
    protocol = {'selection_sha256': sha(WORK / 'selection.json'), 'candidate': name,
                'maps': plan['maps']['final'], 'styles': STYLES, 'controls': controls,
                'head_to_head': ['b113', 'b114'], 'engine': ENGINE, 'engine_hash': ENGINE_HASH,
                'expected_ladder': {'version': 113, 'id': 'ff2f3acc-c4af-48fd-b2a2-85121a367e64'},
                'published_stall_fixtures': fixtures,
                'published_direct_maps': published_direct,
                'frozen_wasm': {n: sha(artifact(n)) for n in [name, *controls]},
                'gates': {'vs_active_pooled_gain': .02, 'vs_active_cluster_lower_bound': 0.0,
                          'vs_active_head_to_head_gt': .5, 'worst_style_drop_max': .10,
                          'vs_sw08_pooled_drop_max': .025, 'fuel_vs_active_ratio_max': 1.15,
                          'stall_vs_sw08_ratio_max': 1.15, 'zero_faults_and_codes': True}}
    p = WORK / 'protocol.json'
    if p.exists():
        assert load(p) == protocol
    else:
        save(p, protocol)
    maps = list(map(Path, protocol['maps']))
    assert all(sha(m) == protocol['maps'][str(m)] for m in maps)
    refs = run('sw08-followup-sealed-reference', [name, *controls], maps, STYLES, 12)
    direct = run('sw08-followup-sealed-direct', [name], maps, protocol['head_to_head'], 12)
    pubdirect = run('sw08-followup-published-direct', [name], list(map(Path, published_direct)),
                    protocol['head_to_head'], 10)
    audit = [r for r in refs if r['opponent'] == 'b111' and r['candidate'] in (name, PARENT)]
    analyze('sw08-followup-sealed-replays', audit)
    fixture_rows = run('sw08-followup-published-stalls', [name, PARENT], list(map(Path, fixtures)),
                       ['b111', 'teammate_john_nnfinal'], 8)
    analyze('sw08-followup-published-stalls', fixture_rows)
    published = load(ROOT/'stall-audit/sw08-followup-published-stalls.json')
    replay = load(ROOT/'stall-audit/sw08-followup-sealed-replays.json')
    quiet = {n: r['counts']['trailing_quiet_pairs']/r['counts']['alive_pairs'] for n, r in replay.items()}
    c = {n: comparison(refs, name, n) for n in controls}
    d = aggregate(direct)[name]
    rate = {n: fuel_rate(refs, n) for n in [name, *controls]}
    g = protocol['gates']
    b113 = c['b113']
    gates = {
        'zero_faults_and_codes': not any(r['faults'] or r['opponent_faults'] or r['diagnostic_codes'] for r in refs+direct),
        'current_reference_gain': b113['gain'] >= g['vs_active_pooled_gain'],
        'positive_cluster_confidence': b113['map_cluster_bootstrap_95'][0] >= g['vs_active_cluster_lower_bound'],
        'direct_v113_above_half': d['opponents']['b113'] > g['vs_active_head_to_head_gt'],
        'worst_style_bounded': min(b113['style_deltas'].values()) >= -g['worst_style_drop_max'],
        'parent_score_preserved': c[PARENT]['gain'] >= -g['vs_sw08_pooled_drop_max'],
        'fuel_rate_bounded': rate[name]['per_1000_scheduled_champion_rounds'] <=
                              rate['b113']['per_1000_scheduled_champion_rounds'] * g['fuel_vs_active_ratio_max'],
        'stall_guard_pass': quiet[name] <= quiet[PARENT] * g['stall_vs_sw08_ratio_max'],
        'published_active_bounded': aggregate(pubdirect)[name]['opponents']['b113'] >= .45,
    }
    report = {'candidate': name, 'expected_ladder': protocol['expected_ladder'], 'gates': gates,
              'approved_for_upload': all(gates.values()), 'comparisons': c, 'head_to_head': d,
              'stall_rates': quiet, 'published_stall_counts': {n: r['counts'] for n, r in published.items()},
              'published_direct': aggregate(pubdirect)[name], 'fuel_rates': rate,
              'games': len(refs)+len(direct)+len(pubdirect)+len(fixture_rows),
              'source_sha256': chosen['source_sha256'], 'wasm_sha256': chosen['wasm_sha256'],
              'protocol_sha256': sha(p)}
    r = WORK / 'qualification.json'
    save(r, report)
    package(name, report, r)
    print(json.dumps({'candidate': name, 'gates': gates, 'head_to_head': d['opponents']}), flush=True)


if __name__ == '__main__':
    {'pick': pick, 'qualify': qualify, 'early-controls': early_controls}[sys.argv[1]]()
