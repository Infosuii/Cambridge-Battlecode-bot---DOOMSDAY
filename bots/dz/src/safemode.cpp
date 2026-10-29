#include "safemode.h"

namespace dz {
void quick_home(const StaticWorld& world,const TurnContext& tc,Actuator& quick) {
    tc.guard();
    const auto entry=cambc::fuel_remaining();
    if (!world.ready||entry<=2800) return;
    // Bounded emergency recovery: no observation rebuild, group/enemy scan,
    // allocation proportional to map size, field computation, shopping or cast.
    quick.use_emergency_budget(); // Preserve this turn's move/cast/error history.
    auto& me=cambc::self(); const auto state=me.state();
    bool moved=false,cleared=false;
    int before=-1,after=-1;
    // Publish before movement so a costly successful move cannot leave an old
    // job claim behind. This is still only a soft claim, without a lease.
    cleared=quick.publish(protocol::with_slot(shared_word(),world.slot,{protocol::idle,false}));
    if (!state.is_dead()&&!state.contains(cambc::champion_state::recalling)&&
        !state.contains(cambc::champion_state::submitting_gems)&&!state.contains(cambc::champion_state::teleporting)) {
        const auto p=me.position(); before=world.home.get(p); after=before;
        if (before>0&&before<cambc::distance_field::unreachable&&state.contains(cambc::champion_state::can_move)) {
            const std::array<vec2,8> directions{vec2::north,vec2::north_east,vec2::east,vec2::south_east,
                vec2::south,vec2::south_west,vec2::west,vec2::north_west};
            for (auto delta:directions) { // Fixed stack storage, no route-vector allocation.
                tc.guard();
                if (cambc::fuel_remaining()<=2500) break;
                auto next=p+delta;
                if (!world.walkable(next)||world.home.get(next)>=before||cambc::vision::has_champion(next)||cambc::vision::has_camp(next)||
                    cambc::vision::has_teleport(next)) continue;
                if (quick.move(next)) { moved=true; after=world.home.get(me.position()); break; }
            }
        }
    }
    tc.guard();
#if DZ_TRACE
    // Formatting a diagnostic can itself spend thousands of fuel. Print this
    // compact local record on the next fresh turn, outside the emergency budget.
    recovery_sample={tc.round,entry,cambc::fuel_remaining(),true,moved,cleared,before,after};
#else
    (void)entry; (void)moved; (void)cleared; (void)after;
#endif
}
Goal safe_goal(StaticWorld& world, Memory& mem, const Observation& obs, const TurnContext& tc) {
    if constexpr (config::camp_safety) {
        auto incoming=camp_damage({obs.p.x,obs.p.y},obs.camps);
        if (incoming>0) {
            const auto fuel_start=cambc::fuel_remaining();
            const auto enemy_before=enemy_danger(obs.p,obs);
            auto route=camp_escape(Tile{obs.p.x,obs.p.y},obs.camps,[&](Tile p,int step) {
                vec2 tile{p.x,p.y};
                return world.walkable(tile) && !obs.occupied.is_set(tile) && enemy_danger(tile,obs)<=enemy_before;
            },[&] {
                return tc.allow(1000+150*obs.camps.size()) && fuel_start-cambc::fuel_remaining()<20000;
            });
            if (route.found && must_escape_camps(obs.hp,incoming,route.damage))
                return {GoalKind::Retreat,-1,vec2{route.exit.x,route.exit.y}};
            if (!route.found && obs.hp<=2*incoming) return {GoalKind::Retreat};
        }
        if (!obs.camps_complete) return {GoalKind::Home};
    }
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

    const int occupied_group=world.group_at(obs.p);
    const bool blocks_respawn=occupied_group>=0&&mem.groups[occupied_group].state==GroupState::Respawning;
    int current = mem.contract.objective;
    if (current >= 0) {
        const auto& belief = mem.groups[current];
        const auto dist = world.distance(current, obs.p);
        if (belief.available(tc.round) && mem.contract.progressing(tc.round, dist, belief.hp, belief.capture))
            return {blocks_respawn&&current==occupied_group ? GoalKind::YieldSpawn : GoalKind::Farm, current};
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
        bool complete=true;
        for (const auto& e : obs.enemies) {
            for (unsigned tile=0;tile<g.tiles.size();++tile) {
                if ((tile&15)==0&&!tc.allow(4000)) { complete=false; break; }
                if (e.p.chebyshev_distance(g.tiles[tile])<=6) { score+=25; break; }
            }
            if (!complete) break;
        }
        if (!complete) break; // Never commit a partly scored candidate.
        if (score < best) { best = score; chosen = i; }
    }
    if (chosen < 0) return {blocks_respawn ? GoalKind::YieldSpawn : GoalKind::Idle};
    if (blocks_respawn&&chosen==occupied_group) return {GoalKind::YieldSpawn,chosen};
    auto& b = mem.groups[chosen];
    mem.contract.start(chosen, tc.round, world.distance(chosen, obs.p), b.hp, b.capture);
    return {GoalKind::Farm, chosen};
}
}
