#include "memory.h"
#include "ledger.h"
#include <numeric>

namespace dz {
namespace {
cambc::map::camp_group_state visible_group_state(const Group& group,const TurnContext& tc) {
    // The caller already proved current visibility. Avoid the convenience
    // wrapper's second unbounded spawn-tile visibility scan on large groups.
    // These are official SDK imports; no hidden state is queried.
    tc.guard();
    std::uint32_t state{};
    cambc::detail::check(cambc::detail::sdk_camp_group_state(static_cast<std::uint32_t>(
        static_cast<cambc::handle_camp_group_t>(group.sdk)),&state));
    if (state==1) return cambc::map::camp_group_alive{};
    if (state==2) return cambc::map::camp_group_reward_available{};
    if (state==3) {
        std::int32_t timer{};
        cambc::detail::check(cambc::detail::sdk_camp_group_cooldown(static_cast<std::uint32_t>(
            static_cast<cambc::handle_camp_group_t>(group.sdk)),&timer));
        return cambc::map::camp_group_respawning{timer};
    }
    throw cambc::error(cambc::error_code::api_not_in_vision,"visible camp-group query unavailable");
}
}
void Memory::init(const StaticWorld& world) {
    if (initialized) return;
    groups.resize(world.groups.size()); member_hp.resize(world.groups.size()); hp_version.assign(world.groups.size(),0);
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
    const auto state = visible_group_state(g,tc);
    auto next = groups[index];
#if DZ_ECONOMY_V2
    next.capture_phase=-1;
#endif
    auto hp=member_hp[index];
    GroupSample sample; sample.members.resize(hp.size());
    if (auto* respawn = std::get_if<cambc::map::camp_group_respawning>(&state)) {
        sample.state=GroupState::Respawning; sample.respawn_timer=respawn->timer;
    } else if (std::holds_alternative<cambc::map::camp_group_reward_available>(state)) {
#if DZ_ECONOMY_V2
        const auto capture=g.sdk.capture_state();
        sample.state=GroupState::Reward; sample.capture_timer=capture.timer;
        next.capture_phase=static_cast<int>(capture.state);
#else
        sample.state=GroupState::Reward; sample.capture_timer=g.sdk.capture_state().timer;
#endif
    } else {
        unsigned i = 0;
        for (const auto& camp : g.sdk.camps()) {
            if (!tc.allow(3500)) break;
            // A defeated camp may have no live entity view. Its state is still
            // readable when its static spawn tile is visible; do not confuse
            // an absent live view with an unobserved dead member.
            if (cambc::vision::in_vision(camp.spawn_position())) sample.members[i] = camp.is_dead() ? 0 : camp.health();
            ++i;
        }
    }
    apply_group_sample(next,hp,g.initial_hp,sample,tc.round);
#if DZ_SIEGE || DZ_ECONOMY_V2
    bool topology_changed=(next.state==GroupState::Respawning)!=(groups[index].state==GroupState::Respawning);
    for(unsigned k=0;k<hp.size()&&!topology_changed;++k)topology_changed=(hp[k]>0)!=(member_hp[index][k]>0);
    if(next.state==GroupState::Respawning&&groups[index].state==GroupState::Respawning)
        topology_changed|=(next.ready>static_cast<int>(tc.round))!=(groups[index].ready>static_cast<int>(tc.round));
    if(groups[index].seen+g.sdk.max_respawn_timer()<=static_cast<int>(tc.round)&&
        std::any_of(member_hp[index].begin(),member_hp[index].end(),[](float value){return value<=0;}))
        topology_changed=true; // Freshly re-observed dead cells replace expired uncertainty.
#endif
    tc.guard(); groups[index] = next;
#if DZ_SIEGE || DZ_ECONOMY_V2
    if(topology_changed)++topology_revision;
#endif
    if (hp!=member_hp[index]) ++hp_version[index];
    member_hp[index]=std::move(hp);
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
        // Exponential back-off: a target that keeps failing (unreachable last
        // member, stale memory) must not pull champions across the map forever.
        g.avoid_until = round + (config::avoid_rounds << std::min(g.failures++, 4u));
    }
    contract.objective = -1;
}
}
