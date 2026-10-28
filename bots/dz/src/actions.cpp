#include "actions.h"
#include <cmath>

namespace dz {
float danger(vec2 p, const Observation& obs) {
    float damage = 0;
    for (const auto& e : obs.enemies) {
        int distance = static_cast<int>(e.p.chebyshev_distance(p));
        if (distance <= e.range + 1) damage += e.strength;
        if (distance <= 6) damage += .25f * e.strength;
    }
    return damage;
}
namespace {
bool movable(vec2 p, const StaticWorld& w, const Observation& o) { return w.walkable(p) && !o.occupied.is_set(p); }
bool actionable(cambc::champion_state state) {
    return !state.is_dead() && !state.contains(cambc::champion_state::recalling) &&
        !state.contains(cambc::champion_state::submitting_gems) && !state.contains(cambc::champion_state::teleporting);
}
// A bounded payload policy for SafeMode, independent of the later engagement model.
void spells(const cambc::unit* target, bool enemy, bool attacked, const Observation& obs,
            const TurnContext& tc, Actuator& act) {
    auto& me = cambc::self();
    for (auto ability : me.abilities()) {
        if (!tc.allow(3500) || !ability.is_ready() || !actionable(me.state())) continue;
        if (ability.is_attack_reset()) {
            if (attacked && target && target->is_visible() && target->health() > 0 &&
                me.position().chebyshev_distance(target->position()) <= me.attack_range()) {
                if (act.cast(ability) && me.can_attack()) act.attack(*target);
            }
            continue;
        }
        if (ability.is_shield()) {
            if (target && obs.hp < .85f * obs.max_hp && !me.buffs().has<cambc::buff_shield>()) act.cast(ability);
            continue;
        }
        if (!target || !target->is_visible() || target->health() <= 0 || (!enemy && !obs.enemies.empty())) continue;
        if (!(ability.is_damage() || ability.is_cc() || ability.is_aoe_damage())) continue;
        if (enemy ? !ability.can_target_enemies() : !ability.can_target_camps()) continue;
        const auto p = target->position();
        if (!ability.valid_tiles().is_set(p)) continue;
        // CC against stun-immune Marcella has no control value; damaging CC still works.
        if (ability.is_cc() && ability.damage_amount() == 0 && enemy) {
            auto* c = dynamic_cast<const cambc::champion*>(target);
            if (c && c->champion_name() == cambc::champion_type::marcella) continue;
        }
        if (ability.can_target_ground() && ability.is_aoe_damage()) act.cast(ability, p);
        else act.cast(ability, *target);
    }
}
void step(const cambc::distance_field& field, const StaticWorld& world, const Observation& obs,
          bool retreat, Actuator& act) {
    if (!cambc::self().can_move()) return;
    const auto origin = cambc::self().position();
    vec2 best = origin;
    float score_best = 1e30f;
    // Prefer a strictly improving distance. Static fields are not used for collision avoidance.
    for (int dx = -1; dx <= 1; ++dx) for (int dy = -1; dy <= 1; ++dy) {
        auto p = origin + vec2{dx,dy};
        if (!world.walkable(p) || (p != origin && obs.occupied.is_set(p))) continue;
        int d = field.get(p);
        if (d == cambc::distance_field::unreachable) continue;
        float score = static_cast<float>(d) + danger(p, obs) * (retreat ? .08f : .015f);
        if (p == origin && d != 0) score += .2f;
        if (cambc::map::bushes().is_set(p)) score -= .02f;
        if (score < score_best) { score_best = score; best = p; }
    }
    if (best != origin) act.move(best);
}
}
void execute(Goal goal, StaticWorld& world, Memory& mem, const Observation& obs, const TurnContext& tc, Actuator& act) {
    auto& me = cambc::self();
    if (!actionable(me.state())) return;
    const bool retreat = goal.kind == GoalKind::Retreat || goal.kind == GoalKind::Home;
    const cambc::unit* target = nullptr;
    bool enemy = false;
    // Free melee hit while leaving; ranged attacks must not consume the escape move.
    float target_score = -1;
    for (auto& e : obs.enemies) {
        if (obs.p.chebyshev_distance(e.p) > obs.range || (retreat && obs.range > 1)) continue;
        float score = 1 / std::max(1.f, e.hp) + (e.hp <= obs.strength ? 10.f : 0.f);
        if (score > target_score) { target_score = score; target = &e.sdk; enemy = true; }
    }
    const cambc::camp* camp_target = nullptr;
    if (!target && goal.kind == GoalKind::Farm) {
        const auto& group = world.groups[goal.index];
        float best = 1e30f;
        for (const auto& c : group.sdk.camps()) {
            if (!tc.allow(3500)) break;
            if (!c.is_visible() || c.is_dead()) continue;
            float score = static_cast<float>(obs.p.chebyshev_distance(c.position())) * 1000 + c.health();
            if (score < best) { best = score; camp_target = &c; }
        }
        target = camp_target;
    }
    bool attacked = false;
    if (target && me.can_attack() && !obs.restrictions.contains(cambc::buff_restrictions::attack) &&
        obs.p.chebyshev_distance(target->position()) <= obs.range) attacked = act.attack(*target);
    spells(target, enemy, attacked, obs, tc, act);
    if (!tc.allow(world.field_budget())) return;

    // Movement roots encode the role. Dynamic occupancy is included so a crowd
    // cannot cause permanent oscillation around a blocked shortest-path step.
    cambc::bitboard roots;
    auto blocked = world.blocked | obs.occupied;
    if (retreat) {
        roots = cambc::map::spawn_region(cambc::team::ally) & ~blocked;
    } else if (goal.kind == GoalKind::Bank && goal.index >= 0) {
        auto altar = world.altars[goal.index].tile;
        for (int dx = -1; dx <= 1; ++dx) for (int dy = -1; dy <= 1; ++dy) {
            auto p = altar + vec2{dx,dy};
            if (world.walkable(p) && (!obs.occupied.is_set(p) || p == obs.p)) roots.set(p);
        }
    } else if (goal.kind == GoalKind::Farm) {
        auto& g = world.groups[goal.index];
        if (mem.groups[goal.index].state == GroupState::Reward) {
            vec2 nearest = obs.p; int distance = 65535;
            for (auto p : g.tiles) {
                if (!tc.allow(5000)) break;
                const auto d = static_cast<int>(p.chebyshev_distance(obs.p));
                if (d < distance && (movable(p, world, obs) || p == obs.p)) { nearest = p; distance = d; }
            }
            if (distance < 65535) roots.set(nearest);
        } else if (camp_target && camp_target->is_visible() && !camp_target->is_dead()) {
            auto pos = camp_target->position();
            for (int dx = -obs.range; dx <= obs.range; ++dx) for (int dy = -obs.range; dy <= obs.range; ++dy) {
                auto p = pos + vec2{dx,dy};
                if ((movable(p, world, obs) || p == obs.p) && p != pos) roots.set(p);
            }
        } else {
            // Unseen group: route toward free spawn tiles or their adjacency.
            vec2 nearest = obs.p; int distance = 65535;
            for (auto p : g.tiles) {
                if (!tc.allow(5000)) break;
                const auto d = static_cast<int>(p.chebyshev_distance(obs.p));
                if (d < distance) { nearest = p; distance = d; }
            }
            if (distance < 65535) {
                for (int dx = -1; dx <= 1; ++dx) for (int dy = -1; dy <= 1; ++dy) {
                    auto p = nearest + vec2{dx,dy};
                    if (movable(p, world, obs)) roots.set(p);
                }
            }
        }
    }
    bool bank_blocked = goal.kind == GoalKind::Bank && roots.is_empty();
    if (!roots.is_empty() && me.can_move()) {
        cambc::distance_field field;
        field.compute(blocked, roots, world.visited);
        tc.guard();
        bank_blocked = goal.kind == GoalKind::Bank && field.get(obs.p) == cambc::distance_field::unreachable;
        if (!bank_blocked) step(field, world, obs, retreat, act);
    }
    if (bank_blocked && me.can_move()) {
            int prerequisite = -1, nearest = 65535;
            const auto& altar_field = *world.altars[goal.index].field;
            for (unsigned index = 0; index < world.groups.size(); ++index) {
                if (!tc.allow(3000)) break;
                for (auto& c : world.groups[index].sdk.camps()) {
                    if (!tc.allow(3500)) break;
                    if (!c.is_visible() || c.is_dead()) continue;
                    auto p = c.position();
                    int distance = static_cast<int>(obs.p.chebyshev_distance(p));
                    if (distance < nearest && altar_field.get(p) < altar_field.get(obs.p)) {
                        prerequisite = index; nearest = distance;
                    }
                }
            }
            if (prerequisite >= 0 && tc.allow(15000)) {
                mem.observe_group(world, prerequisite, tc);
                auto& b = mem.groups[prerequisite];
                mem.contract.start(prerequisite, tc.round, world.distance(prerequisite, obs.p), b.hp, b.capture);
                execute({GoalKind::Farm, prerequisite}, world, mem, obs, tc, act);
                return;
            }
            // Until the blocking camp is visible, advance along the static route.
            step(altar_field, world, obs, false, act);
    }
    // Refresh the attack allowance after movement: melee can close and hit in one
    // turn; ranged cannot. An exclusive spell also affects these live allowances.
    if (!attacked && target && target->is_visible() && target->health() > 0 && me.can_attack() &&
        me.position().chebyshev_distance(target->position()) <= me.attack_range()) {
        attacked = act.attack(*target);
        spells(target, enemy, attacked, obs, tc, act);
    }
    if (goal.kind == GoalKind::Bank) {
        auto p = me.position(); auto altar = world.altars[goal.index].tile;
        if (p.chebyshev_distance(altar) <= cambc::constants::submit_gems_range) {
            if (cambc::vision::has_altar_lock(altar)) {
                auto lock = cambc::vision::altar_lock_at(altar);
                if (lock.is_enemy() && me.can_attack()) act.attack(lock);
                else if (!lock.is_enemy()) act.bank(altar);
            } else act.bank(altar);
        }
    }
    if (goal.kind == GoalKind::Home && !cambc::map::spawn_region(cambc::team::ally).is_set(me.position()) &&
        danger(me.position(), obs) == 0 && world.home.get(me.position()) > cambc::constants::recall_time + 1) act.recall();
    if (me.ward_cooldown() == 0 && tc.allow(2500) && !obs.restrictions.contains(cambc::buff_restrictions::ward) && actionable(me.state())) {
        auto p = me.position();
        if (!cambc::map::altars().is_set(p) && !cambc::vision::ward_tiles(cambc::team::ally).is_set(p)) act.ward(p);
    }
}
}
