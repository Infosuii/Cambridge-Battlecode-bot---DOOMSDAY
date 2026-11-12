"""Reproduce sw08's regression and freeze independently tested follow-up arms."""
import concurrent.futures
import json
from pathlib import Path
import sys

from local_panel import run
from policy_rows import stdout
from project import ARENA, ROOT, build, digest, save, sha

WORK = ROOT / 'sw08-followup'
PARENT = 'sw08'
STYLES = ['b111', 'nnm4', 'v92', 'ref_x1', 'ref_hold_rush100', 'teammate_john_nnfinal']


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def replace(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new)


def build_from(name, parent, edit, debug=False):
    root = ARENA / 'bots' / parent / 'src'
    files = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
    edit(files)
    out = ARENA / 'bots' / name / 'src'
    if out.exists():
        assert {p.name: p.read_bytes() for p in out.iterdir() if p.is_file()} == files
    else:
        out.mkdir(parents=True)
        for filename, data in files.items():
            (out / filename).write_bytes(data)
    wasm = build(name, debug=debug)
    save(out.parent / 'followup-build.json', {'parent': parent, 'source': digest(out), 'wasm': sha(wasm)})


def trace(files):
    c = files['bot.cpp'].decode()
    key = '    // The planner chose a bank trip first (APEX_PLAN).'
    c = replace(c, key, '''    debug_block({
        const int old = target_group;
        const int dist = best >= 0 && w.has_field(best) ? w.group_distance(best, pos) : -1;
        std::printf("SWSEL %d %u %d %d %d %d %d %d %d %d %d\\n", round, my_id, old, best, nn_group,
            best_need, dist, gems, static_cast<int>(hp), static_cast<int>(w.enemies.size()),
            best >= 0 ? avoid_until[best] - round : 0);
    });
''' + key)
    files['bot.cpp'] = c.encode()


def diagnosis():
    names = {'swtrace0': 'mx500', 'swtrace1': PARENT}
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda n: build_from(n, names[n], trace, True), names))
    old = load(ROOT / 'panels/stall-sealed-reference/results.json')
    flips = load(ROOT / 'stall-audit/sealed-v111-outcome-flips.json')
    cases = [(r['map_sha256'], r['side']) for r in flips if r['candidate_score'] == 0][:10]
    pinned = {(r['map_sha256'], r['side']): r for r in old
              if r['candidate'] == PARENT and r['opponent'] == 'b111'}
    cells = [(n, 'b111', pinned[k]['map_file'], k[1]) for n in names for k in cases]
    maps = list(dict.fromkeys(Path(c[2]) for c in cells))
    rows = run('sw08-divergence-trace', list(names), maps, ['b111'], 8, True, schedule=cells)
    index = {(r['candidate'], r['map_sha256'], r['side']): r for r in rows}
    original = {(r['candidate'], r['map_sha256'], r['side']): r for r in old if r['opponent'] == 'b111'}
    reports = []
    for k in cases:
        A, B = [index[n, *k] for n in names]
        streams = [stdout(r['replay_bundle'], r['side']).splitlines() for r in (A, B)]
        sels = []
        for stream in streams:
            sels.append({tuple(map(int, p[1:3])): list(map(int, p[3:])) for line in stream
                         if (p := line.split()) and p[0] == 'SWSEL'})
        keys = sorted(sels[0].keys() & sels[1].keys())
        first = next((i for i in keys if sels[0][i] != sels[1][i]), None)
        events = [(p[0], *map(int, p[1:])) for line in streams[1] if (p := line.split())
                  and p[0] in ('STALL_AVOID', 'STALL_CLEAR', 'WAIT_FALLBACK') and p[0] != 'WAIT_FALLBACK']
        reports.append({'map': A['map'], 'side': A['side'], 'outcomes': [A['score'], B['score']],
                        'reproduced': [r['score'] == original[names[r['candidate']], *k]['score'] for r in (A, B)],
                        'first_shared_different_decision': {'round_and_champion': first,
                            'parent': sels[0].get(first), 'sw08': sels[1].get(first)},
                        'first_interventions': sorted(events, key=lambda e: e[1])[:8],
                        'intervention_counts': {t: sum(e[0] == t for e in events) for t in ('STALL_AVOID', 'STALL_CLEAR')}})
    save(WORK / 'divergences.json', reports)
    print(json.dumps(reports, separators=(',', ':')), flush=True)


def legality(files):
    files['common.h'] = b'#define SW_LEGAL_TARGETS 1\n' + files['common.h']
    h = files['bot.h'].decode()
    declaration = '    int nn_ens_sample(int v92g);'
    assert h.count(declaration) == 1
    files['bot.h'] = h.replace(declaration,
        '    bool nn_target_allowed(int group, int observed_state) const;\n' + declaration).encode()
    c = files['nnrec.cpp'].decode()
    marker = 'static NNPub nn_pub;'
    c = replace(c, marker, marker + '''
bool Bot::nn_target_allowed(int group, int observed_state) const {
    if (group < 0 || static_cast<std::size_t>(group) >= w.groups.size()) return false;
    if (static_cast<std::size_t>(group) < avoid_until.size() && avoid_until[group] > round) return false;
    return w.groups[group].state != GroupState::respawning ||
           observed_state == static_cast<int>(GroupState::respawning);
}
''')
    search = 'r < 4 && nn_pub.rank[r] >= 0; ++r) {'
    assert c.count(search) == 4
    c = c.replace(search, search + '''
        if (!nn_target_allowed(nn_pub.rank[r], nn_pub.st[r])) continue;''')
    old = '''        for (int i = 0; i < kC; ++i)
            if (sample_features[kCOffL + i * kCF] == 1 && sample_features[kCOffL + i * kCF + 1] == v92g) bs = i;'''
    c = replace(c, old, '''        for (int i = 0; i < kC; ++i) {
            const auto* slot_features = sample_features + kCOffL + i * kCF;
            if (slot_features[0] != 1 ||
                (slot_features[1] != v92g && !nn_target_allowed(slot_features[1], slot_features[7]))) {
                v[i] = -2e9f;
                continue;
            }
            if (slot_features[1] == v92g) bs = i;
        }''')
    files['nnrec.cpp'] = c.encode()


def paths(files):
    c = files['bot.cpp'].decode()
    old = '''            int d = 1 << 20;
            for (int ci : g.camps) d = std::min(d, cheb(w.camps[ci].pos, pos));'''
    c = replace(c, old, '''            int d = w.has_field(gi) ? w.group_distance(gi, pos) : kUnreach;
            if (d == kUnreach) {
                d = 1 << 20;
                for (int ci : g.camps) d = std::min(d, cheb(w.camps[ci].pos, pos));
            }''')
    old = '''        if (!walk_toward(goal) && !bit(goal, pos)) {
            if (walk_unreachable) {
                // No attack position is reachable over static terrain: drop the group (see to-capture).'''
    new = '''        if (!walk_toward(goal) && !bit(goal, pos)) {
            if (walk_unreachable && !melee && !bit(attack_zone, pos) &&
                bc::fuel_remaining() > 24000) {
                // A preferred full-range ring can sit across a wall even when
                // a closer firing tile is reachable. Try the complete zone.
                if (walk_toward(attack_zone)) {
                    debug_block({ std::printf("SW_RING %d %u\\n", round, my_id); });
                }
            }
            if (walk_unreachable) {
                // No attack position is reachable over static terrain: drop the group (see to-capture).'''
    c = replace(c, old, new)
    c = replace(c, '''            if (break_out()) return true;
        }
        if (!melee) {''', '''            if (!walked && break_out()) return true;
        }
        if (!melee) {''')
    files['bot.cpp'] = c.encode()


def combined(files):
    legality(files)
    paths(files)


def capture_handoff(files):
    legality(files)
    h = files['bot.h'].decode()
    marker = '    std::vector<int> avoid_until;'
    h = replace(h, marker, '    std::vector<int> ally_yield_until; // short capture handoff deadline\n' + marker)
    files['bot.h'] = h.encode()
    c = files['bot.cpp'].decode()
    marker = '    if (avoid_until.size() != w.groups.size()) avoid_until.assign(w.groups.size(), 0);'
    c = replace(c, marker, marker + '''
    if (ally_yield_until.size() != w.groups.size()) ally_yield_until.assign(w.groups.size(), 0);''')
    for n in (6, 3, 4):
        old = f'avoid_until[gi] = round + {n};'
        c = replace(c, old, f'avoid_until[gi] = ally_yield_until[gi] = round + {n};')
    c = replace(c, 'avoid_until[best] = round + 8;',
                'avoid_until[best] = ally_yield_until[best] = round + 8;')
    c = replace(c, '''        avoid_until[nn_group] > round) {''',
                '''        !nn_target_allowed(nn_group, static_cast<int>(w.groups[nn_group].state))) {''')
    files['bot.cpp'] = c.encode()
    c = files['nnrec.cpp'].decode()
    old = '    if (static_cast<std::size_t>(group) < avoid_until.size() && avoid_until[group] > round) return false;'
    c = replace(c, old, '''    if (static_cast<std::size_t>(group) < avoid_until.size() && avoid_until[group] > round) {
        if (static_cast<std::size_t>(group) >= ally_yield_until.size() ||
            ally_yield_until[group] != avoid_until[group]) return false;
        const auto& g = w.groups[group];
        if (g.state == GroupState::reward && (group_capture_covered(g) ||
            (tune::kShareGold && w.enemies.empty() && poorer_ally_takes(g, group, false)))) return false;
        debug_block({ std::printf("SW_HANDOFF_READY %d %u %d\\n", round, my_id, group); });
    }''')
    files['nnrec.cpp'] = c.encode()


def handoff_and_paths(files):
    capture_handoff(files)
    paths(files)


def handoff_preference(files, keep_nearby):
    capture_handoff(files)
    c = files['nnrec.cpp'].decode()
    old = '''        if (g.state == GroupState::reward && (group_capture_covered(g) ||
            (tune::kShareGold && w.enemies.empty() && poorer_ally_takes(g, group, false)))) return false;'''
    if keep_nearby:
        c = replace(c, old, '''        const bool nearby = group == target_group ||
            (w.has_field(group) && w.group_distance(group, pos) <= 2);
        if (!nearby && g.state == GroupState::reward && (group_capture_covered(g) ||
            (tune::kShareGold && w.enemies.empty() && poorer_ally_takes(g, group, false)))) return false;''')
    else:
        c = replace(c, '        const auto& g = w.groups[group];\n' + old,
                    '        // A short ally preference is handled by the capture ownership logic.')
    files['nnrec.cpp'] = c.encode()


def freeze_plan():
    original = load(ROOT / 'campaign.json')
    old_sealed = load(ROOT / 'qualification-stall/protocol.json')
    maps = sorted((ARENA / 'maps_sw08_followup').glob('*.map26a'))
    assert len(maps) == 128
    extra = {str(p): sha(p) for p in maps}
    exposed = {h for role in original['maps'].values() for h in role.values()} | set(old_sealed['maps'].values())
    assert len(set(extra.values())) == 128 and not set(extra.values()) & exposed
    # Generator interleaves families. Each split sees all five families.
    splits = {'train': {str(p): extra[str(p)] for p in maps[:64]},
              'dev': {str(p): extra[str(p)] for p in maps[64:88]},
              'final': {str(p): extra[str(p)] for p in maps[88:]}}
    data = {'maps': splits, 'styles': STYLES, 'opponents': ['b113', 'b114'],
            'initial_checkpoint': str(ROOT / 'training/q15-model-selection/mx500.pt'),
            'checkpoint_sha256': sha(ROOT / 'training/q15-model-selection/mx500.pt'),
            'generator_manifest_sha256': sha(ARENA / 'maps_sw08_followup/manifest.json')}
    path = WORK / 'plan.json'
    if path.exists():
        assert load(path) == data
    else:
        save(path, data)
    return data


def screen():
    plan = freeze_plan()
    arms = {'sf01': legality, 'sf02': paths, 'sf03': combined}
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda n: build_from(n, PARENT, arms[n]), arms))
    styles = ['b111', 'nnm4', 'ref_hold_rush100']
    maps = [Path(p) for p in plan['maps']['dev']]
    rows = run('sw08-followup-mechanisms', [PARENT, *arms], maps, styles, 12)
    from retune_campaign import aggregate
    data = aggregate(rows)
    save(WORK / 'mechanisms.json', data)
    print(json.dumps(data), flush=True)


def handoff_screen():
    plan = freeze_plan()
    arms = {'sf04': capture_handoff, 'sf05': handoff_and_paths}
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda n: build_from(n, PARENT, arms[n]), arms))
    styles = ['b111', 'nnm4', 'ref_hold_rush100']
    maps = [Path(p) for p in plan['maps']['dev']]
    rows = run('sw08-followup-handoff', list(arms), maps, styles, 10)
    from retune_campaign import aggregate
    data = aggregate(rows)
    save(WORK / 'handoff.json', data)
    print(json.dumps(data), flush=True)


def handoff_retry():
    plan = freeze_plan()
    arms = {'sf06': lambda f: handoff_preference(f, False), 'sf07': lambda f: handoff_preference(f, True)}
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        list(pool.map(lambda n: build_from(n, PARENT, arms[n]), arms))
    maps = [Path(p) for p in plan['maps']['dev']]
    rows = run('sw08-followup-handoff-retry', list(arms), maps, STYLES, 8)
    from retune_campaign import aggregate
    save(WORK / 'handoff-retry.json', aggregate(rows))


def training_parent():
    plan = freeze_plan()
    observed = {**load(WORK / 'mechanisms.json'), **load(WORK / 'handoff.json')}
    base = observed[PARENT]
    names = ['sf01', 'sf03', 'sf04', 'sf05']
    viable = [n for n in names if observed[n]['faults'] == 0 and observed[n]['fuel'] <= base['fuel'] * 1.15]
    assert viable
    # Reserve the release panel. On the diagnostic panel, value recovering the
    # demonstrated v111 weakness alongside the pooled score and fault budget.
    def score(n):
        return observed[n]['score'] + .35 * observed[n]['opponents']['b111']
    best = max(viable, key=score)
    parent = next((n for n in ('sf04', 'sf05') if n in viable and score(n) >= score(best) - .015), best)
    mix = ['b111', 'b113', 'nnm4', 'b111', 'b114', 'v92',
           'ref_x1', 'b111', 'ref_hold_rush100', 'teammate_john_nnfinal']
    save(WORK / 'training-plan.json', {**plan, 'train_styles': mix})
    save(WORK / 'training-parent.json', {'parent': parent, 'source_sha256': digest(ARENA/'bots'/parent/'src'),
        'scores': observed, 'selection': 'Development pooled score plus 0.35 times b111 score; prefer the handoff repair within 1.5 points.'})
    print(parent, flush=True)


if __name__ == '__main__':
    {'diagnose': diagnosis, 'screen': screen, 'handoff': handoff_screen,
     'handoff-retry': handoff_retry, 'training-parent': training_parent}[sys.argv[1]]()
