"""Apply a sparring style to a copy of exact v109 source (JOHNDOE #151 sparring calibration).

usage: python -I spar_patch.py <src_dir> <style>   style 1 = camp invader, 2 = carrier/altar pressure, 3 = camp invader v2 (sticky target), 4 = invader v3 (steal finished enemy-side rewards only)

Both styles use two raiders (claim slots 0 and 1) from round SPAR_FROM, while healthy and carrying less than
SPAR_GEMS. Every other body and every other turn plays unchanged v109.
  1 camp invader: the raiders' farm target is forced, after all v92/actor overrides, to the best enemy-side camp group
    (camp nearer the enemy spawn: d_enemy < 0.8 d_ours). Reward-state groups and groups where enemies were seen
    recently come first.
  2 carrier/altar pressure: before hunt(), a raider walks at and hits any visible off-spawn enemy carrying >=
    SPAR_CARRY gems within 12. Otherwise its farm target is forced to a group within 16 of the altar nearest the
    enemy spawn, and with none open it posts 3 tiles from that altar.
"""
import os
import sys

src, style = sys.argv[1], int(sys.argv[2])


def patch(name, old, new, count=1):
    p = os.path.join(src, name)
    t = open(p, encoding="utf-8").read()
    assert t.count(old) == count, (name, old[:60], t.count(old))
    open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))


patch("common.h", "#define CLFS 1\n", f"#define CLFS 1\n#define SPAR_STYLE {style}\n")

patch("bot.h", "    bool hunt();\n", """    bool hunt();
#if SPAR_STYLE
    bool spar_raider() const;
    int spar_pick();
    bool spar_pressure();
    bool spar_post();
    int spar_last = -2;
    std::uint32_t spar_chased = 0xffffffffu;
    int spar_commit = -1, spar_commit_round = 0;
    std::vector<int> spar_ban;
#endif
""")

impl = r'''
#if SPAR_STYLE
#ifndef SPAR_FROM
#define SPAR_FROM 100
#endif
#ifndef SPAR_GEMS
#define SPAR_GEMS 40
#endif
#ifndef SPAR_COMMIT
#define SPAR_COMMIT 60
#endif
#ifndef SPAR_CARRY
#define SPAR_CARRY 20
#endif
namespace {
vec2 spar_center(const std::vector<vec2>& ps) {
    long x = 0, y = 0;
    for (vec2 p : ps) x += p.x, y += p.y;
    const long n = ps.empty() ? 1 : static_cast<long>(ps.size());
    return vec2{static_cast<int>(x / n), static_cast<int>(y / n)};
}
} // namespace

bool Bot::spar_raider() const {
    return slot <= 1 && team_size >= 3 && round >= SPAR_FROM && gems < SPAR_GEMS && hp >= 0.5f * max_hp;
}

int Bot::spar_pick() {
    if (!spar_raider() || w.spawn_tiles.empty()) return -1;
    const vec2 A = spar_center(w.spawn_tiles), B = spar_center(w.enemy_spawn.positions());
    vec2 altar{-1, -1};
#if SPAR_STYLE == 2
    for (vec2 a : w.altars)
        if (altar.x < 0 || cheb(a, B) < cheb(altar, B)) altar = a;
    if (altar.x < 0) return -1;
#endif
#if SPAR_STYLE >= 3
    // v2: commit to one raid group until it is taken (respawning), avoided, or SPAR_COMMIT rounds pass; a timed-out
    // group is banned for 40 rounds so the raiders stop churning between enemy-side targets.
    if (spar_ban.size() != w.groups.size()) spar_ban.assign(w.groups.size(), 0);
    if (spar_commit >= 0 && spar_commit < static_cast<int>(w.groups.size())) {
        const auto& cg = w.groups[static_cast<std::size_t>(spar_commit)];
        const bool gone = cg.state == GroupState::respawning ||
            (static_cast<std::size_t>(spar_commit) < avoid_until.size() && avoid_until[static_cast<std::size_t>(spar_commit)] > round);
        if (!gone && round - spar_commit_round <= SPAR_COMMIT) {
            if (spar_commit != spar_last) {
                std::printf("SPR %d %u %d %d %d\n", round, my_id, slot, SPAR_STYLE, spar_commit);
                spar_last = spar_commit;
            }
            return spar_commit;
        }
        if (!gone) spar_ban[static_cast<std::size_t>(spar_commit)] = round + 40;
        spar_commit = -1;
    }
#endif
    int best = -1, best_key = 1 << 30;
    for (std::size_t gi = 0; gi < w.groups.size(); ++gi) {
        const auto& g = w.groups[gi];
#if SPAR_STYLE >= 3
        if (spar_ban[gi] > round) continue;
#endif
        if (g.camps.empty() || (g.gems == 0 && g.gold < 40)) continue;
        if (gi < avoid_until.size() && avoid_until[gi] > round) continue;
        if (g.state == GroupState::respawning && g.respawn_round - round > 15) continue;
#if SPAR_STYLE == 4
        // v3: steal only finished enemy-side rewards (or ones back within 10 rounds); one raider per group
        if (g.state == GroupState::alive || (g.state == GroupState::respawning && g.respawn_round - round > 10)) continue;
        if (claim_of(1 - slot) == static_cast<int>(gi)) continue;
#endif
        const vec2 c = w.camps[static_cast<std::size_t>(g.camps[0])].pos;
#if SPAR_STYLE == 1 || SPAR_STYLE >= 3
        if (cheb(c, B) * 10 >= cheb(c, A) * 8) continue; // enemy side only
#else
        if (cheb(c, altar) > 16) continue; // around the enemy altar
#endif
        const int d = w.has_field(static_cast<int>(gi)) ? w.group_distance(static_cast<int>(gi), pos) : cheb(c, pos);
        if (d >= kUnreach) continue;
#if SPAR_STYLE == 4
        if (d > 25) continue;
#endif
        int key = d;
        if (g.state == GroupState::reward) key -= SPAR_STYLE >= 3 ? 30 : 15;
        if (round - g.enemy_round <= 30) key -= 10;
        if (key < best_key) best_key = key, best = static_cast<int>(gi);
    }
#if SPAR_STYLE >= 3
    if (best >= 0) spar_commit = best, spar_commit_round = round;
#endif
    if (best != spar_last) {
        std::printf("SPR %d %u %d %d %d\n", round, my_id, slot, SPAR_STYLE, best);
        spar_last = best;
    }
    return best;
}

bool Bot::spar_post() {
#if SPAR_STYLE == 2
    if (!spar_raider() || !bc::self().can_move()) return false;
    const vec2 B = spar_center(w.enemy_spawn.positions());
    vec2 altar{-1, -1};
    for (vec2 a : w.altars)
        if (altar.x < 0 || cheb(a, B) < cheb(altar, B)) altar = a;
    if (altar.x < 0) return false;
    mode = "spar-post";
    if (cheb(pos, altar) <= 3) return true;
    bc::bitboard goal;
    goal.clear();
    goal.draw_chebyshev(altar, 3.0f);
    walk_toward(goal);
    return true;
#else
    return false;
#endif
}

bool Bot::spar_pressure() {
#if SPAR_STYLE == 2
    if (!spar_raider()) return false;
    const EnemyRec* best = nullptr;
    int bd = 13;
    for (const auto& e : w.enemies) {
        if (e.hp <= 0 || e.gems < SPAR_CARRY || bit(w.enemy_spawn_zone, e.pos)) continue;
        const int d = cheb(e.pos, pos);
        if (d < bd || (d == bd && best && e.gems > best->gems)) bd = d, best = &e;
    }
    if (!best) return false;
    if (best->id != spar_chased) {
        std::printf("SPC %d %u %d %u %d %d\n", round, my_id, slot, best->id, best->gems, bd);
        spar_chased = best->id;
    }
    FlagScope combat{combat_move};
    mode = "spar-chase";
    if (cheb(best->pos, pos) <= range) {
        cast_on_enemy(*best);
        if (attack_unit(best->unit, best->pos)) use_reset_and_attack(best->unit, best->pos);
        return true;
    }
    bc::bitboard goal;
    goal.clear();
    goal.draw_chebyshev(best->pos, static_cast<float>(range));
    walk_toward(goal);
    if (cheb(best->pos, pos) <= range) {
        cast_on_enemy(*best);
        attack_unit(best->unit, best->pos);
    }
    return true;
#else
    return false;
#endif
}
#endif

// Move toward the freshest nearby enemy sighting when healthy and not carrying much.
bool Bot::hunt() {'''
patch("bot.cpp", "\n// Move toward the freshest nearby enemy sighting when healthy and not carrying much.\nbool Bot::hunt() {", impl)

# decision chain: carrier chase before hunt()
patch("bot.cpp", "    } else if (hunt()) {\n    } else if (\n", """#if SPAR_STYLE
    } else if (spar_pressure()) {
#endif
    } else if (hunt()) {
    } else if (
""")

# farm: forced raid target after all v92 / actor overrides
patch("bot.cpp", """    // The planner chose a bank trip first (APEX_PLAN).
    if (tune::kPlan && plan_bank_round == round && gems >= 10) {""", """#if SPAR_STYLE
    if (!low_fuel) {
        const int sp = spar_pick();
        if (sp >= 0) best = sp, best_need = 1;
        else if (spar_post()) return true;
    }
#endif
    // The planner chose a bank trip first (APEX_PLAN).
    if (tune::kPlan && plan_bank_round == round && gems >= 10) {""")
print("patched", src, "style", style)
