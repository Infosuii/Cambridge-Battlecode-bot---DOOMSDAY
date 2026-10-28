#include "memory.h"
#include <numeric>

namespace dz {
void Memory::init(const StaticWorld& world) {
    if (initialized) return;
    groups.resize(world.groups.size()); member_hp.resize(world.groups.size());
    for (unsigned g = 0; g < groups.size(); ++g) {
        groups[g].hp = world.groups[g].max_hp;
        member_hp[g] = world.groups[g].initial_hp;
    }
    initialized = true;
}
void Memory::observe_group(const StaticWorld& world, int index, const TurnContext& tc) {
    const auto& g = world.groups[index];
    bool visible = false;
    for (auto p : g.tiles) {
        if (!tc.allow(2500)) return;
        if (cambc::vision::in_vision(p)) { visible = true; break; }
    }
    if (!visible) return;
    const auto state = g.sdk.state();
    auto next = groups[index];
    next.seen = tc.round;
    if (auto* respawn = std::get_if<cambc::map::camp_group_respawning>(&state)) {
        next.state = GroupState::Respawning; next.ready = tc.round + respawn->timer;
        next.hp = g.max_hp; next.capture = 65535;
        // A new generation must not inherit last generation's partial damage.
        member_hp[index] = g.initial_hp;
    } else if (std::holds_alternative<cambc::map::camp_group_reward_available>(state)) {
        next.state = GroupState::Reward; next.hp = 0;
        next.capture = g.sdk.capture_state().timer;
    } else {
        unsigned i = 0;
        for (const auto& camp : g.sdk.camps()) {
            if (!tc.allow(3500)) break;
            if (camp.is_visible()) member_hp[index][i] = camp.is_dead() ? 0 : camp.health();
            ++i;
        }
        next.hp = std::accumulate(member_hp[index].begin(), member_hp[index].end(), 0.0f);
        next.state = next.hp + .01f < g.max_hp ? GroupState::Partial : GroupState::Alive;
        next.capture = 65535;
    }
    tc.guard(); groups[index] = next;
}
void Memory::update(const StaticWorld& world, const TurnContext& tc) {
    init(world);
    if (contract.objective >= 0) observe_group(world, contract.objective, tc);
    // Bound the scan independently of unusually large camp counts.
    for (unsigned n = 0; n < 12 && n < groups.size() && tc.allow(5000); ++n) {
        auto index = static_cast<int>(cursor++ % groups.size());
        if (index != contract.objective) observe_group(world, index, tc);
    }
}
void Memory::release(int round) {
    if (contract.objective >= 0) {
        auto& g = groups[contract.objective];
        g.avoid_until = round + (++g.failures > 1 ? 40 : config::avoid_rounds);
    }
    contract.objective = -1;
}
}
