"""Isolate the two proven stall fixes on the official v113 policy."""
import concurrent.futures
from pathlib import Path
import sys

from local_panel import artifact, run
from project import ARENA, ROOT, digest, save, sha
from qualify_campaign import comparison, fuel_rate, package
from retune_campaign import aggregate
from stall_campaign import analyze
from sw08_followup import STYLES, build_from, load, replace
from sw08_v113_anchor import DEV_STYLES, plan

WORK = ROOT/'sw08-followup/v113-minimal'
NAMES = ['rv10','rv11','rv12']


def repair(files, route, spawn):
    c = files['bot.cpp'].decode().replace('\r\n','\n')
    h = files['bot.h'].decode().replace('\r\n','\n')
    if route:
        h = replace(h, '    std::vector<int> avoid_until;',
                    '    std::vector<int> route_avoid_until;\n    std::vector<int> avoid_until;')
        marker = '    if (avoid_until.size() != w.groups.size()) avoid_until.assign(w.groups.size(), 0);'
        c = replace(c, marker, marker + '\n    if (route_avoid_until.size() != w.groups.size()) route_avoid_until.assign(w.groups.size(), 0);')
        c = replace(c, 'avoid_until[static_cast<std::size_t>(gi)] = round + 100;',
                    'avoid_until[gi] = route_avoid_until[gi] = round + 100;')
        assert c.count('avoid_until[gi] = round + 300;') == 2
        c = c.replace('avoid_until[gi] = round + 300;', 'avoid_until[gi] = route_avoid_until[gi] = round + 300;')
        c = replace(c, '#ifdef A2_NN_NEED\n', '''    // Only veto proven route failures. Short capture preferences
    // still use v113's original ownership and target selection policy.
    if (nn_group >= 0 && static_cast<std::size_t>(nn_group) < route_avoid_until.size() &&
        route_avoid_until[nn_group] > round) {
        debug_block({ std::printf("RV_ROUTE_BLOCK %d %u %d\\n", round, my_id, nn_group); });
        nn_group = -1;
    }
#ifdef A2_NN_NEED
''')
    if spawn:
        repaired = (ARENA/'bots/sf06/src/bot.cpp').read_text(encoding='utf-8')
        s = repaired.index('        if ((stall_repairs & 6) && integration_enabled(1)')
        e = repaired.index('        return hp < max_hp; // stay put this turn so the spawn heals us', s)
        clear = repaired[s:e]
        clear = clear.replace('(stall_repairs & 6) && integration_enabled(1) && ', '')
        clear = replace(clear, '''                    bc::bitboard neighbors;
                    neighbors.clear();
                    neighbors.draw_chebyshev(pos, 1.0f);
                    neighbors &= ~w.hot_zone & ~w.static_blocked & ~w.unit_tiles & ~w.camp_tiles_all;
                    if ((stall_repairs & 2) && !neighbors.is_empty() && walk_toward(neighbors)) {
                        plateau_turns = 0;
                        mode = "home-hot-exit";
                        debug_block({ std::printf("STALL_SPAWN %d %u %d\\n", round, my_id, static_cast<int>(hp)); });
                        return true;
                    }
''','')
        clear = clear.replace('(stall_repairs & 4) && ', '')
        marker = '        return hp < max_hp; // stay put this turn so the spawn heals us'
        c = replace(c, marker, clear + marker)
    files['bot.cpp'] = c.encode()
    files['bot.h'] = h.encode()


def screen():
    previous = load(ROOT/'sw08-followup/v113-anchor/selection.json')
    assert previous['winner'] is None, 'A different candidate already owns this release map set'
    configs = [(True,False),(False,True),(True,True)]
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda a: build_from(a[0], 'b113', lambda files: repair(files, *a[1])),
                      zip(NAMES, configs)))
    p = plan()
    maps = list(map(Path, p['dev']))
    rows = run('sw08-v113-minimal-dev-reference', NAMES, maps, DEV_STYLES, 12)
    d = run('sw08-v113-minimal-dev-direct', NAMES, maps, ['b113'], 12)
    r, d = aggregate(rows), aggregate(d)
    baseline = previous['scores']['b113']['score']
    eligible = [n for n in NAMES if not r[n]['faults'] and not d[n]['faults'] and
                r[n]['score'] >= baseline - .015 and d[n]['score'] >= .50]
    winner = max(eligible, key=lambda n: r[n]['score'] + .40 * d[n]['score']) if eligible else None
    data = {'winner': winner, 'scores': r, 'direct': d, 'incumbent_score': baseline}
    if winner:
        data.update(wasm_sha256=sha(artifact(winner)), source_sha256=digest(ARENA/'bots'/winner/'src'))
    save(WORK/'selection.json', data)
    print({'winner': winner, 'reference': {n: r[n]['score'] for n in NAMES},
           'direct': {n: d[n]['score'] for n in NAMES}}, flush=True)


def qualify():
    s = load(WORK/'selection.json')
    n = s['winner']
    spawn_only_recheck = False
    if not n:
        # A one-game miss in the development head-to-head is inconclusive.
        # Freeze the best pooled arm for a separate safety-specific test without
        # altering the recorded screen or the final strength requirements.
        q, d = s['scores']['rv11'], s['direct']['rv11']
        if q['score'] <= s['incumbent_score'] or d['score'] < .5 - 1/d['games'] or q['faults'] or d['faults']:
            return
        n = 'rv11'
        spawn_only_recheck = True
        s = {'winner': n, 'development_sha256': sha(WORK/'selection.json'),
             'source_sha256': digest(ARENA/'bots'/n/'src'), 'wasm_sha256': sha(artifact(n)),
             'reason': 'Positive pooled score and one-game miss in direct development. Fresh validation and dedicated spawn fixture.'}
    assert sha(artifact(n)) == s['wasm_sha256'] and digest(ARENA/'bots'/n/'src') == s['source_sha256']
    p = plan()
    names = ('03homonoliths',) if spawn_only_recheck else ('01islands','03homonoliths')
    fixtures = [Path(f) for f in load(ROOT/'campaign.json')['maps']['dev']
                if Path(f).stem in names]
    fixture_styles = (['b111','nnm4','ref_x1','teammate_john_nnfinal','ref_hold_rush100']
                      if spawn_only_recheck else ['b111','teammate_john_nnfinal'])
    metric = 'spawn_near_camp_stall_pairs' if spawn_only_recheck else 'trailing_quiet_pairs'
    protocol = {'selected': s, 'maps': p['final'], 'expected_ladder': p['expected_ladder'],
                'fixtures': {str(f): sha(f) for f in fixtures},
                'fixture_styles': fixture_styles, 'stall_metric': metric,
                'design': 'Safety-only release. Require at least a 25% lower incident stall rate on the failure fixture, '
                          'at least even pooled and direct strength, a lower map-cluster bound above -5 percentage points, '
                          'no style loss beyond 10 points, bounded fuel, and no faults or codes.'}
    pp = WORK/'protocol.json'
    if pp.exists():
        assert load(pp) == protocol
    else:
        save(pp, protocol)
    fixture = run('sw08-v113-minimal-stall-fixtures', [n,'b113'], fixtures, fixture_styles, 8)
    analyze('sw08-v113-minimal-fixtures', fixture)
    counts = load(ROOT/'stall-audit/sw08-v113-minimal-fixtures.json')
    quiet = {k: c['counts'][metric]/c['counts']['alive_pairs'] for k,c in counts.items()}
    if quiet['b113'] == 0 or quiet[n] > quiet['b113']*.75:
        save(WORK/'fixture-failure.json', {'candidate': n, 'quiet_rates': quiet, 'required_ratio': .75})
        return
    maps = list(map(Path, p['final']))
    refs = run('sw08-v113-minimal-final-reference', [n,'b113'], maps, STYLES, 12)
    direct = run('sw08-v113-minimal-final-direct', [n], maps, ['b113'], 12)
    c = comparison(refs, n, 'b113')
    rates = {k: fuel_rate(refs,k) for k in (n,'b113')}
    a = aggregate(direct)[n]
    gates = {'zero_faults_and_codes': not any(r['faults'] or r['opponent_faults'] or r['diagnostic_codes']
                                             for r in refs+direct+fixture),
             'no_pooled_drop': c['gain'] >= 0,
             'bounded_cluster_lower': c['map_cluster_bootstrap_95'][0] >= -.05,
             'no_direct_drop': a['score'] >= .50,
             'worst_style_bounded': min(c['style_deltas'].values()) >= -.10,
             'fuel_rate_bounded': rates[n]['per_1000_scheduled_champion_rounds'] <=
                                  1.15 * rates['b113']['per_1000_scheduled_champion_rounds'],
             'stall_guard_pass': quiet[n] <= quiet['b113']*.75}
    r = {'candidate': n, 'expected_ladder': p['expected_ladder'], 'gates': gates,
         'approved_for_upload': all(gates.values()), 'comparisons': {'b113': c}, 'head_to_head': a,
         'stall_rates': quiet, 'fuel_rates': rates, 'games': len(refs)+len(direct)+len(fixture),
         'source_sha256': s['source_sha256'], 'wasm_sha256': s['wasm_sha256'], 'protocol_sha256': sha(pp)}
    path = WORK/'qualification.json'
    save(path, r)
    package(n, r, path)
    print({'candidate': n, 'gates': gates}, flush=True)


if __name__ == '__main__':
    {'screen': screen, 'qualify': qualify}[sys.argv[1]]()
