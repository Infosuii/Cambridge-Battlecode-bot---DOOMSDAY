// Objective-aware combat: protect completed work; contest a reward only with immediate, supported access.
#include "bot.h"
#include "fight.h"

#if V58_CAPTURE_STAND
bool Bot::capture_stand() {
    if (target_group < 0 || target_group >= static_cast<int>(w.groups.size()) || hp < 0.55f * max_hp ||
        gems >= 40 || heading_home || win_now() || round + capture_time >= bc::constants::max_rounds ||
        bit(w.hot_zone, pos) || (bc::fuel_remaining() + nn_spent) < 18000) return false;
    const auto& g = w.groups[target_group];
    if (g.state != GroupState::reward || !bit(g.tiles, pos)) return false;
    float burst = 0.0f;
    const EnemyRec* target = nullptr;
    for (const auto& e : w.enemies) {
        if (bit(g.tiles, e.pos)) return false; // capture cannot advance with an enemy occupying the region
        if (e.tributing() && enemy_score + e.gems >= static_cast<int>(bc::constants::winning_gems)) return false;
        const int distance = cheb(e.pos, pos);
        if (distance <= e.range + 2) burst += 3.0f * e.strength; // two turns plus one possible attack reset
        if (distance <= 5) {
            const auto kit = spell_kit(e.type, e.focus);
            burst += kit.nuke * (kit.two_spells ? 2.0f : 1.0f);
        }
        if (distance <= std::max(range, 4) && (!target || e.hp < target->hp)) target = &e;
    }
    if (hp <= 1.3f * burst) {
#if V58_CAPTURE_FOOTWORK
        // Only replace a flight from an unsafe tile, never a safe attack. No teammate already on the reward.
        bool occupied = false;
        for (const auto& ally : w.allies) occupied |= bit(g.tiles, ally.pos);
        if (!occupied && bc::self().can_move() && (bc::fuel_remaining() + nn_spent) >= 24000) {
            vec2 safe{-1, -1};
            float least = burst;
            for (vec2 delta : kDirs) {
                const vec2 q = pos + delta;
                if (q.x < 0 || q.y < 0 || q.x >= w.width || q.y >= w.height) continue;
                if (!bit(g.tiles, q) || bit(w.static_blocked, q) || bit(w.unit_tiles, q) || bit(w.hot_zone, q)) continue;
                float incoming = 0.0f;
                for (const auto& enemy : w.enemies) {
                    const int distance = cheb(q, enemy.pos);
                    if (distance <= enemy.range + 2) incoming += 3.0f * enemy.strength;
                    if (distance <= 5) {
                        const auto kit = spell_kit(enemy.type, enemy.focus);
                        incoming += kit.nuke * (kit.two_spells ? 2.0f : 1.0f);
                    }
                }
                if (hp > 1.3f * incoming && incoming < least) safe = q, least = incoming;
            }
            if (safe.x >= 0) {
                try {
                    if (bc::self().move_absolute(safe)) {
                        pos = safe; walked = true; mode = "capture-shift"; return true;
                    }
                } catch (...) {}
            }
        }
#endif
        return false;
    }
#if V58_CAPTURE_STAND >= 2
    // One visible anchor is enough. Prefer Vesper's capture bonus, then stable actor id; other bodies retain combat.
    std::uint32_t anchor = my_id;
    bool anchor_carry = type == bc::champion_type::vesper_vale;
    for (const auto& ally : w.allies) {
        const bool carry = ally.type == bc::champion_type::vesper_vale;
        if ((!carry && anchor_carry) || (carry == anchor_carry && ally.id >= anchor)) continue;
        if (!bit(g.tiles, ally.pos) || ally.hp < 0.55f * ally.max_hp || ally.hp <= 1.3f * burst ||
            bit(w.hot_zone, ally.pos)) continue;
        try {
            const int bag = static_cast<int>(ally.unit.gem_count());
            if (bag >= 40 || ally_score + bag >= static_cast<int>(bc::constants::winning_gems)) continue;
        } catch (...) { continue; }
        anchor = ally.id; anchor_carry = carry;
    }
    if (anchor != my_id) return false;
#endif
    if (target) {
        // Only stationary offensive casts: cast_on_enemy also considers striking dashes, which can leave the region.
        int best = -1;
        float best_damage = -1.0f;
        for (int s = 0; s < 2; ++s) {
            const auto& spell = spells[s];
            if (!spell_ready(s) || !spell.enemies || cheb(pos, target->pos) > static_cast<int>(spell.range)) continue;
            if (spell.kind != bc::ability_kind::damage && spell.kind != bc::ability_kind::aoe_damage &&
                spell.kind != bc::ability_kind::cc) continue;
            const float damage = spell.modifier * focus + (spell.kind == bc::ability_kind::cc ? 120.0f : 0.0f);
            if (damage > best_damage) best = s, best_damage = damage;
        }
        if (best >= 0) {
            try {
                auto ability = bc::self().abilities()[best];
                const bool used = spells[best].ground ? ability.use(target->pos) : ability.use(target->unit);
                if (used) cast_done = true;
            } catch (...) {}
        }
        if (cheb(pos, target->pos) <= range) attack_unit(target->unit, target->pos);
    }
    mode = "capture-stand";
    return true;
}
#endif

#if V58_DENY_CAP
bool Bot::deny_capture() {
    if (gems >= 20 || hp < 0.75f * max_hp || heading_home || win_now() || !bc::self().can_move() ||
        (bc::fuel_remaining() + nn_spent) < 24000) return false;
    int best = -1;
    vec2 landing{-1, -1};
    float best_value = 0.0f;
    for (int gi = 0; gi < static_cast<int>(w.groups.size()); ++gi) {
        const auto& g = w.groups[gi];
        if (g.state != GroupState::reward || bit(g.tiles, pos)) continue;
        bool enemy_on = false;
        for (const auto& e : w.enemies) if (bit(g.tiles, e.pos)) { enemy_on = true; break; }
        if (!enemy_on) continue;
        vec2 tile{-1, -1};
        for (vec2 q : g.tiles.positions()) if (cheb(q, pos) == 1 && !bit(w.static_blocked, q) &&
            !bit(w.unit_tiles, q) && !bit(w.hot_zone, q)) { tile = q; break; }
        if (tile.x < 0) continue; // guaranteed immediate entry, never a remote chase
        float friendly = strength + 0.2f * focus, hostile = 0.0f;
        int helpers = 0;
        for (const auto& ally : w.allies) if (ally.hp >= 0.5f * ally.max_hp && cheb(ally.pos, tile) <= ally.range + 1) {
            friendly += ally.strength + 0.2f * ally.focus; ++helpers;
        }
        for (const auto& enemy : w.enemies) if (cheb(enemy.pos, tile) <= enemy.range + 2)
            hostile += enemy.strength + 0.2f * enemy.focus;
        if (helpers == 0 || friendly < 1.2f * hostile) continue;
        const float value = g.gems + 0.2f * g.gold;
        if (value > best_value) best_value = value, best = gi, landing = tile;
    }
    if (best < 0) return false;
    bc::bitboard goal; goal.clear(); goal.set(landing, true);
    if (!walk_toward(goal)) return false;
    mode = "capture-deny";
    return true;
}
#endif

#if V58_CAMP_CONTACT
bool Bot::camp_contact() {
    if (target_group < 0 || target_group >= static_cast<int>(w.groups.size()) || hp < 0.65f * max_hp ||
        gems >= 40 || heading_home || win_now() || (bc::fuel_remaining() + nn_spent) < 30000) return false;
    for (const auto& enemy : w.enemies)
        if (cheb(pos, enemy.pos) <= std::max(6, enemy.range + 2)) return false;
    auto& group = w.groups[target_group];
    if (group.state != GroupState::alive || group.hp_left(w.camps) > 4.0f * my_dps(&group)) return false;
    bool engaged = false, damaged = false;
    for (int ci : group.camps) {
        const auto& camp = w.camps[ci];
        damaged |= camp.dead || camp.hp < camp.max_hp;
        engaged |= !camp.dead && bit(w.visible, camp.pos) && cheb(camp.pos, pos) <= range;
    }
    if (!engaged || !damaged || hp - 2.0f * incoming_from_group(group, pos) < 0.5f * max_hp) return false;
    // Existing camp staffing, targeting, tank rotation, cast ordering and movement remain authoritative.
    return fight_camps(group, champions_needed(group, group.hp_left(w.camps)));
}
#endif
