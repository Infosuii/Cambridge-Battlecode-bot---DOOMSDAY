// v67 contact controller: bounded local power, shared focus, early retreats and direct action application.
#include "bot.h"

#ifndef V67_FIGHT
#define V67_FIGHT 0
#endif
#ifndef V67_JOIN_RATIO
#define V67_JOIN_RATIO 1.10f
#endif
#ifndef V67_FLEE_RATIO
#define V67_FLEE_RATIO 0.78f
#endif
#ifndef V67_LEAVE_HP
#define V67_LEAVE_HP 0.60f
#endif

bool Bot::v67_contact() {
    if (!V67_FIGHT || w.enemies.empty()) return false;
    const EnemyRec* target = nullptr;
    int nearest = 99;
    for (const auto& e : w.enemies) {
        const int distance = cheb(pos, e.pos);
        if (e.hp <= 0 || (bit(w.enemy_spawn, e.pos) && distance > range)) continue;
        if (distance < nearest || (distance == nearest && target && e.hp < target->hp))
            nearest = distance, target = &e;
    }
    if (!target || nearest > 7) return false;
    struct Restore {
        bool& flag;
        bool previous;
        ~Restore() { flag = previous; }
    } restore{combat_move, combat_move};
    combat_move = true;
    const auto power = [](float health, float attack, float magic) {
        return std::max(0.0f, health) * std::max(1.0f, attack + magic * 0.20f);
    };
    float ours = power(hp, strength, focus), theirs = 0;
    int friends = 1, enemies = 0;
    for (const auto& a : w.allies) {
        const int distance = cheb(a.pos, target->pos);
        if (a.hp <= 0 || distance > a.range + 4) continue;
        const float arrival = std::max(0.25f, 1 - std::max(0, distance - a.range) / 7.0f);
        ours += arrival * power(a.hp, a.strength, a.focus);
        friends += distance <= a.range + 2;
    }
    for (const auto& e : w.enemies) {
        if (cheb(e.pos, pos) > 7 || e.hp <= 0) continue;
        theirs += power(e.hp, e.strength, e.focus);
        ++enemies;
    }
    const float ratio = ours / std::max(1.0f, theirs), fraction = hp / std::max(1.0f, max_hp);
    const bool finish = nearest <= range && target->hp <= strength * (spell_ready(0) || spell_ready(1) ? 1.5f : 0.8f);
    const bool flee = !finish && (ratio < V67_FLEE_RATIO ||
        (fraction < V67_LEAVE_HP && ratio < 1.6f) ||
        (friends == 1 && enemies >= 2 && ratio < 1.35f));
    const bool engage = finish || (ratio >= V67_JOIN_RATIO && fraction >= 0.65f) ||
                        (nearest <= range && ratio >= 0.95f && fraction >= 0.75f);
    if (w.groups.size() < 112) {
        if (enemy_handles.empty())
            for (const auto& e : bc::champions(team::enemy))
                enemy_handles.push_back(static_cast<std::uint32_t>(static_cast<bc::handle_champion_t>(e)));
        if (engage && !flee) {
            for (int s = 0; s < std::min(slot, kClaimSlots); ++s) {
                const int claim = claim_of(s);
                if (claim < 112 || claim >= 118 || static_cast<std::size_t>(claim - 112) >= enemy_handles.size()) continue;
                bool near = false;
                for (const auto& a : w.allies)
                    near |= a.id == ally_handle[s] && cheb(a.pos, pos) <= 7;
                if (!near) continue;
                for (const auto& e : w.enemies)
                    if (e.id == enemy_handles[claim - 112] && cheb(pos, e.pos) <= nearest + 2) target = &e;
                break;
            }
            const auto at = std::find(enemy_handles.begin(), enemy_handles.end(), target->id);
            if (at != enemy_handles.end() && at - enemy_handles.begin() < 6)
                write_order(112 + static_cast<int>(at - enemy_handles.begin()));
        } else if (flee) write_order(118);
    }
    auto& me = bc::self();
    if (flee) {
        mode = "v67-retreat";
        if (melee)
            for (const auto& e : w.enemies)
                if (cheb(e.pos, pos) <= range && attack_unit(e.unit, e.pos)) break;
        const bool dashed = dash_away();
        const bool stepped = me.can_move() && retreat_from(target->pos);
        if (!dashed && !stepped && cheb(pos, target->pos) <= range) {
            cast_on_enemy(*target);
            if (attack_unit(target->unit, target->pos)) use_reset_and_attack(target->unit, target->pos);
        }
        if (fraction < 0.65f) heading_home = true;
        return true;
    }
    if (!engage) {
        if (nearest <= target->range + 2) {
            mode = "v67-space";
            if (melee && nearest <= range) attack_unit(target->unit, target->pos);
            retreat_from(target->pos);
            return true;
        }
        return false;
    }
    mode = "v67-engage";
    // Reach spell or striking dash opens the encounter. Reset helpers remain basic -> reset -> basic.
    cast_on_enemy(*target);
    if (cheb(pos, target->pos) <= range) {
        if (attack_unit(target->unit, target->pos)) use_reset_and_attack(target->unit, target->pos);
        return true;
    }
    if (me.can_move()) {
        bc::bitboard goals;
        goals.clear();
        goals.draw_chebyshev(target->pos, static_cast<float>(range));
        walk_toward(goals);
    }
    if (cheb(pos, target->pos) <= range) {
        cast_on_enemy(*target);
        if (attack_unit(target->unit, target->pos)) use_reset_and_attack(target->unit, target->pos);
    }
    return true;
}
