"""Select once on development evidence, then qualify on unused generated maps."""
from pathlib import Path
import math
import sys
from local_panel import artifact, run
from project import ARENA, ROOT, ENGINE, ENGINE_HASH, digest, save, sha
from qualify_campaign import comparison, fuel_rate, package
from retune_campaign import aggregate, ranking
from stall_campaign import PARENT, WD, analyze, read

OUT = ROOT / 'qualification-stall'
PANEL = ROOT / 'panels'


def selection():
    reports = [WD / (n + '-development.json') for n in ('targeted', 'reference', 'clear')]
    counts = {k: v['counts'] for p in reports for k, v in read(p).items()}
    sources = [PANEL / f'stall-{n}-development' / 'results.json'
               for n in ('fallthrough', 'targeted', 'reference', 'clear')]
    scores = aggregate([r for p in sources for r in read(p)])
    base = counts[PARENT]
    bq = base['trailing_quiet_pairs'] / base['alive_pairs']
    ordered = ranking(scores, PARENT)
    activated_clear = {'sw' + r['candidate'].removeprefix('stdebug').zfill(2) for r in read(WD / 'clear-activations.json')
                       if r['event'] == 'STALL_CLEAR'}
    candidates = []
    for arm in ordered:
        name = arm['name']
        if name in (PARENT, 'sw01', 'sw03'):
            continue
        c = counts[name]
        quiet = c['trailing_quiet_pairs'] / c['alive_pairs']
        if (arm['faults'] == 0 and arm['score'] >= scores[PARENT]['score'] - .015 and
                arm['fuel'] <= scores[PARENT]['fuel'] * 1.15 and quiet <= bq * .90):
            candidates.append(name)
    by_name = {r['name']: r for r in ordered}
    winner = candidates[0] if candidates else None
    if winner:
        # Prefer the repair that demonstrably addresses both reported failure
        # modes when the two options are within one percentage point in dev.
        winner = next((n for n in candidates if n in activated_clear and
                       by_name[n]['score'] >= by_name[winner]['score'] - .01 and
                       by_name[n]['utility'] >= by_name[winner]['utility'] - .01), winner)
    result = {'winner': winner, 'ranking': ordered, 'stall_counts': counts,
              'criteria': 'At least 10% fewer trailing quiet stall rounds per alive round; development score within 1.5 points of mx500; bounded fuel; zero faults.',
              'eligible': candidates, 'activated_spawn_clear': sorted(activated_clear),
              'selection_tie_break': 'Prefer observed activation for both fixes within 1 point in score and selection utility.',
              'development_panels_sha256': {p.parent.name: sha(p) for p in sources}}
    if winner:
        result.update(source_sha256=digest(ARENA / 'bots' / winner / 'src'), wasm_sha256=sha(artifact(winner)))
    save(OUT / 'selection.json', result)
    print({'winner': winner, 'eligible': candidates}, flush=True)
    return result


def qualify():
    receipt = OUT / 'selection.json'
    selected = read(receipt) if receipt.exists() else selection()
    name = selected['winner']
    if not name:
        raise SystemExit('No stall repair met the predeclared development requirements.')
    assert digest(ARENA / 'bots' / name / 'src') == selected['source_sha256']
    assert sha(artifact(name)) == selected['wasm_sha256']
    cfg = read(ROOT / 'campaign.json')
    exposed = {v for p in cfg['maps'].values() for v in p.values()}
    maps = [p for p in sorted((ARENA / 'maps_generated_v113').glob('*.map26a')) if sha(p) not in exposed]
    assert len(maps) == 28 and len({sha(p) for p in maps}) == len(maps)
    controls = ['b113', 'b114', PARENT]
    protocol = {'selection_sha256': sha(receipt), 'candidate': name, 'engine': ENGINE, 'engine_hash': ENGINE_HASH,
                'maps': {str(p): sha(p) for p in maps}, 'styles': cfg['styles'], 'controls': controls,
                'direct': ['b113', 'b114'], 'frozen_artifacts': {n: sha(artifact(n)) for n in [name, *controls]},
                'gates': 'No faults or diagnostic codes; at least +3 points vs v113 and v114, with positive map-cluster lower bounds, direct scores above half vs both, no style worse by more than ten points, fuel <= 1.15x v113, and trailing quiet stall rate lower than mx500 and v114.',
                'caveat': 'Unused generated maps; publication and ladder performance require separate evidence.'}
    protocol_file = OUT / 'protocol.json'
    if protocol_file.exists():
        assert read(protocol_file) == protocol
    else:
        save(protocol_file, protocol)
    rows = run('stall-sealed-reference', [name, *controls], maps, cfg['styles'], 12)
    direct = run('stall-sealed-direct', [name], maps, protocol['direct'], 12)
    comps = {n: comparison(rows, name, n) for n in controls}
    rate = {n: fuel_rate(rows, n) for n in [name, *controls]}
    head = {n: {'score': sum(r['score'] for r in direct if r['opponent'] == n),
                'games': sum(r['opponent'] == n for r in direct)} for n in protocol['direct']}
    audit = [r for r in rows if r['candidate'] in (name, PARENT, 'b114') and r['opponent'] == 'b111']
    analyze('sealed-stall-replay', audit)
    s = read(WD / 'sealed-stall-replay.json')
    quiet = {n: v['counts']['trailing_quiet_pairs'] / v['counts']['alive_pairs'] for n, v in s.items()}
    gates = {'zero_faults_and_codes': not any(r['faults'] or r['opponent_faults'] or r['diagnostic_codes'] for r in rows+direct),
             'fuel_rate_bounded': rate[name]['per_1000_scheduled_champion_rounds'] <=
                                  rate['b113']['per_1000_scheduled_champion_rounds'] * 1.15,
             'fewer_trailing_quiet_stalls': quiet[name] < min(quiet[PARENT], quiet['b114'])}
    for n in protocol['direct']:
        c = comps[n]
        gates[n + '_reference_gain'] = c['gain'] >= .03 and c['map_cluster_bootstrap_95'][0] > 0
        gates[n + '_direct'] = head[n]['score'] > head[n]['games'] / 2
        gates[n + '_worst_style_bounded'] = min(c['style_deltas'].values()) >= -.10
    result = {'candidate': name, 'approved_for_upload': all(gates.values()), 'gates': gates,
              'comparisons': comps, 'head_to_head': head, 'fuel_rates': rate,
              'trailing_quiet_stall_rates': quiet, 'games': len(rows) + len(direct),
              'protocol_sha256': sha(protocol_file), 'source_sha256': selected['source_sha256'],
              'wasm_sha256': selected['wasm_sha256']}
    path = OUT / 'result.json'
    save(path, result)
    package(name, result, path)
    print({'candidate': name, 'gates': gates}, flush=True)


def normalize_result():
    """Rebind the package if the in-flight runner encoded an empty slice as NaN."""
    p = OUT / 'result.json'
    r = read(p)
    changed = False
    for c in r['comparisons'].values():
        g = c['published_gain']
        if g is not None and not math.isfinite(g):
            assert c['maps'] == c['fresh_generated_maps']
            c['published_gain'] = None
            changed = True
    if changed:
        save(p, r)
        package(r['candidate'], r, p)


if __name__ == '__main__':
    {'select': selection, 'qualify': qualify, 'normalize': normalize_result}[sys.argv[1]]()
