"""Homonoliths objective trace: debug-only printf (free in debug builds, compiled out in release).

Builds dx01 = hp01 + trace lines; no behavior edits. Runs debug dx01 and release hp01 on 03homonoliths
against local references, then summarises job eligibility of the 600-gem groups and target selection.
"""
from pathlib import Path
import sys, json, collections
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from local_panel import run, read_native
from project import ROOT, save
from sw08_followup import build_from, load, replace
from policy_rows import stdout

GJ = r'''
#define GJ_ON(gi_) (w.groups[gi_].gems >= 300 && round <= 1000 && round % 5 == 0)
#define GJT(why) debug_block({ if (GJ_ON(gi)) std::printf("GJ %d %d %d %d %d %s\n", round, slot, static_cast<int>(gi), static_cast<int>(w.groups[gi].state), dist, why); })
'''


def trace(files):
    c = files['bot.cpp'].decode()
    c = replace(c, '#include "a2stack.h"\n', '#include "a2stack.h"\n' + GJ, ) if c.count('#include "a2stack.h"\n') == 1 else c
    c = replace(c, '            if (best_case <= prune_bound()) {\n',
                '            if (best_case <= prune_bound()) {\n                GJT("prune");\n')
    c = replace(c, '        if (group_capture_covered(g)) {\n', '        if (group_capture_covered(g)) {\n            GJT("covered");\n')
    c = replace(c, '        if (need > team_size) continue;',
                '        if (need > team_size) {\n            debug_block({ if (GJ_ON(gi)) std::printf("GJ %d %d %d %d %d needgt need%d team%d hp_left%.0f claims%d/%d\\n", round, slot, static_cast<int>(gi), static_cast<int>(g.state), dist, need, team_size, hp_left, lower, higher); });\n            continue;\n        }')
    old = 'need > (big ? team_size : UB_JOB_MAX) || lower_call)\n                continue;'
    assert c.count(old) == 1
    c = c.replace(old, 'need > (big ? team_size : UB_JOB_MAX) || lower_call) {\n'
        '                debug_block({ if (GJ_ON(gi)) std::printf("GJ %d %d %d %d %d noinit need%d big%d ni%d ban%d lower_call%d claims%d/%d hint%d\\n", round, slot, static_cast<int>(gi), static_cast<int>(g.state), dist, need, big ? 1 : 0, no_initiate ? 1 : 0, round < call_ban_until ? 1 : 0, lower_call ? 1 : 0, lower, higher, participants_hint); });\n'
        '                continue;\n            }')
    c = replace(c, 'lower >= need + tune::kCapStaff - 1) continue;',
                'lower >= need + tune::kCapStaff - 1) {\n            GJT("capstaff");\n            continue;\n        }')
    c = replace(c, '        if (score > best_score) {\n',
                '        debug_block({ if (GJ_ON(gi)) std::printf("GJ %d %d %d %d %d scored need%d part%d init%d siege%d claims%d/%d hp_left%.0f kill%.0f value%.1f cost%.1f score%.4f best%.4f bestg%d\\n", round, slot, static_cast<int>(gi), static_cast<int>(g.state), dist, need, participants, initiating ? 1 : 0, siege ? 1 : 0, lower, higher, hp_left, kill, value, cost, score, best_score, best); });\n'
                '        if (score > best_score) {\n')
    c = replace(c, '    if (best != target_group) {\n',
                '    debug_block({ if (round <= 1000 && round % 5 == 0) std::printf("SEL %d %d %s %d %d %d %d %d %d %d %d %d %s\\n", round, slot, bc::to_string(type).c_str(), nn_v92best, nn_group, best, best_need, target_group, static_cast<int>(hp), static_cast<int>(max_hp), static_cast<int>(gems), static_cast<int>(w.enemies.size()), mode); });\n'
                '    if (best != target_group) {\n')
    files['bot.cpp'] = c.encode()


def main():
    build_from('dx01', 'hp01', trace, debug=True)
    maps = load(ROOT / 'published-maps.json')
    target = Path(next(row['file'] for row in maps if row['name'] == '03homonoliths'))
    rows = run('v118-homonoliths-trace', ['dx01'], [target], ['ref_x1', 'b111', 'teammate_john_nnfinal'], workers=6, debug=True)
    out = []
    for r in rows:
        txt = stdout(r['replay_bundle'], r['side'])
        gj = collections.Counter(); sel = collections.Counter(); first_scored = {}
        nn_over = collections.Counter(); per_round_targets = collections.defaultdict(list)
        for line in txt.splitlines():
            p = line.split()
            if not p: continue
            if p[0] == 'GJ':
                rnd, slot, gi = int(p[1]), int(p[2]), int(p[3]); why = p[6]
                gj[(gi, why)] += 1
                if why == 'scored' and gi not in first_scored: first_scored[gi] = rnd
            elif p[0] == 'SEL':
                rnd, slot, typ, rule, nn, best, need, tgt = int(p[1]), int(p[2]), p[3], int(p[4]), int(p[5]), int(p[6]), int(p[7]), int(p[8])
                per_round_targets[rnd].append((typ, rule, nn, best, need))
                if nn >= 0 and nn != rule: nn_over[(rule, nn)] += 1
                sel[(best,)] += 1
        n = read_native(r['summary']); ours = 'team' + r['side'].upper()
        caps = sorted((v['timestamp']['round'], e['owner']['team'], v['target']['id'], float(v['value'])) for e in n['events'] if e['kind'] == 'gemCollection'
                      for v in e['entries'] if float(v['value']) and (v.get('target') or {}).get('kind') == 'campGroup')
        out.append({'opponent': r['opponent'], 'side': r['side'], 'score': r['score'], 'rounds': r['rounds'], 'fuel': r['fuel'],
                    'captures': caps[:6], 'gj_reasons': {f'{k[0]}:{k[1]}': v for k, v in sorted(gj.items())},
                    'first_scored': first_scored, 'final_choice_counts': {str(k[0]): v for k, v in sorted(sel.items())},
                    'nn_overrides_top': [[*k, v] for k, v in nn_over.most_common(8)],
                    'targets_r5_r100_r300': {k: per_round_targets.get(k) for k in (5, 100, 300, 600)}})
    save(HERE / 'homonoliths-trace.json', out)
    print(json.dumps(out, indent=1)[:12000])


if __name__ == '__main__':
    main()
