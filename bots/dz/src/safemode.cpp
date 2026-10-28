#include "safemode.h"

namespace dz {
Goal safe_goal(StaticWorld& world, Memory& mem, const Observation& obs, const TurnContext& tc) {
    float ours = obs.hp * obs.strength, theirs = 0;
    bool close = false;
    for (const auto& a : obs.allies) if (obs.p.chebyshev_distance(a.p) <= 6) ours += a.hp * a.strength;
    for (const auto& e : obs.enemies) {
        if (obs.p.chebyshev_distance(e.p) <= 8) theirs += e.hp * e.strength;
        if (obs.p.chebyshev_distance(e.p) <= e.range + 2) close = true;
    }
    if (close && (obs.hp < .6f * obs.max_hp || theirs > ours * 1.2f)) return {GoalKind::Retreat};
    int altar = -1, altar_distance = 65535;
    for (unsigned a = 0; a < world.altars.size(); ++a) {
        int d = world.altar_distance(a, obs.p);
        if (d < altar_distance) { altar = a; altar_distance = d; }
    }
    if (altar >= 0 && bank_now(obs.bag, altar_distance, obs.submitted, cambc::constants::winning_gems)) return {GoalKind::Bank, altar};
    if (obs.hp < .3f * obs.max_hp || obs.gold >= 150) return {GoalKind::Home};

    int current = mem.contract.objective;
    if (current >= 0) {
        const auto& belief = mem.groups[current];
        const auto dist = world.distance(current, obs.p);
        if (belief.available(tc.round) && mem.contract.progressing(tc.round, dist, belief.hp, belief.capture))
            return {GoalKind::Farm, current};
        if (!belief.available(tc.round)) mem.contract.objective = -1;
        else mem.release(tc.round);
    }
    auto word = shared_word();
    float best = 1e30f; int chosen = -1;
    const auto type = cambc::self().champion_name();
    const bool runner = type == cambc::champion_type::vesper_vale || type == cambc::champion_type::tavi;
    for (unsigned i = 0; i < world.groups.size(); ++i) {
        if (!tc.allow(3500)) break;
        const auto& belief = mem.groups[i]; const auto& g = world.groups[i];
        if (!belief.available(tc.round)) continue;
        const int dist = world.distance(i, obs.p);
        if (dist >= 65535 || (!g.field && dist > 30)) continue;
        int claims = 0;
        for (unsigned slot = 0; slot < world.allies.size() && slot < protocol::slots; ++slot)
            if (slot != world.slot && i < 112 && protocol::slot(word, slot).objective == i) ++claims;
        // A nearest-safe-group policy, not the unvalidated ObjModel/auction.
        float score = static_cast<float>(dist) + .03f * g.strength + (g.cluster ? claims * 10.f : claims * 2.f);
        if (runner && !g.cluster) score += 12;
        if (belief.state == GroupState::Reward) score -= 8;
        for (const auto& e : obs.enemies) for (auto p : g.tiles) {
            if (e.p.chebyshev_distance(p) <= 6) { score += 25; break; }
        }
        if (score < best) { best = score; chosen = i; }
    }
    if (chosen < 0) return {GoalKind::Idle};
    auto& b = mem.groups[chosen];
    mem.contract.start(chosen, tc.round, world.distance(chosen, obs.p), b.hp, b.capture);
    return {GoalKind::Farm, chosen};
}
}
