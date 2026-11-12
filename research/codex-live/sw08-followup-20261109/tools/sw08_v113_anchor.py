"""Try the verified stall repairs on the actual v113 strategy and weight baseline."""
import concurrent.futures
from pathlib import Path
import sys

from local_panel import artifact, run
from project import ARENA, ROOT, ENGINE, ENGINE_HASH, digest, save, sha
from qualify_campaign import comparison, fuel_rate, package
from retune_campaign import aggregate
from stall_campaign import analyze
from sw08_followup import STYLES, build_from, freeze_plan, load, replace

WORK = ROOT/'sw08-followup/v113-anchor'
DEV_STYLES = ['b111', 'nnm4', 'v92', 'ref_hold_rush100']
NAMES = ['rv01', 'rv02', 'rv03']


def literal_v113(files, trained):
    source = ARENA/'bots/sf06/src'
    repaired = (source/'bot.cpp').read_text(encoding='utf-8')
    files['integration.h'] = (source/'integration.h').read_bytes().replace(b'{15, 1}', b'{5, 1}')
    for name in ('world.cpp', 'world.h', 'nnrec.cpp'):
        files[name] = (source/name).read_bytes()
    if trained:
        files['nn_weights.h'] = (ARENA/'bots/sfhs002/src/nn_weights.h').read_bytes()

    h = files['bot.h'].decode().replace('\r\n', '\n')
    for marker, addition in (
        ('    int nn_ens_sample(int v92g);', '    bool nn_target_allowed(int group, int observed_state) const;\n'),
        ('    bool go_home_if_needed();', '    bool integration_release_spawn();\n'),
        ('    std::vector<int> avoid_until;', '    std::vector<int> ally_yield_until;\n'),
    ):
        h = replace(h, marker, addition + marker)
    files['bot.h'] = h.encode()
    c = files['bot.cpp'].decode().replace('\r\n', '\n')
    c = replace(c, '#include "a2map.h"', '#include "a2map.h"\n#include "integration.h"\nstatic volatile int stall_repairs = 5;')
    start = repaired.index('bool Bot::integration_release_spawn()')
    stop = repaired.index('    if (type == bc::champion_type::tavi && hp >= max_hp * tune::kRetreatHp)', start)
    old_start = c.index('bool Bot::go_home_if_needed()')
    old_stop = c.index('    if (type == bc::champion_type::tavi && hp >= max_hp * tune::kRetreatHp)', old_start)
    c = c[:old_start] + repaired[start:stop] + c[old_stop:]
    c = replace(c, '    } else if (go_home_if_needed()) {',
                '    } else if (integration_release_spawn()) {\n    } else if (go_home_if_needed()) {')
    marker = '    if (avoid_until.size() != w.groups.size()) avoid_until.assign(w.groups.size(), 0);'
    c = replace(c, marker, marker + '''
    if (ally_yield_until.size() != w.groups.size()) ally_yield_until.assign(w.groups.size(), 0);''')
    for n in (6, 3, 4):
        token = f'avoid_until[gi] = round + {n};'
        c = replace(c, token, f'avoid_until[gi] = ally_yield_until[gi] = round + {n};')
    c = replace(c, 'avoid_until[best] = round + 8;', 'avoid_until[best] = ally_yield_until[best] = round + 8;')
    start = repaired.index('    if ((stall_repairs & 1) && nn_group')
    stop = repaired.index('#ifdef A2_NN_NEED', start)
    c = replace(c, '#ifdef A2_NN_NEED\n', repaired[start:stop] + '#ifdef A2_NN_NEED\n')
    files['bot.cpp'] = c.encode()


def narrower_integration(files):
    files['integration.h'] = files['integration.h'].replace(b'{15, 1}', b'{13, 1}')
    assert b'{13, 1}' in files['integration.h']
    files['nn_weights.h'] = (ARENA/'bots/b113/src/nn_weights.h').read_bytes()


def plan():
    prior = freeze_plan()
    old = load(ROOT/'campaign.json')
    spent = {h for m in (prior, old) for role in m['maps'].values() for h in role.values()}
    spent |= set(load(ROOT/'qualification-stall/protocol.json')['maps'].values())
    maps = sorted((ARENA/'maps_v113_stability').glob('*.map26a'))
    assert len(maps) == 112
    hashes = {str(p): sha(p) for p in maps}
    assert len(set(hashes.values())) == 112 and not (set(hashes.values()) & spent)
    result = {'dev': {str(p): hashes[str(p)] for p in maps[:24]},
              'reserve': {str(p): hashes[str(p)] for p in maps[24:72]},
              'final': {str(p): hashes[str(p)] for p in maps[72:]},
              'engine': ENGINE, 'engine_hash': ENGINE_HASH,
              'expected_ladder': {'version': 113, 'id': 'ff2f3acc-c4af-48fd-b2a2-85121a367e64'},
              'gate': {'minimum_reference_gain': .02, 'minimum_cluster_lower_bound': 0.0,
                       'direct_v113_above': .50, 'worst_style_drop': .10,
                       'fuel_ratio_max': 1.15, 'fixture_stall_increase_max': .15},
              'excluded_from_release_selection': 'All earlier final-map hashes, including the failed sfhs002 holdout'}
    p = WORK/'plan.json'
    if p.exists():
        assert load(p) == result
    else:
        save(p, result)
    return result


def screen():
    p = plan()
    jobs = [('rv01', 'b113', lambda f: literal_v113(f, False)),
            ('rv02', 'b113', lambda f: literal_v113(f, True)),
            ('rv03', 'sf06', narrower_integration)]
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda j: build_from(*j), jobs))
    maps = list(map(Path, p['dev']))
    refs = run('sw08-v113-anchor-dev-reference', [*NAMES,'b113'], maps, DEV_STYLES, 12)
    direct = run('sw08-v113-anchor-dev-direct', NAMES, maps, ['b113'], 12)
    rs, ds = aggregate(refs), aggregate(direct)
    base = rs['b113']
    winners = []
    for n in NAMES:
        q, d = rs[n], ds[n]
        valid = not (q['faults'] or d['faults']) and q['score'] >= base['score'] - .01 and d['score'] >= .50
        if valid:
            winners.append(n)
    n = max(winners, key=lambda n: rs[n]['score'] + .40 * ds[n]['score']) if winners else None
    result = {'winner': n, 'scores': rs, 'direct': ds, 'plan_sha256': sha(WORK/'plan.json'),
              'candidates_meeting_development_floor': winners}
    if n:
        result.update(source_sha256=digest(ARENA/'bots'/n/'src'), wasm_sha256=sha(artifact(n)))
    save(WORK/'selection.json', result)
    print({'winner': n, 'reference': {n: q['score'] for n,q in rs.items()},
           'direct': {n: d['score'] for n,d in ds.items()}}, flush=True)


def qualify():
    p = plan()
    selected = load(WORK/'selection.json')
    name = selected['winner']
    if not name:
        print('The v113-anchored controls did not clear development.', flush=True)
        return
    assert sha(artifact(name)) == selected['wasm_sha256']
    assert digest(ARENA/'bots'/name/'src') == selected['source_sha256']
    public = load(ROOT/'campaign.json')
    fixtures = [Path(p) for p in public['maps']['dev'] if Path(p).stem in ('01islands','03homonoliths')]
    pubmaps = [Path(p) for p in public['maps']['final'] if Path(p).parent.name != 'maps_generated_v113']
    locked = {**p, 'selection_sha256': sha(WORK/'selection.json'), 'candidate': name,
              'artifacts': {n: sha(artifact(n)) for n in (name,'b113','sw08')},
              'reference_styles': STYLES, 'published_direct': {str(p): sha(p) for p in pubmaps},
              'stall_fixtures': {str(p): sha(p) for p in fixtures}}
    pp = WORK/'protocol.json'
    if pp.exists():
        assert load(pp) == locked
    else:
        save(pp, locked)
    f = list(map(Path, p['final']))
    refs = run('sw08-v113-anchor-final-reference', [name,'b113','sw08'], f, STYLES, 12)
    direct = run('sw08-v113-anchor-final-direct', [name], f, ['b113'], 12)
    published = run('sw08-v113-anchor-published-direct', [name], pubmaps, ['b113'], 10)
    sr = run('sw08-v113-anchor-stall-fixtures', [name,'sw08','b113'], fixtures,
             ['b111','teammate_john_nnfinal'], 8)
    analyze('sw08-v113-anchor-fixtures', sr)
    stalls = load(ROOT/'stall-audit/sw08-v113-anchor-fixtures.json')
    quiet = {n: s['counts']['trailing_quiet_pairs']/s['counts']['alive_pairs'] for n,s in stalls.items()}
    c = {n: comparison(refs, name, n) for n in ('b113','sw08')}
    rates = {n: fuel_rate(refs,n) for n in (name,'b113','sw08')}
    a, b = aggregate(direct)[name], aggregate(published)[name]
    g = p['gate']
    threshold = min(quiet['b113'], quiet['sw08'] * (1 + g['fixture_stall_increase_max']))
    gates = {'zero_faults_and_codes': not any(r['faults'] or r['opponent_faults'] or r['diagnostic_codes']
                                             for r in refs+direct+published+sr),
             'reference_gain': c['b113']['gain'] >= g['minimum_reference_gain'],
             'positive_cluster_confidence': c['b113']['map_cluster_bootstrap_95'][0] >= g['minimum_cluster_lower_bound'],
             'direct_v113_above_half': a['score'] > g['direct_v113_above'],
             'published_active_bounded': b['score'] >= .45,
             'worst_style_bounded': min(c['b113']['style_deltas'].values()) >= -g['worst_style_drop'],
             'fuel_rate_bounded': rates[name]['per_1000_scheduled_champion_rounds'] <=
                                  rates['b113']['per_1000_scheduled_champion_rounds'] * g['fuel_ratio_max'],
             'stall_guard_pass': quiet[name] <= threshold}
    report = {'candidate': name, 'expected_ladder': p['expected_ladder'], 'gates': gates,
              'approved_for_upload': all(gates.values()), 'comparisons': c, 'head_to_head': a,
              'published_direct': b, 'stall_rates': quiet, 'fuel_rates': rates,
              'games': len(refs)+len(direct)+len(published)+len(sr),
              'source_sha256': selected['source_sha256'], 'wasm_sha256': selected['wasm_sha256'],
              'protocol_sha256': sha(pp)}
    target = WORK/'qualification.json'
    save(target, report)
    package(name, report, target)
    print({'candidate': name, 'gates': gates, 'direct': a['score']}, flush=True)


if __name__ == '__main__':
    {'screen': screen, 'qualify': qualify}[sys.argv[1]]()
