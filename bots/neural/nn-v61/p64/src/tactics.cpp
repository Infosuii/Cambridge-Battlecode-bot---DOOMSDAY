// V58 action density and survival helpers. Selected-objective/visible-contact work only, never a scoring-loop hook.
#include "bot.h"

#if V58_ACT
bool Bot::act_camp_before_walk(GroupRec& g) {
    if (walked || cast_done) return false;
    float reach = 0.0f;
    for (int s = 0; s < 2; ++s) {
        const auto& spell = spells[s];
        if (spell_ready(s) && spell.excludes_walk && spell.camps && spell.modifier > 0.0f)
            reach = std::max(reach, spell.range);
    }
    if (reach <= range) return false;
    int target = -1;
    float key = 1e30f;
    for (int ci : g.camps) {
        const auto& camp = w.camps[ci];
        if (camp.dead || !bit(w.visible, camp.pos) || cheb(pos, camp.pos) > static_cast<int>(reach)) continue;
        const float value = camp.hp - camp.strength * 1000.0f;
        if (value < key) key = value, target = ci;
    }
    if (target < 0 || !cast_on_camp(target)) return false;
    mode = "stand-cast-camp";
    return true;
}

bool Bot::act_enemy_before_walk() {
    if (w.enemies.empty() || walked || cast_done || (!spells[0].excludes_walk && !spells[1].excludes_walk)) return false;
    const EnemyRec* target = nullptr;
    int distance = 999;
    for (const auto& e : w.enemies) {
        const int d = cheb(pos, e.pos);
        if (d < distance) distance = d, target = &e;
    }
    if (!target) return false;
    const bool not_fleeing = act_enemy_id == target->id && act_enemy_round == round - 1 &&
        distance <= cheb(pos, act_enemy_previous);
    act_enemy_id = target->id; act_enemy_round = round; act_enemy_previous = target->pos;
    if (!not_fleeing || distance <= range || hp < 0.65f * max_hp || (gems >= 30 && hp < 0.8f * max_hp)) return false;
    float friendly = strength + focus * 0.125f, hostile = 0.0f;
    for (const auto& a : w.allies) if (a.hp >= 0.5f * a.max_hp && cheb(a.pos, pos) <= 5) friendly += a.strength + a.focus * 0.125f;
    for (const auto& e : w.enemies) if (cheb(e.pos, pos) <= 6) hostile += e.strength + e.focus * 0.125f;
    if (hostile > 1.25f * friendly) return false;
    bool ready = false;
    for (int s = 0; s < 2; ++s) {
        const auto& spell = spells[s];
        if (spell_ready(s) && spell.excludes_walk && spell.modifier > 0.0f &&
            (spell.enemies || spell.kind == bc::ability_kind::aoe_damage) && distance <= static_cast<int>(spell.range)) ready = true;
    }
    if (!ready || !cast_on_enemy(*target)) return false;
    mode = "stand-cast-enemy";
    return true;
}
#endif

#if V58_VISION
void Bot::vision_objective() {
    if (round - vision_checked < 10) return;
    vision_checked = round;
    if (bc::fuel_remaining() < static_cast<std::uint64_t>(tune::kDetSafety) + 5000) return;
    vec2 objective{-1, -1};
    int closest = 5;
    if (gems >= 10) for (vec2 altar : w.altars) {
        const int d = cheb(pos, altar);
        if (d < closest) closest = d, objective = altar;
    }
    if (objective.x < 0 && target_group >= 0 && target_group < static_cast<int>(w.groups.size())) {
        const auto& g = w.groups[target_group];
        if (!g.camps.empty()) {
            const vec2 at = w.camps[g.camps[0]].pos;
            if (cheb(pos, at) <= 4) {
                int enemy = kUnreach;
                for (vec2 spawn : w.enemy_spawn.positions()) enemy = std::min(enemy, cheb(at, spawn));
                const int home = fdist(w.spawn_field, at);
                if (home != kUnreach && home >= 0.65f * enemy) objective = at;
            }
        }
    }
    if (objective.x < 0) for (const auto& enemy : w.enemies) if (cheb(pos, enemy.pos) <= 4) {
        objective = enemy.pos; break;
    }
    if (objective.x < 0 || (ward_pos.x >= 0 && cheb(ward_pos, objective) <= 4)) return;
    auto& me = bc::self();
    try {
        if (me.ward_cooldown() > 0) return;
        const auto valid = me.ward_placement_tiles();
        vec2 best{-1, -1};
        int score = -100000;
        for (vec2 q : valid.positions()) {
            if (q == ward_pos || bit(w.static_blocked, q)) continue;
            const int value = -20 * cheb(q, objective) + std::min(40, static_cast<int>(fdist(w.spawn_field, q)));
            if (value > score) score = value, best = q;
        }
        if (best.x >= 0 && me.place_ward(best)) ward_pos = best;
    } catch (...) { }
}
#endif

#if V58_LOCKS
void Bot::locks_objective() {
    if (bc::fuel_remaining() < static_cast<std::uint64_t>(tune::kDetSafety) + 3000) return;
    for (vec2 altar : w.altars) {
        if (cheb(pos, altar) > 2) continue;
        bool wanted = enemy_score >= 700 && ally_score >= 600;
        for (const auto& enemy : w.enemies)
            if (enemy.gems >= 30 && cheb(enemy.pos, altar) <= 6) wanted = true;
        if (!wanted) continue;
        try {
            if (bc::vision::has_altar_lock(altar)) continue;
            auto& lock = bc::self().consumables()[bc::consumable_type::altar_lock];
            if (lock.count() == 0) return;
            if (lock.use(altar)) return;
        } catch (...) { }
    }
}
#endif

#if V60_HOME_GUARD
// Ladder losses: 6.5 of our 13.8 deaths per game were within 15 tiles of our own spawn and 23% came within 60 rounds of
// respawning, against 13% for the winners: champions left the spawn one at a time into a waiting enemy team. Spawn
// tiles heal and enemies cannot enter them, so a champion on spawn with visible enemies around stays there (hitting
// whatever is in reach) until it has the numbers, is fully healed and the enemy has thinned out, or the hold times out.
bool Bot::home_guard() {
    if (!bit(w.ally_spawn, pos) || round < home_guard_off_until) {
        home_hold_since = -1;
        return false;
    }
    int foes = 0;
    for (const auto& e : w.enemies)
        if (!bit(w.enemy_spawn, e.pos) && cheb(e.pos, pos) <= V60_HOME_RADIUS) ++foes;
    if (V60_HOME_GUARD >= 2 && foes == 0)
        for (const auto& seen : w.sightings)
            if (round - seen.round <= 6 && cheb(seen.pos, pos) <= V60_HOME_RADIUS) ++foes;
    if (foes == 0) {
        home_hold_since = -1;
        return false;
    }
    int friends = 1;
    for (const auto& a : w.allies) friends += cheb(a.pos, pos) <= 6 && a.hp >= 0.6f * a.max_hp;
    if (friends > foes && hp >= 0.9f * max_hp) {
        home_hold_since = -1;
        return false;
    }
    if (home_hold_since < 0) home_hold_since = round;
    if (round - home_hold_since > V60_HOME_HOLD) {
        home_hold_since = -1;
        home_guard_off_until = round + 20; // a stalemate costs farming: go back to normal play for a while
        return false;
    }
    mode = "home-guard";
    return true;
}
#endif

#if V58_SURVIVE
bool Bot::survive_bank_due() const {
    if (gems < 35) return false;
    for (const auto& seen : w.sightings)
        if (round - seen.round <= 15 && cheb(pos, seen.pos) <= 12) return true;
    for (const auto& e : w.enemies) if (cheb(pos, e.pos) <= 12) return true;
    return false;
}

bool Bot::survive_contact() {
    if (w.enemies.empty() || bit(w.ally_spawn, pos) || bc::fuel_remaining() < static_cast<std::uint64_t>(tune::kDetSafety) + 8000) return false;
    const EnemyRec* nearest = nullptr;
    int distance = 999;
    for (const auto& enemy : w.enemies) {
        const int d = cheb(pos, enemy.pos);
        if (d < distance) nearest = &enemy, distance = d;
    }
    if (!nearest || distance > 6) return false;
    auto value = [](float health, float maximum, float attack, float magic) {
        return std::max(1.0f, attack + 0.2f * magic) * (std::max(0.0f, health) + 0.2f * maximum);
    };
    auto stun_slot = [](bc::champion_type champion) {
        using ct = bc::champion_type;
        if (champion == ct::ryth || champion == ct::ren || champion == ct::prism || champion == ct::marcella) return 0;
        if (champion == ct::tavi || champion == ct::heart_of_ruin || champion == ct::cassi) return 1;
        return -1;
    };
    float friendly = value(hp, max_hp, strength, focus), hostile = 0.0f;
    const int my_stun = stun_slot(type);
    if (my_stun >= 0 && spell_ready(my_stun)) friendly *= 1.15f;
    for (const auto& ally : w.allies) {
        const int d = cheb(ally.pos, nearest->pos);
        if (d > ally.range + 3) continue;
        const float reach = d <= ally.range ? 1.0f : 0.6f;
        friendly += reach * value(ally.hp, ally.max_hp, ally.strength, ally.focus);
    }
    for (const auto& enemy : w.enemies) {
        if (cheb(pos, enemy.pos) > 6) continue;
        float power = value(enemy.hp, enemy.max_hp, enemy.strength, enemy.focus);
        const int slot_with_stun = stun_slot(enemy.type);
        if (slot_with_stun >= 0) {
            bool ready = true; // unknown visible-enemy cooldown is conservatively treated as ready
            if (&enemy == nearest) {
                std::int32_t cd = 0;
                if (bc::detail::sdk_champion_cooldown(enemy.id, slot_with_stun, &cd) == 0) ready = cd == 0;
            }
            if (ready) power *= 1.15f;
        }
        hostile += power;
    }
    const bool bag_panic = gems >= 30 && hp < 0.35f * max_hp;
    const bool immediate_finish = distance <= range && nearest->hp < 0.5f * strength;
    if (!bag_panic && (immediate_finish || hostile < 1.65f * friendly)) return false;
    // Prefer a dash landing outside visible attack ranges and known camp danger, then use existing multi-threat retreat.
    bc::bitboard blocked = w.static_blocked | w.unit_tiles | w.hot_zone;
    for (const auto& enemy : w.enemies) blocked.draw_chebyshev(enemy.pos, static_cast<float>(enemy.range));
    const bool previous_combat = combat_move;
    combat_move = true;
    const bool dashed = try_dash(w.spawn_field, blocked);
    combat_move = previous_combat;
    const bool moved = dashed || retreat_from(nearest->pos);
    if (!moved) return false;
    if (bag_panic || hp < 0.45f * max_hp) heading_home = true;
    mode = bag_panic ? "flee-bag" : "flee-power";
    return true;
}
#endif
