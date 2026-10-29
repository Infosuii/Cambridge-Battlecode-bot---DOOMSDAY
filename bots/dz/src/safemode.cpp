#include "safemode.h"
#include "clear_risk.h"

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
    if (obs.bag > mem.last_bag || obs.submitted > mem.last_submitted) mem.last_income = tc.round;
    mem.last_bag = obs.bag; mem.last_submitted = obs.submitted;
    if (tc.round - mem.last_income > 150 && !mem.legacy(tc.round)) { mem.legacy_until = tc.round + 300; mem.last_income = tc.round; }
    const bool legacy = mem.legacy(tc.round);
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

    auto clear_risk=[&](int index,float extra=0) { return group_clear_risk(world,mem,obs,index,extra); };
    const int occupied_group=world.group_at(obs.p);
    const bool blocks_respawn=occupied_group>=0&&mem.groups[occupied_group].state==GroupState::Respawning;
    int current = mem.contract.objective;
    if (current >= 0) {
        const auto& belief = mem.groups[current];
        const auto dist = world.distance(current, obs.p);
        // Abandon an awake damaging clear the present crew is predicted to
        // lose. A sleeping group cannot hit us; the executor gates waking it.
        bool awake=false;
        if (world.groups[current].strength>0 && belief.state!=GroupState::Reward) {
            const auto awake_tiles=cambc::vision::awake_camp_tiles();
            for (auto t:world.groups[current].tiles) if (awake_tiles.is_set(t)) { awake=true; break; }
        }
        if (awake && !legacy) {
            unsigned crew=1;
            for (const auto& a:obs.allies) if (a.hp>0 && a.p.chebyshev_distance(obs.p)<=4) ++crew;
            auto risk=clear_risk(current,crew_strength(obs,obs.p,4));
            if (!risk.complete() || obs.hp<=1.1*risk.damage*crew_share(crew)) { mem.release(tc.round); current=-1; }
        }
        if (current>=0 && belief.available(tc.round) && mem.contract.progressing(tc.round, dist, belief.hp, belief.capture))
            return {blocks_respawn&&current==occupied_group ? GoalKind::YieldSpawn : GoalKind::Farm, current};
        if (current>=0) {
            if (!belief.available(tc.round)) mem.contract.objective = -1;
            else mem.release(tc.round);
        }
    }
    if (tc.round < mem.idle_until && obs.hp >= .9f * obs.max_hp) return {GoalKind::Idle};
    auto word = shared_word();
    float best = 1e30f; int chosen = -1;
    for (unsigned i = 0; i < world.groups.size(); ++i) {
        if (!tc.allow(3500)) break;
        const auto& belief = mem.groups[i]; const auto& g = world.groups[i];
        if (!belief.available(tc.round)) continue;
        const int dist = world.distance(i, obs.p);
        if (dist >= 65535 || (!g.field && dist > 30)) continue;
        int claims = 0;
        for (unsigned slot = 0; slot < world.allies.size() && slot < protocol::slots; ++slot)
            if (slot != world.slot && i < 112 && protocol::slot(word, slot).objective == i) ++claims;
        // Reward per round of travel, clear and capture, over solo-survivable
        // groups only. A heuristic rate, not the unvalidated ObjModel/auction.
        const float value=(g.sdk.gem_value()+.1f*g.sdk.gold_value())/(1.f+claims);
        if (value<=0) continue;
        const float fixed=dist+cambc::constants::capture_time+2.f;
        if (-value/fixed>=best) continue; // Cannot win even with a free clear.
        float clear_rounds=0;
        if (legacy) {
            // The pre-gate nearest-group score, used only while starving.
            float score = dist + .03f * g.strength + (g.cluster ? claims * 10.f : claims * 2.f) - (belief.state == GroupState::Reward ? 8.f : 0.f);
            if (score < best) { best = score; chosen = i; }
            continue;
        }
        if (belief.state!=GroupState::Reward) {
            auto risk=clear_risk(static_cast<int>(i));
            if (!risk.complete() || (g.strength>0 && !clear_survivable(risk,obs.hp,obs.max_hp))) continue;
            clear_rounds=risk.attacks+.25f*g.tiles.size();
        }
        float score=-value/(fixed+clear_rounds);
        bool complete=true;
        for (const auto& e : obs.enemies) {
            for (unsigned tile=0;tile<g.tiles.size();++tile) {
                if ((tile&15)==0&&!tc.allow(4000)) { complete=false; break; }
                if (e.p.chebyshev_distance(g.tiles[tile])<=6) { score*=.33f; break; }
            }
            if (!complete) break;
        }
        if (!complete) break; // Never commit a partly scored candidate.
        if (score < best) { best = score; chosen = i; }
    }
    // One crew decision per team: the lowest living slot leads. A follower
    // that cannot solo the leader's damaging target joins it.
    unsigned leader=world.slot;
    for (unsigned slot=0;slot<world.allies.size()&&slot<protocol::slots;++slot)
        if (slot==world.slot || protocol::slot(word,slot).objective!=protocol::dead) { leader=slot; break; }
    if (!legacy && leader!=world.slot && !blocks_respawn && obs.hp >= .9f * obs.max_hp) {
        const int job=protocol::slot(word,leader).objective;
        if (job<static_cast<int>(world.groups.size()) && world.groups[job].strength>0 && mem.groups[job].available(tc.round) &&
            mem.groups[job].state!=GroupState::Reward && world.distance(job,obs.p)<65535 && job!=chosen) {
            auto solo=clear_risk(job);
            if (!clear_survivable(solo,obs.hp,obs.max_hp)) {
                auto& b=mem.groups[job];
                mem.contract.start(job,tc.round,world.distance(job,obs.p),b.hp,b.capture,config::crew_window);
                return {GoalKind::Farm,job};
            }
        }
    }
    if (!legacy && leader==world.slot && !blocks_respawn && obs.hp >= .9f * obs.max_hp) {
        // Crew pass (leader only): damaging groups no one can solo. Every healthy champion
        // ranks them by static home distance, so the team converges on one
        // target; an ally's claim strongly attracts the rest. Assumes living
        // allies hit as hard as we do and share the group's damage. Taken when
        // its per-champion rate beats our best solo rate. The executor's wake
        // gate checks the crew actually present before the first attack.
        unsigned living=1;
        for (unsigned slot=0;slot<world.allies.size()&&slot<protocol::slots;++slot)
            if (slot!=world.slot && protocol::slot(word,slot).objective!=protocol::dead) ++living;
        const float extra=(living-1)*obs.strength*obs.camp_damage;
        float crew_best=1e30f; int crew_choice=-1;
        for (unsigned i=0;i<world.groups.size()&&living>=2;++i) {
            if (!tc.allow(3500)) break;
            const auto& belief=mem.groups[i]; const auto& g=world.groups[i];
            if (g.strength<=0 || belief.state==GroupState::Reward || !belief.available(tc.round)) continue;
            if (world.distance(i,obs.p)>=65535) continue;
            const int home=world.home.get(g.tiles.front());
            if (home>=cambc::distance_field::unreachable) continue;
            int claims=0;
            for (unsigned slot=0;slot<world.allies.size()&&slot<protocol::slots;++slot)
                if (slot!=world.slot && i<112 && protocol::slot(word,slot).objective==i) ++claims;
            const float value=(g.sdk.gem_value()+.1f*g.sdk.gold_value())*(claims?4.f:1.f)/living;
            const float fixed=home+cambc::constants::capture_time+2.f;
            if (value<=0 || -value/fixed>=crew_best) continue;
            auto risk=clear_risk(static_cast<int>(i),extra);
            // An ally's claim already passed its own crew check; a weak hitter
            // pricing the crew with its own strength must not refuse to join.
            if (!claims && !clear_survivable(risk,obs.hp,obs.max_hp,crew_share(living))) continue;
            if (!risk.complete()) continue;
            const float score=-value/(fixed+risk.attacks);
            if (score<crew_best) { crew_best=score; crew_choice=static_cast<int>(i); }
        }
        if (crew_choice>=0 && crew_best<best) {
            auto& b=mem.groups[crew_choice];
            mem.contract.start(crew_choice,tc.round,world.distance(crew_choice,obs.p),b.hp,b.capture,config::crew_window);
            return {GoalKind::Farm,crew_choice};
        }
    }
    if (chosen < 0) {
        if (blocks_respawn) return {GoalKind::YieldSpawn};
        // Nothing is survivable now: healing at home widens the feasible set.
        if (obs.hp < .9f * obs.max_hp) return {GoalKind::Home};
        mem.idle_until = tc.round + 4;
        return {GoalKind::Idle};
    }
    if (blocks_respawn&&chosen==occupied_group) return {GoalKind::YieldSpawn,chosen};
    auto& b = mem.groups[chosen];
    mem.contract.start(chosen, tc.round, world.distance(chosen, obs.p), b.hp, b.capture);
    return {GoalKind::Farm, chosen};
}
}
