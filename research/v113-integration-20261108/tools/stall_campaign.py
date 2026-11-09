"""Compare repair variants on pinned development matches and replay audits."""
import concurrent.futures as cf
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from local_panel import run
from policy_rows import stdout
from project import ARENA, ROOT, build, digest, save, sha

WD = ROOT / 'stall-audit'
REFS = ['b111', 'nnm4', 'ref_x1', 'teammate_john_nnfinal']
PARENT = 'mx500'
FIX = 'sw01'
OLD = '''            const int altar_trip = gems >= 10 && w.ensure_altar_field()
                ? 2 * static_cast<int>(fdist(w.altar_field, pos)) + (gems + 9) / 10 : 0;
            const int home_trip = std::min(2 * static_cast<int>(fdist(w.spawn_field, pos)), 12);
            if (gems >= 10 && wait > altar_trip + 2) {
                force_tribute = true;
                return tribute_if_needed();
            }
            if (gold >= 90 && !shop_done && wait > home_trip + 4 && type != bc::champion_type::tavi) {
                heading_home = true;
                return go_home_if_needed();
            }'''
NEW = '''            const int altar_dist = gems >= 10 && w.ensure_altar_field() ? fdist(w.altar_field, pos) : kUnreach;
            const int altar_trip = 2 * altar_dist + (gems + 9) / 10;
            const int home_trip = std::min(2 * static_cast<int>(fdist(w.spawn_field, pos)), 12);
            if (altar_dist != kUnreach && wait > altar_trip + 2) {
                const bool previous_intent = force_tribute;
                force_tribute = true;
                if (tribute_if_needed()) return true;
                force_tribute = previous_intent;
                debug_block({ std::printf("WAIT_FALLBACK %d %u bank %d\\n", round, my_id, wait); });
            }
            if (gold >= 90 && !shop_done && wait > home_trip + 4 && type != bc::champion_type::tavi) {
                const bool previous_intent = heading_home;
                heading_home = true;
                if (go_home_if_needed()) return true;
                heading_home = previous_intent && !bit(w.ally_spawn, pos);
                debug_block({ std::printf("WAIT_FALLBACK %d %u home %d\\n", round, my_id, wait); });
            }
            mode = "wait-respawn";'''


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def make(name=FIX, replacement=NEW, mask=0, parent=PARENT, integration_mask=15):
    source = ARENA / 'bots' / parent / 'src'
    dest = ARENA / 'bots' / name / 'src'
    original = (source / 'bot.cpp').read_text(encoding='utf-8')
    assert original.count(OLD) == 1
    candidate = original.replace(OLD, replacement)
    if mask:
        key = '#include "a2map.h"'
        assert candidate.count(key) == 1
        candidate = candidate.replace(key, key + f'\nstatic volatile int stall_repairs = {mask};')
        key = '#ifdef A2_NN_NEED\n    // E126: an override keeps'
        assert candidate.count(key) == 1
        candidate = candidate.replace(key, '''    if ((stall_repairs & 1) && nn_group >= 0 && nn_group < static_cast<int>(avoid_until.size()) &&
        avoid_until[nn_group] > round) {
        debug_block({ std::printf("STALL_AVOID %d %u %d %d\\n", round, my_id, nn_group, avoid_until[nn_group] - round); });
        nn_group = -1;
    }
''' + key)
        key = '        return hp < max_hp; // stay put this turn so the spawn heals us'
        assert candidate.count(key) == 1
        candidate = candidate.replace(key, '''        if ((stall_repairs & 2) && integration_enabled(1) && bit(w.hot_zone, pos) &&
            hp >= max_hp * 0.40f && hp < max_hp * 0.85f) {
            static int plateau_turns = 0, plateau_round = -2;
            static vec2 plateau_pos{-1, -1};
            if (round != plateau_round) {
                plateau_turns = round == plateau_round + 1 && pos == plateau_pos && hp <= prev_hp + 1.0f
                    ? plateau_turns + 1 : 0;
                plateau_round = round;
                plateau_pos = pos;
            }
            if (plateau_turns >= 6 && me.can_move() && !walked && bc::fuel_remaining() > 18000) {
                bool threat = false;
                for (const auto& e : w.enemies) threat |= cheb(e.pos, pos) <= 8;
                for (const auto& s : w.sightings) threat |= round - s.round <= 5 && cheb(s.pos, pos) <= 8;
                if (!threat) {
                    bc::bitboard neighbors;
                    neighbors.clear();
                    neighbors.draw_chebyshev(pos, 1.0f);
                    neighbors &= ~w.hot_zone & ~w.static_blocked & ~w.unit_tiles & ~w.camp_tiles_all;
                    if (!neighbors.is_empty() && walk_toward(neighbors)) {
                        plateau_turns = 0;
                        mode = "home-hot-exit";
                        debug_block({ std::printf("STALL_SPAWN %d %u %d\\n", round, my_id, static_cast<int>(hp)); });
                        return true;
                    }
                }
            }
        }
''' + key)
        if mask & 4:
            candidate = candidate.replace('(stall_repairs & 2) && integration_enabled(1)',
                                          '(stall_repairs & 6) && integration_enabled(1)')
            key = 'if (!neighbors.is_empty() && walk_toward(neighbors))'
            assert candidate.count(key) == 1
            candidate = candidate.replace(key, 'if ((stall_repairs & 2) && !neighbors.is_empty() && walk_toward(neighbors))')
            key = '''                        return true;
                    }
                }
            }
        }
        return hp < max_hp;'''
            assert candidate.count(key) == 1
            candidate = candidate.replace(key, key.replace('                    }\n                }', '''                    }
                    // No adjacent safe tile: use the spawn heal while clearing
                    // a visible camp that can hit us from its current tile.
                    int target = -1;
                    float best = -1.0f;
                    if ((stall_repairs & 4) && bc::fuel_remaining() > 18000)
                        for (std::size_t i = 0; i < w.camps.size(); ++i) {
                            const auto& c = w.camps[i];
                            if (c.dead || c.strength <= 0 || cheb(pos, c.pos) > c.range ||
                                !bit(w.visible, c.pos)) continue;
                            const int d = cheb(pos, c.pos);
                            bool usable = d <= range;
                            for (int s = 0; s < 2; ++s)
                                usable |= spells[s].camps && d <= spells[s].range && spell_ready(s);
                            const float priority = c.strength / std::max(1.0f, c.hp);
                            if (usable && priority > best) target = static_cast<int>(i), best = priority;
                        }
                    if (target >= 0 && (attack_unit(w.camps[target].camp, w.camps[target].pos) || cast_on_camp(target))) {
                        mode = "home-hot-clear";
                        debug_block({ std::printf("STALL_CLEAR %d %u %d\\n", round, my_id, target); });
                        return true;
                    }
                }''', 1))
    if not dest.exists():
        shutil.copytree(source, dest)
        (dest / 'bot.cpp').write_text(candidate, encoding='utf-8', newline='\n')
        p = dest / 'integration.h'
        c = p.read_text(encoding='utf-8')
        assert c.count('{15, 1}') == 1
        p.write_text(c.replace('{15, 1}', f'{{{integration_mask}, 1}}'), encoding='utf-8', newline='\n')
    assert (dest / 'bot.cpp').read_text(encoding='utf-8') == candidate
    wasm = build(name)
    save(WD / f'{name}-build.json', {'parent': parent, 'integration_mask': integration_mask,
        'stall_mask': mask, 'source_sha256': digest(dest), 'wasm_sha256': sha(wasm)})


def decode(row):
    d = WD / 'local' / Path(row['summary']).parent.name
    d.mkdir(parents=True, exist_ok=True)
    source = Path(row['replay_bundle'])
    assert sha(source) == row['replay_sha256']
    raw = d / 'native.repl26a'
    with zipfile.ZipFile(source) as z:
        data = z.read('replay.repl26a')
    raw.write_bytes(data)
    spec = {'match': d.name, 'map': row['map'], 'version': row['candidate'],
            'side': int(row['side'] == 'b'), 'replay': str(raw), 'summary': row['summary'],
            'sha256': hashlib.sha256(data).hexdigest(), 'summary_sha256': row['summary_sha256']}
    specfile, report = d / 'spec.json', d / 'report.json'
    save(specfile, spec)
    subprocess.run(['node', '--no-warnings', str(ROOT / 'stall_replay.mjs'), str(specfile), str(report)], check=True, timeout=150)
    # Keep original replay bundles and the derived reports, without a second raw copy.
    raw.unlink()
    return {'opponent': row['opponent'], 'map_sha256': row['map_sha256'], **read(report)}


def analyze(label, rows):
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        reports = list(pool.map(decode, rows))
    result = {}
    for name in sorted({r['version'] for r in reports}):
        found = [r for r in reports if r['version'] == name]
        counts = {k: sum(r['counts'][k] for r in found) for k in found[0]['counts']}
        episodes = [{**s, 'match': r['match'], 'map': r['map'], 'opponent': r['opponent'], 'side': r['side']}
                    for r in found for s in r['stalls']]
        quiet = [s for s in episodes if s['trailing_rounds'] * 2 >= s['end'] - s['start']
                 and s['enemy_near_rounds'] == 0]
        counts['trailing_quiet_pairs'] = sum(s['end'] - s['start'] for s in quiet)
        counts['games'] = len(found)
        result[name] = {'counts': counts, 'fuel_events': sum(r['fuel_events'] for r in found),
                        'worst': sorted(episodes, key=lambda s: s['end']-s['start'], reverse=True)[:10],
                        'worst_trailing_quiet': sorted(quiet, key=lambda s: s['end']-s['start'], reverse=True)[:10]}
    save(WD / (label + '.json'), result)
    print(json.dumps({k: v['counts'] for k, v in result.items()}), flush=True)


def comparison():
    a = read(ROOT / 'panels/native-weight-damping/results.json')
    b = read(ROOT / 'panels/teammate-feature-development-supplement/results.json')
    rows = [r for r in a+b if r['candidate'] in (PARENT, 'b114') and r['opponent'] in (REFS[0], REFS[-1])
            and 'maps_generated' not in r['map_file']]
    keys = lambda n: {(r['opponent'], r['map_sha256'], r['side']) for r in rows if r['candidate'] == n}
    assert keys(PARENT) == keys('b114') and len(rows) == 2 * len(keys(PARENT))
    analyze('incumbent-comparison', rows)


def repair():
    make()
    cfg = read(ROOT / 'campaign.json')
    maps = list(map(Path, cfg['maps']['dev']))
    rows = run('stall-fallthrough-development', [PARENT, FIX], maps, cfg['styles'], 12)
    audit = [r for r in rows if r['opponent'] in (REFS[0], REFS[-1]) and 'maps_generated' not in r['map_file']]
    analyze('fallthrough-development', audit)


def trace(targeted=False, clear=False):
    cfg = read(ROOT / 'campaign.json')
    preferred = ('01islands', '03homonoliths', '00ambush', '01big_world', '00stampede')
    maps = [Path(p) for p in cfg['maps']['dev'] if Path(p).stem in preferred]
    assert any(m.stem == '01islands' for m in maps)
    parents = ('sw08', 'sw09') if clear else ('sw02', 'sw03', 'sw04') if targeted else (PARENT, FIX)
    bots = ['stdebug8', 'stdebug9'] if clear else ['stdebug' + str(i) for i in range(2, 5)] if targeted else ['stdebug0', 'stdebug1']
    for parent, name in zip(parents, bots):
        source = ARENA / 'bots' / parent / 'src'
        dest = ARENA / 'bots' / name / 'src'
        if not dest.exists():
            shutil.copytree(source, dest)
            p = dest / 'bot.cpp'
            c = p.read_text(encoding='utf-8')
            key = '    PROF_CHECK("decide");'
            assert c.count(key) == 1
            p.write_text(c.replace(key, key + '''
    debug_block({
        if (!walked && !cast_done && me.can_move()) {
            const bool valid = target_group >= 0 && target_group < static_cast<int>(w.groups.size());
            const int state = valid ? static_cast<int>(w.groups[target_group].state) : -1;
            const int wait = valid ? w.groups[target_group].respawn_round - round : -1;
            std::printf("STTRACE %d %u %s %d %d %d %d %d %d %d %d %d %llu\\n",
                round, my_id, mode, target_group, state, wait, pos.x, pos.y, gems, gold,
                static_cast<int>(w.enemies.size()), avoid_until.empty() || !valid ? 0 : avoid_until[target_group] - round,
                static_cast<unsigned long long>(bc::fuel_remaining()));
        }
    });
'''), encoding='utf-8', newline='\n')
        build(name, debug=True)
    label = 'stall-clear-trace' if clear else 'stall-targeted-trace' if targeted else 'stall-mechanism-trace'
    rows = run(label, bots, maps, [REFS[0], REFS[-1]], 8, debug=True)
    episodes = []
    activations = []
    for r in rows:
        report = decode(r)
        by = {}
        fallback = []
        for line in stdout(r['replay_bundle'], r['side']).splitlines():
            f = line.split()
            if f and f[0] == 'STTRACE' and len(f) == 14:
                by[int(f[2]), int(f[1])] = f[3:]
            if f and f[0] == 'WAIT_FALLBACK':
                fallback.append(f[1:])
            if f and f[0] in ('STALL_AVOID', 'STALL_SPAWN', 'STALL_CLEAR'):
                activations.append({'candidate': r['candidate'], 'map': r['map'], 'opponent': r['opponent'],
                                    'side': r['side'], 'event': f[0], 'detail': f[1:]})
        for s in report['stalls']:
            trace_rows = [by[s['id'], t] for t in range(s['start'], s['end']) if (s['id'], t) in by]
            modes = {}
            for tr in trace_rows:
                tag = ' '.join(tr[:3])
                modes[tag] = modes.get(tag, 0) + 1
            episodes.append({'candidate': r['candidate'], 'map': r['map'], 'opponent': r['opponent'],
                'side': r['side'], 'mode_counts': modes, 'trace_start': trace_rows[:2],
                'trace_end': trace_rows[-2:], 'fallback_events_game': len(fallback), **s})
    episodes.sort(key=lambda s: s['end']-s['start'], reverse=True)
    save(WD / ('clear-mode-episodes.json' if clear else 'targeted-mode-episodes.json' if targeted else 'mode-episodes.json'), episodes)
    if targeted:
        save(WD / ('clear-activations.json' if clear else 'targeted-activations.json'), activations)
    print(json.dumps([{k: s[k] for k in ('map','candidate','start','end','mode_counts','fallback_events_game')}
                      for s in episodes[:12]]), flush=True)


def targeted():
    arms = {'sw02': 1, 'sw03': 2, 'sw04': 3}
    with cf.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda p: make(p[0], mask=p[1]), arms.items()))
    cfg = read(ROOT / 'campaign.json')
    maps = list(map(Path, cfg['maps']['dev']))
    styles = cfg['styles']
    old = read(ROOT / 'panels/stall-fallthrough-development/results.json')
    rows = run('stall-targeted-development', list(arms), maps, styles, 12)
    audit = [r for r in rows + old if r['opponent'] in (REFS[0], REFS[-1]) and 'maps_generated' not in r['map_file']]
    analyze('targeted-development', audit)


def reference_repair():
    # Original v113 weights test whether the verified safety changes need the
    # trained blend; compare shorter banking shortcuts as a separate feature.
    arms = [('sw05', 'qs000', 15), ('sw06', 'qs000', 13), ('sw07', PARENT, 13)]
    with cf.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda a: make(a[0], mask=3, parent=a[1], integration_mask=a[2]), arms))
    cfg = read(ROOT / 'campaign.json')
    maps = list(map(Path, cfg['maps']['dev']))
    rows = run('stall-reference-development', [a[0] for a in arms], maps, cfg['styles'], 12)
    audit = [r for r in rows if r['opponent'] in (REFS[0], REFS[-1]) and 'maps_generated' not in r['map_file']]
    analyze('reference-development', audit)


def clear_repair():
    arms = {'sw08': 5, 'sw09': 7}
    with cf.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda a: make(a[0], mask=a[1]), arms.items()))
    cfg = read(ROOT / 'campaign.json')
    maps = list(map(Path, cfg['maps']['dev']))
    rows = run('stall-clear-development', list(arms), maps, cfg['styles'], 12)
    audit = [r for r in rows if r['opponent'] in (REFS[0], REFS[-1]) and 'maps_generated' not in r['map_file']]
    analyze('clear-development', audit)


if __name__ == '__main__':
    {'compare': comparison, 'repair': repair, 'trace': trace, 'targeted': targeted,
     'targeted-trace': lambda: trace(True), 'reference': reference_repair,
     'clear': clear_repair, 'clear-trace': lambda: trace(True, True)}[sys.argv[1]]()
