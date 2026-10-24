"""Agent A: build the teacher-capture scratch tree (patch 03) from ROOT/bot/src.

Adds compile-time-gated captures (`if constexpr (nnt::k...)`, nn_teacher.h) of teacher locals at the proposed hook
points. With every head off the gates are false and no code is generated. Every edit is anchored on unique original
text; hunks are placed away from patches 01/02 so the three patches apply in any order.

    python tools/audit_teacher_capture.py <dest_src_dir>
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G = 'if constexpr (nnt::k{k}) nn_teacher_access::'  # gate prefix


def sub(t: str, old: str, new: str) -> str:
    n = t.count(old)
    if n != 1:
        raise SystemExit(f'anchor found {n} times: {old[:80]!r}')
    return t.replace(old, new, 1)


SHOP_PREPASS = '''    if constexpr (nnt::kShop) {
        // Teacher capture (nn_teacher.h): the first purchase the loop below will make, computed before buying.
        int g = gold, step_i = -1, want = 0;
        bool lock = false;
        std::uint32_t item = 0;
        try {
            if (tune::kAltarLocks && g >= 10 && me.can_buy(bc::consumable_type::altar_lock)) lock = true, g -= 10;
            if (g >= 30) {
                const auto counts = me.item_count();
                int k = 0;
                for (const auto& step : build_for(type)) {
                    int owned = static_cast<int>(counts[step.item]);
                    if (const auto emblem = step.item.result()) owned += static_cast<int>(counts[*emblem]) * 5;
                    const int wv = std::min(step.total - owned, g / 30);
                    if (wv > 0) {
                        step_i = k, want = wv, item = static_cast<std::uint32_t>(step.item);
                        break;
                    }
                    ++k;
                }
            }
        } catch (...) {
        }
        nn_teacher_access::cap_shop(*this, lock, step_i, item, want);
    }
'''


def capture(src: Path) -> None:
    p = src / 'bot.cpp'
    t = p.read_text(encoding='utf-8')
    t = sub(t, 'namespace d = cambc::detail;\n',
            'namespace d = cambc::detail;\n#include "nn_teacher.h" // teacher captures: compile-time gated, no code with every head off\n')
    # shop: teacher's next purchase (hook: shop head before the build loop)
    t = sub(t, 'void Bot::shop() {\n    PROF(shop);\n    auto& me = bc::self();\n',
            'void Bot::shop() {\n    PROF(shop);\n    auto& me = bc::self();\n' + SHOP_PREPASS)
    # follow_field: ordered downhill steps (hook: move head after the sort, before the move loop)
    t = sub(t, '    std::sort(cands.begin(), cands.begin() + n, [](const Cand& a, const Cand& b) { return a.score < b.score; });\n',
            '    std::sort(cands.begin(), cands.begin() + n, [](const Cand& a, const Cand& b) { return a.score < b.score; });\n'
            '    ' + G.format(k='Move') + 'cap_steps(*this, cands.data(), n);\n')
    # cast_on_enemy: slot / striking-dash choice (hook: combat head before `if (dash_slot >= 0)`)
    t = sub(t, '        if (best_hits > -1000) {\n            dash_slot = s;\n            best_value = value;\n        }\n    }\n    if (dash_slot >= 0) {\n',
            '        if (best_hits > -1000) {\n            dash_slot = s;\n            best_value = value;\n        }\n    }\n'
            '    ' + G.format(k='Cast') + 'cap_cast(*this, e, best, best_value, dash_slot, dash_aim);\n    if (dash_slot >= 0) {\n')
    # ward_ahead: chosen bush tile (hook: ward head before `if (best.x < 0)`)
    t = sub(t, '    if (best.x < 0) return false;\n    try {\n        if (me.place_ward(best)) {\n            ward_pos = best;\n            return true;\n'
               '        }\n    } catch (const std::exception& e) {\n        LOG("ward ahead error',
            '    ' + G.format(k='Ward') + 'cap_ward(*this, best, best_d);\n'
            '    if (best.x < 0) return false;\n    try {\n        if (me.place_ward(best)) {\n            ward_pos = best;\n            return true;\n'
            '        }\n    } catch (const std::exception& e) {\n        LOG("ward ahead error')
    # handle_enemies: threat summary, per-enemy target keys, formula / team / search / final verdicts
    t = sub(t, '    const float ci_risk = (type == bc::champion_type::cassi || type == bc::champion_type::issac) ? tune::kCiRisk : 1.0f;\n',
            '    const float ci_risk = (type == bc::champion_type::cassi || type == bc::champion_type::issac) ? tune::kCiRisk : 1.0f;\n'
            '    ' + G.format(k='Fight') + 'cap_fight_begin(*this, nearest_d, ttd, threat_on_me, risk);\n')
    t = sub(t, '        const float key = ttk / worth;\n        if (key < best_key) {',
            '        const float key = ttk / worth;\n        ' + G.format(k='Fight') + 'cap_enemy(e, key, ttk, worth, dist);\n        if (key < best_key) {')
    t = sub(t, '    bool tfc_applied = false;\n',
            '    ' + G.format(k='Fight') + 'cap_formula(target, target_ttk, winning, in_danger);\n    bool tfc_applied = false;\n')
    t = sub(t, '            order = team_decide(order_target);\n            commander = order != 0;\n        }\n',
            '            order = team_decide(order_target);\n            commander = order != 0;\n        }\n'
            '        ' + G.format(k='Fight') + 'cap_tfc(order);\n')
    t = sub(t, '        const int verdict = tactical_decide();\n',
            '        const int verdict = tactical_decide();\n        ' + G.format(k='Fight') + 'cap_td_verdict(verdict);\n')
    t = sub(t, '#endif\n    if (tune::kTribDeny & 2) {\n        if (in_danger && !winning) try_lock_altar();',
            '#endif\n    ' + G.format(k='Fight') + 'cap_fight_final(target, winning, in_danger, threat_on_me);\n'
            '    if (tune::kTribDeny & 2) {\n        if (in_danger && !winning) try_lock_altar();')
    # tribute_if_needed: bank verdict and its terms (hook: bank head right after `go`)
    t = sub(t, '        dist <= tune::kTributeNearDist + static_cast<int>(std::lround(2.0f * LABK(36))) || (threatened && gems >= 20 && dist <= 8);\n',
            '        dist <= tune::kTributeNearDist + static_cast<int>(std::lround(2.0f * LABK(36))) || (threatened && gems >= 20 && dist <= 8);\n'
            '    ' + G.format(k='Bank') + 'cap_bank(*this, go, dist, wins, late, end_bank, rhythm, edge, threatened, use_safe);\n')
    # score_groups: top-K first targets + final choice (objective head hooks in farm() before the commit)
    t = sub(t, '#endif\n    return best;\n}\n',
            '#endif\n    ' + G.format(k='Objective') + 'cap_objective(*this, top, n_top, best, best_need, best_score, participants_hint);\n'
            '    return best;\n}\n')
    # play_turn: dead turn and the behaviour-chain branch taken
    t = sub(t, '        // Dead turns have the whole budget free: use it to precompute distance fields.\n        if (inited) build_fields();\n        return;\n',
            '        ' + G.format(k='Chain') + 'cap_chain(*this, nnt::Chain::dead);\n'
            '        // Dead turns have the whole budget free: use it to precompute distance fields.\n        if (inited) build_fields();\n        return;\n')
    t = sub(t, '    if (fought) {\n        if (std::string_view(mode) == "idle") mode = "enemy";\n',
            '    if (fought) {\n        ' + G.format(k='Chain') + 'cap_chain(*this, nnt::Chain::enemy);\n'
            '        if (std::string_view(mode) == "idle") mode = "enemy";\n')
    t = sub(t, '        mode = "tribute-win";\n',
            '        mode = "tribute-win";\n        ' + G.format(k='Chain') + 'cap_chain(*this, nnt::Chain::tribute_win);\n')
    t = sub(t, '        if (std::string_view(mode) == "idle") mode = "home";\n',
            '        if (std::string_view(mode) == "idle") mode = "home";\n        ' + G.format(k='Chain') + 'cap_chain(*this, nnt::Chain::home);\n')
    t = sub(t, '    } else if (hunt()) {\n    } else if (tribute_if_needed()) {\n        mode = "tribute";\n    } else {\n        if (!farm()) mode = "nofarm";\n',
            '    } else if (hunt()) {\n        ' + G.format(k='Chain') + 'cap_chain(*this, nnt::Chain::hunt);\n'
            '    } else if (tribute_if_needed()) {\n        mode = "tribute";\n        ' + G.format(k='Chain') + 'cap_chain(*this, nnt::Chain::tribute);\n'
            '    } else {\n        if (!farm()) mode = "nofarm";\n'
            '        ' + G.format(k='Chain') + 'cap_chain(*this, std::string_view(mode) == "nofarm" ? nnt::Chain::nofarm : nnt::Chain::farm);\n')
    p.write_text(t, encoding='utf-8', newline='\n')

    p = src / 'tsearch.cpp'
    t = p.read_text(encoding='utf-8')
    t = sub(t, '#include <cstring>\n#include <variant>\n', '#include <cstring>\n#include <variant>\n\n#include "nn_teacher.h"\n')
    t = sub(t, '    const float margin = std::max(0.0f, tune::kTsDecideMargin + LABK(30)); // lab knob 30: decide margin\n',
            '    const float margin = std::max(0.0f, tune::kTsDecideMargin + LABK(30)); // lab knob 30: decide margin\n'
            '    ' + G.format(k='Fight') + 'cap_td_values(fight, run, margin);\n')
    p.write_text(t, encoding='utf-8', newline='\n')

    p = src / 'draft.cpp'
    t = p.read_text(encoding='utf-8')
    t = sub(t, 'using cd = bc::champion_draft;\n', 'using cd = bc::champion_draft;\n#include "nn_teacher.h" // draft capture (compile-time gated)\n')
    t = sub(t, '    for (int c = 0; c < 12; ++c) {\n        if (taken[c]) continue;\n        float z = dn::b2;\n',
            '    ' + G.format(k='Draft') + 'cap_draft_begin();\n'
            '    for (int c = 0; c < 12; ++c) {\n        if (taken[c]) continue;\n        float z = dn::b2;\n')
    t = sub(t, '        if (z > best_z) best_z = z, best = c;\n    }\n    (void)x;\n    if (best < 0) return false;\n    bc::draft::pick(static_cast<cd>(best));\n',
            '        ' + G.format(k='Draft') + 'cap_draft_score(c, z);\n'
            '        if (z > best_z) best_z = z, best = c;\n    }\n    (void)x;\n    if (best < 0) return false;\n'
            '    ' + G.format(k='Draft') + 'cap_draft_pick(best); // draft_pick head hook: substitute `best` here\n'
            '    bc::draft::pick(static_cast<cd>(best));\n')
    p.write_text(t, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    dest = Path(sys.argv[1]).resolve()
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(ROOT / 'bot' / 'src', dest, ignore=shutil.ignore_patterns('.cambc'))
    capture(dest)
    print('ok', dest)
