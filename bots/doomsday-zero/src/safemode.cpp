#include "safemode.h"
#include "clear_risk.h"
#include "economy.h"
#include "engage.h"
#include "siege.h"
#include "crew.h"
#include "lifecycle.h"
#if DZ_ECONOMY_V2
#include "allocation.h"
#endif
#if DZ_CLEAR_TIME_CLOCK
#include "clear_clock.h"
#endif
#include "team_plan.h"
#include "market.h"
#include "v81_assess.h"

namespace dz {
void quick_home(const StaticWorld& world,const TurnContext& tc,Actuator& quick) {
    tc.guard();
    const auto entry=fuel_left();
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
                if (fuel_left()<=2500) break;
                auto next=p+delta;
                if (!world.walkable(next)||world.home.get(next)>=before||cambc::vision::has_champion(next)||cambc::vision::has_camp(next)||
                    cambc::vision::has_teleport(next)) continue;
                if (quick.move(next)) { moved=true; after=world.home.get(me.position()); break; }
            }
        }
    }
    tc.guard();
#if DZ_TRACE
    { ::dz::TraceScope dz_trace_scope;
    // Formatting a diagnostic can itself spend thousands of fuel. Print this
    // compact local record on the next fresh turn, outside the emergency budget.
    recovery_sample={tc.round,entry,cambc::fuel_remaining(),true,moved,cleared,before,after};
    }
#else
    (void)entry; (void)moved; (void)cleared; (void)after;
#endif
}
#if DZ_ECONOMY_V2
static Goal strategic_goal(StaticWorld& world, Memory& mem, const Observation& obs, const TurnContext& tc) {
#else
Goal safe_goal(StaticWorld& world, Memory& mem, const Observation& obs, const TurnContext& tc) {
#endif
#if DZ_ECONOMY_V2
    const auto planner_start=fuel_left();
    mem.track_enemies(obs,tc.round);
    if(auto goal=neutral_recovery(world,mem,obs,tc))return *goal;
#endif
    if constexpr (config::camp_safety) {
        auto incoming=camp_damage({obs.p.x,obs.p.y},obs.camps);
        if (incoming>0) {
            const auto fuel_start=fuel_left();
            const auto enemy_before=enemy_danger(obs.p,obs);
            auto route=camp_escape(Tile{obs.p.x,obs.p.y},obs.camps,[&](Tile p,int step) {
                vec2 tile{p.x,p.y};
                return world.walkable(tile) && !obs.is_occupied(tile) && enemy_danger(tile,obs)<=enemy_before;
            },[&] {
                return tc.allow(1000+150*obs.camps.size()) && fuel_start-fuel_left()<20000;
            });
            if (route.found && must_escape_camps(obs.hp,incoming,route.damage)) {
#if DZ_ECONOMY_V2
                mem.neutral_escape.arm(tc.round,{obs.p.x,obs.p.y},route);
#endif
                return {GoalKind::Retreat,-1,vec2{route.exit.x,route.exit.y}};
            }
            if (!route.found && obs.hp<=2*incoming) return {GoalKind::Retreat};
        }
        if (!obs.camps_complete) return {GoalKind::Home};
    }
#if DZ_STYLE == 1
    {
        const SeenChampion* prey=nullptr;
        for (const auto& e:obs.enemies)
            if (!world.in_enemy_spawn(e.p) && (!prey || obs.p.chebyshev_distance(e.p)<obs.p.chebyshev_distance(prey->p))) prey=&e;
        if (prey && obs.hp>=.25f*obs.max_hp) return {GoalKind::Fight,-1,prey->p};
        if (obs.hp>=.6f*obs.max_hp && !world.altars.empty() && obs.bag<config::bank_bag) {
            static int target=-1;
            if (target<0) {
                const auto spawns=cambc::map::spawn_region(cambc::team::enemy).positions();
                int best=1<<30;
                for (unsigned a=0;a<world.altars.size()&&!spawns.empty();++a) {
                    const int d=static_cast<int>(world.altars[a].tile.chebyshev_distance(spawns.front()));
                    if (d<best) { best=d; target=static_cast<int>(a); }
                }
            }
            if (target>=0 && obs.p.chebyshev_distance(world.altars[target].tile)>3) return {GoalKind::Fight,-1,world.altars[target].tile};
        }
    }
#endif
#if DZ_STYLE == 2
    // Turtle: leave any visible enemy, never chase.
    for (const auto& e:obs.enemies) if (obs.p.chebyshev_distance(e.p)<=8) return {GoalKind::Retreat};
#endif
    if (obs.bag > mem.last_bag || (DZ_PERSONAL_PROGRESS||DZ_ECONOMY_V2 ? obs.gold > mem.last_gold : obs.submitted > mem.last_submitted)) mem.last_income = tc.round;
    mem.last_bag = obs.bag; mem.last_submitted = obs.submitted;
    mem.last_gold=obs.gold;
    if (
#if DZ_ECONOMY_V2
        economy::starved(tc.round,mem.last_income,mem.last_work)
#else
        tc.round-mem.last_income>150
#endif
        &&!mem.legacy(tc.round)) { mem.legacy_until=tc.round+300;mem.last_income=tc.round; }
    bool legacy = mem.legacy(tc.round);
#if DZ_HAS(EE)
    if (DZ_ON(EE)) mem.remember_enemies(obs,tc.round);
#endif
    // Local fight: we and allies within 6 against visible enemies within 8.
    // Enemy HP carries a 25% margin for unseen reinforcements and spells.
    // Win -> engage the weakest nearby enemy (this also joins allies' fights);
    // lose -> leave before contact, or retreat once in reach.
#if DZ_ECONOMY_V2
    // A speculative rollout must leave room to choose and execute income.
    // Previously a 40k partial combat forecast was followed by a 25k auction,
    // starving the executor on corners. Keep the bounded local check below.
    const auto engagement=engagement_goal(world,mem,obs,
#if DZ_LIFECYCLE
        tc.keep(30000)
#else
        tc
#endif
    );
    if(engagement&&engagement->kind!=GoalKind::Idle)return *engagement;
    if(!engagement) {
#else
    {
#endif
        std::array<Fighter,fight_units> ours{}, theirs{};
        std::size_t n_ours=1, n_theirs=0;
        ours[0]={obs.hp,obs.strength};
        for (const auto& a : obs.allies) {
#if DZ_ECONOMY_V2 && DZ_LIFECYCLE
            const bool present=std::any_of(obs.enemies.begin(),obs.enemies.end(),[&](const auto& enemy){return
                enemy.p.chebyshev_distance(obs.p)<=8&&a.p.chebyshev_distance(enemy.p)<=a.range+1;});
            if(!present)continue;
#endif
            if (a.hp>0 && n_ours<fight_units && obs.p.chebyshev_distance(a.p) <= 6) ours[n_ours++]={a.hp,a.strength};
        }
        bool reach=false, near=false; const SeenChampion* focus=nullptr;
        for (const auto& e : obs.enemies) {
            const int d=static_cast<int>(obs.p.chebyshev_distance(e.p));
            if (d > (DZ_ON(EE) ? DZ_EE_SCAN : 8) || n_theirs>=fight_units) continue;
            theirs[n_theirs++]={1.25f*e.hp,e.strength};
            if (d <= e.range + 1) reach=true;
            if (d <= e.range + (DZ_ON(EE) ? DZ_EE_NEAR : 3)) near=true;
            if (d <= 5 && !world.in_enemy_spawn(e.p) && (!focus || e.hp < focus->hp)) focus=&e;
        }
        DZ_PROF('f');
#if DZ_HAS(EE2)
        if (DZ_ON(EE2) && n_theirs) {
            // V-M2 model: the old !won rule retreated from ~62% of contacts while 7% ended in death.
            std::array<Fighter,fight_units> close{}; std::size_t n_close=0; int nearest=99; float reach_damage=0;
            for (const auto& e : obs.enemies) {
                const int d=static_cast<int>(obs.p.chebyshev_distance(e.p));
                if (d>8 || n_close>=fight_units) continue;
                close[n_close++]={e.hp,e.strength}; nearest=std::min(nearest,d);
                if (d<=2) reach_damage+=e.strength;
            }
            if (n_close) {
                const float z=death_logit(std::span<const Fighter>(ours.data(),n_ours),std::span<const Fighter>(close.data(),n_close),
                    obs.hp/std::max(1.f,obs.max_hp),nearest,reach_damage);
                const bool bankable=bank_now(obs.bag,cambc::distance_field::unreachable,obs.submitted,cambc::constants::winning_gems);
                if (z > (DZ_ON(EE2_BOLD) ? -0.8473f : -1.7346f)) return {GoalKind::Retreat}; // logit(.30) / logit(.15)
                if (focus && z < -3.1781f && obs.hp>=.3f*obs.max_hp && !bankable && // logit(.04)
                    simulate_fight(std::span<const Fighter>(ours.data(),n_ours),std::span<const Fighter>(theirs.data(),n_theirs)).won())
                    return {GoalKind::Fight,-1,focus->p};
                n_theirs=0; // Neither: keep working; the executor still takes local attacks.
            }
        }
#endif
#if DZ_HAS(ASSESS)
        if (DZ_ON(ASSESS) && n_theirs && tc.allow(14000)) {
            // v81hl's learned fight-or-run value (engine counterfactuals): a confident +-5 gem prediction decides;
            // otherwise the incumbent rule below stands.
            int nearest=99; const SeenChampion* close=nullptr;
            for (const auto& e : obs.enemies) {
                const int d=static_cast<int>(obs.p.chebyshev_distance(e.p));
                if (d<nearest && !world.in_enemy_spawn(e.p)) { nearest=d; close=&e; }
            }
            if (close && nearest<=4) {
                const float value=v81::assess_fight(obs,tc.round);
                const bool bankable=bank_now(obs.bag,cambc::distance_field::unreachable,obs.submitted,cambc::constants::winning_gems);
                if (value>5.f && obs.hp>=.3f*obs.max_hp && !bankable) return {GoalKind::Fight,-1,(focus?focus:close)->p};
                // Mode 1 (v81hl's +-5): deaths 18 -> 15 a game but margin -57 vs m3 (it leaves too many contacts).
                if (DZ_ASSESS_MODE!=2 && value<(DZ_ASSESS_MODE==3 ? -15.f : -5.f)) return {GoalKind::Retreat};
            }
        }
#endif
#if DZ_HAS(EE3)
        // Surplus only: after EE3 (~15k with DZ_FAST_FIGHT) the executor must still afford a fresh whole-map field.
        if (DZ_ON(EE3) && n_theirs && tc.allow(world.field_budget()+25000)) {
            // B1 v2: expected exchange from two calibrated contact models: ee_model (this body dies within 4 rounds)
            // and ee_enemy_model (a given enemy dies within 4, from its own side). Only adds engagements with a
            // positive expected exchange; everything else falls through to the incumbent fight/retreat rule. v1
            // (dz-ee3-*-01) also overrode retreats and kept working below P 0.15: deaths 19.0 -> 21.1, -12.8 banked.
            std::array<Fighter,fight_units> close{}; std::size_t n_close=0; int nearest=99; float reach_damage=0;
            for (const auto& e : obs.enemies) {
                const int d=static_cast<int>(obs.p.chebyshev_distance(e.p));
                if (d>8 || n_close>=fight_units) continue;
                close[n_close++]={e.hp,e.strength}; nearest=std::min(nearest,d);
                if (d<=2) reach_damage+=e.strength;
            }
            if (n_close) {
                const float pd=sigmoid(death_logit(std::span<const Fighter>(ours.data(),n_ours),std::span<const Fighter>(close.data(),n_close),
                    obs.hp/std::max(1.f,obs.max_hp),nearest,reach_damage));
                DZ_PROF('3');
                const float tempo=.25f*cambc::constants::respawn_time; // Rounds of lost work at DZ's ~0.25 gems/round.
                const float death_cost=obs.bag+tempo;
                float best_ev=-1e30f; const SeenChampion* target=nullptr; int priced=0;
                for (const auto& e : obs.enemies) {
                    if (static_cast<int>(obs.p.chebyshev_distance(e.p))>5 || world.in_enemy_spawn(e.p) || priced>=2) continue;
                    ++priced;
                    std::array<Fighter,fight_units> side{}, foes{}; std::size_t n_side=1, n_foes=0; int en=99; float er=0;
                    side[0]={e.hp,e.strength};
                    for (const auto& o : obs.enemies)
                        if (&o!=&e && o.hp>0 && n_side<fight_units && o.p.chebyshev_distance(e.p)<=6) side[n_side++]={o.hp,o.strength};
                    auto add=[&](vec2 p,float hp,float strength) {
                        const int d=static_cast<int>(p.chebyshev_distance(e.p));
                        if (d>8 || n_foes>=fight_units) return;
                        foes[n_foes++]={hp,strength}; en=std::min(en,d);
                        if (d<=2) er+=strength;
                    };
                    add(obs.p,obs.hp,obs.strength);
                    for (const auto& a : obs.allies) if (a.hp>0) add(a.p,a.hp,a.strength);
                    const float pk=sigmoid(contact_logit(std::span<const Fighter>(side.data(),n_side),std::span<const Fighter>(foes.data(),n_foes),
                        e.hp/std::max(1.f,e.max_hp),en,er,ee_enemy_model::intercept,ee_enemy_model::weights));
                    const float carried=tc.allow(3000)?static_cast<float>(e.sdk.gem_count()):0.f;
                    const float ev=pk*(carried+gold_weight(tc.round)*cambc::constants::kill_gold+tempo)-pd*death_cost;
                    if (ev>best_ev) { best_ev=ev; target=&e; }
                }
                DZ_PROF('4');
                const bool bankable=bank_now(obs.bag,cambc::distance_field::unreachable,obs.submitted,cambc::constants::winning_gems);
                if (target && best_ev>0 && pd<.3f && obs.hp>=.3f*obs.max_hp && !bankable) return {GoalKind::Fight,-1,target->p};
            }
        }
#endif
        if (n_theirs) {
            auto fight=simulate_fight(std::span<const Fighter>(ours.data(),n_ours),std::span<const Fighter>(theirs.data(),n_theirs));
            DZ_PROF('g');
            // Banking already outranks farming below. Test whether it should
            // also outrank a voluntary fight: the executor still takes legal
            // local attacks, and an unsafe losing contact can still retreat.
            const bool bankable=DZ_CARRIER_BANK_PRIORITY &&
                bank_now(obs.bag,cambc::distance_field::unreachable,obs.submitted,cambc::constants::winning_gems);
            bool engage_won=fight.won();
#if DZ_HAS(HOME) || DZ_HAS(FIGHT) || DZ_HAS(TURTLE)
            if (const float k=aggression(); k!=1.f && focus) {
                // Team plan: engage as if our side were k times as strong; the retreat test keeps the plain result.
                std::array<Fighter,fight_units> scaled=ours;
                for (std::size_t i=0;i<n_ours;++i) scaled[i].damage*=k;
                engage_won=simulate_fight(std::span<const Fighter>(scaled.data(),n_ours),std::span<const Fighter>(theirs.data(),n_theirs)).won();
            }
#endif
            if (engage_won && focus && obs.hp >= .3f * obs.max_hp && !bankable && DZ_STYLE != 2) {
                bool engage=true;
#if DZ_FIGHT_GEM_VALUE
                // Query only the already-visible chosen focus, after the
                // existing fight/survival/carrier checks. Test immediate gem
                // denial as a reason to chase rather than price kill gold.
                engage=tc.allow(2000)&&focus->sdk.gem_count()>0;
#endif
#if DZ_ENGAGE_IN_RANGE || (DZ_ECONOMY_V2 && DZ_LIFECYCLE)
                // The old simulation gave every ally within six instant DPS,
                // even when its own attack range could not reach the focus.
                // Only filter voluntary engagements. Keep the established
                // losing-contact retreat decision unchanged below.
                std::array<Fighter,fight_units> present{};std::size_t n_present=1;
                present[0]=ours[0];
                for(const auto& a:obs.allies)if(a.hp>0&&n_present<fight_units&&
                    obs.p.chebyshev_distance(a.p)<=6&&a.p.chebyshev_distance(focus->p)<=a.range)
                    present[n_present++]={a.hp,a.strength};
                engage=engage&&tc.allow(6000)&&simulate_fight(std::span<const Fighter>(present.data(),n_present),
                    std::span<const Fighter>(theirs.data(),n_theirs)).won();
#endif
                if(engage)return {GoalKind::Fight,-1,focus->p};
            }
            if (!fight.won() && (DZ_ON(EE) ? near : reach)) {
#if DZ_HAS(EE_REGROUP) || (DZ_ECONOMY_V2 && DZ_LIFECYCLE)
                if (DZ_ON(EE_REGROUP)||DZ_LIFECYCLE) {
                // A same-speed chaser keeps hitting a body that flees alone (00ambush R204-221
                // replay); run toward help instead, where the joint fight can be won.
                const SeenChampion* help=nullptr;
                for (const auto& a:obs.allies) {
                    if (a.hp<.5f*a.max_hp || obs.p.chebyshev_distance(a.p)>12 || obs.p.chebyshev_distance(a.p)<2) continue;
#if DZ_ECONOMY_V2 && DZ_LIFECYCLE
                    if(enemy_danger(a.p,obs)>enemy_danger(obs.p,obs))continue;
#endif
                    if (!help || obs.p.chebyshev_distance(a.p)<obs.p.chebyshev_distance(help->p)) help=&a;
                }
                if (help) return {GoalKind::Retreat,-1,help->p};
                }
#endif
                return {GoalKind::Retreat};
            }
        }
    }
    DZ_PROF('F');
#if DZ_ECONOMY_V2 && DZ_LIFECYCLE
    if(!mem.siege_task.active())return lifecycle_goal(world,mem,obs,tc);
#endif
#if DZ_ECONOMY_V2
    if(obs.bag>0&&obs.enemies.empty())for(unsigned a=0;a<world.altars.size();++a)
        if(obs.p.chebyshev_distance(world.altars[a].tile)<=cambc::constants::submit_gems_range) {
            const auto admission=bank_admission(world,mem,obs,a,tc);
            if(admission!=BankAdmission::Denied) {
                // Serve a real carrier already at a submission endpoint before
                // optional access, equipment or auction work spends its budget.
                mem.contract.objective=-1;mem.leave_crew();mem.delivery_trip={};mem.early_opening={};
                return {GoalKind::Bank,static_cast<int>(a)};
            }
        }
    if(auto goal=yield_siege_lane(world,mem,obs,tc))return *goal;
    // A live visit owns the execution budget before speculative altar/channel
    // searches. Rebuilding those first could keep a recovered worker returning
    // Home forever without advancing or timing out its existing approach.
    if(mem.siege_task.active())if(auto goal=siege_goal(world,mem,obs,tc,false))return *goal;
    if(mem.openings.size()!=world.altars.size()&&obs.enemies.empty()&&world.home.get(obs.p)==0) {
        quote_opening(world,mem,obs,tc);return {GoalKind::Home};
    }
#endif
    // Bank only at an altar whose gating groups are not alive. A gated altar
    // used to send everyone to bank, find no free tile, refuse to wake the gate
    // and re-select Bank forever (DZ_STUCK, 01boss-battle).
    auto altar_open=[&](unsigned a) {
        const auto& gm=world.altars[a].gate_members;
        if (gm.empty()) return true;
        for (auto [g,k]:gm) {
            const auto st=mem.groups[g].state;
            if (st==GroupState::Reward || st==GroupState::Respawning) return true;
            if (k<static_cast<int>(mem.member_hp[g].size()) && mem.member_hp[g][k]<=0) return true;
        }
        return false;
    };
    int altar = -1, altar_distance = 65535, gated_altar = -1, gated_distance = 65535;
#if DZ_ECONOMY_V2
    // Speculative delivery searches cannot consume the next executable income
    // decision. An actual carrier receives priority; an empty worker retains
    // enough headroom for its auction and the executor.
    const bool priced_delivery=std::any_of(mem.bank_access.begin(),mem.bank_access.end(),[&](const auto& view){return
        view.plan.complete()&&view.current(tc.round,mem.topology_revision,mem.threat_revision,obs.max_hp,obs.camp_factor,view.channel);});
    // Until a delivery quote exists, alternate the two expensive dependencies.
    // Always protecting the full auction prevented the first bank quote from
    // ever running; always pricing access prevented the first income bid.
    const bool access_turn=obs.bag>0||(!priced_delivery&&((tc.round+world.slot)&1u)==0);
    const auto access_tc=tc.keep(access_turn?12000:40000);
    // Give the fair forecast slot its budget before any cold physical route.
    // With the old ordinal scan, a far altar could consume that budget on every
    // turn and permanently starve the near altar on the opposite map side.
    if(!world.altars.empty())bank_access(world,mem,obs,mem.bank_forecast_cursor%world.altars.size(),access_tc);
#endif
#if DZ_SIEGE || DZ_ECONOMY_V2
    mem.route_gate_count=0;
#endif
    for (unsigned a = 0; a < world.altars.size(); ++a) {
        int d = world.altar_distance(a, obs.p);
        bool open=altar_open(a);
#if DZ_SIEGE || DZ_ECONOMY_V2
        bool known=false;
#if DZ_ECONOMY_V2
        if(a<mem.access_fields.size()) {
            const auto& field=mem.access_fields[a];
            if(field.revision==mem.topology_revision&&field.expires>static_cast<int>(tc.round)) {
                open=!field.closed&&field.field&&field.field->get(obs.p)<65535;known=true;
            }
        }
#endif
        if(!known) {
            const auto route=altar_route(world,mem,obs,a,
#if DZ_ECONOMY_V2
                access_tc
#else
                tc
#endif
                );
            if(route.status==access::Status::Blocked) {
                if(const auto reachable=altar_access(world,mem,obs,a,
#if DZ_ECONOMY_V2
                    access_tc
#else
                    tc
#endif
                    ))open=*reachable;
                if(mem.route_gate_count<mem.route_gates.size())mem.route_gates[mem.route_gate_count++]={route.blocker.group,route.blocker.member};
            } else if(route.status==access::Status::Clear)open=true;
            else if(route.status==access::Status::Unreachable)continue;
        }
#endif
#if DZ_ECONOMY_V2
        const auto* delivery=bank_access(world,mem,obs,a,access_tc);
        open=open&&delivery&&delivery->plan.quality==bank::Quality::Bounded;
        if(delivery)for(unsigned i=0;i<delivery->plan.count&&mem.route_gate_count<mem.route_gates.size();++i) {
            const auto& threat=delivery->threats[delivery->plan.cuts[i]];
            const std::pair<int,int> member{threat.group,threat.member};
            if(std::find(mem.route_gates.begin(),mem.route_gates.begin()+mem.route_gate_count,member)==mem.route_gates.begin()+mem.route_gate_count)
                mem.route_gates[mem.route_gate_count++]=member;
        }
#endif
        if (!open) { if (d < gated_distance) { gated_altar = a; gated_distance = d; } continue; }
        if (d < altar_distance) { altar = a; altar_distance = d; }
    }
#if DZ_TRACE
    { ::dz::TraceScope dz_trace_scope;
    if (world.slot==0 && tc.round%200==20) for (unsigned a=0;a<world.altars.size();++a) {
        ::dz::trace("DZ_ALTAR round=%u altar=%u tile=%d,%d open=%d gates=%zu",tc.round,a,world.altars[a].tile.x,world.altars[a].tile.y,altar_open(a),world.altars[a].gate_members.size());
        for (auto [g,k]:world.altars[a].gate_members) ::dz::trace(" g%d/m%d:st%d:hp%.0f:str%.0f",g,k,static_cast<int>(mem.groups[g].state),
            k<static_cast<int>(mem.member_hp[g].size())?mem.member_hp[g][k]:-1.f,world.groups[g].strength);
        ::dz::trace("\n");
    }
    }
#endif
    // Every altar gated by a live group (only 01boss-battle and 02guardians in
    // the pool): the reachability logic above cannot bank at all, so fall back
    // to the pre-gate policy, whose blocked-altar path clears the gate by
    // repeated waves. A dedicated siege plan is map-specific work, deferred.
#if DZ_HAS(RING_GATES) && !DZ_ECONOMY_V2
    if (DZ_ON(RING_GATES) && altar < 0 && gated_altar >= 0 && !world.altars[gated_altar].gates.empty() && obs.hp >= .5f*obs.max_hp) {
        int pick=-1; float weakest=1e30f;
        unsigned living=1;
        {
            const auto word=shared_word();
            for (unsigned slot=0;slot<world.allies.size()&&slot<protocol::slots;++slot)
                if (slot!=world.slot && protocol::slot(word,slot).objective!=protocol::dead) ++living;
        }
        for (int g:world.altars[gated_altar].gates) {
            if (!mem.groups[g].available(tc.round) || world.distance(g,obs.p)>=cambc::distance_field::unreachable) continue;
            if (world.groups[g].strength>=weakest) continue;
            // Only a gate the whole living team can survive clearing (tank rule shares damage).
            const auto risk=group_clear_risk(world,mem,obs,g,(living-1)*obs.strength*obs.camp_damage);
            if (!clear_survivable(risk,obs.hp,obs.max_hp,crew_share(living))) continue;
            weakest=world.groups[g].strength; pick=g;
        }
        if (pick>=0) {
            if (mem.contract.objective!=pick) {
                auto& b=mem.groups[pick];
                mem.contract.start(pick,tc.round,world.distance(pick,obs.p),b.hp,b.capture,config::crew_window);
            }
            return {GoalKind::Farm,pick};
        }
    }
#endif
#if DZ_SIEGE || DZ_ECONOMY_V2
    // The economy chooses NEW openings against income and gear. A live siege
    // keeps its checked strike/withdraw/recovery controller until completion.
    if(!DZ_ECONOMY_V2||mem.siege_task.active())
        if(auto goal=siege_goal(world,mem,obs,tc,altar>=0))return *goal;
#endif
#if DZ_ECONOMY_V2
    // Finish the bounded delivery itinerary before optional shop forecasts can
    // consume its budget. Each call advances one path slice or cut price.
    if(altar<0&&obs.enemies.empty())quote_opening(world,mem,obs,access_tc);
    if(auto goal=economic_goal(world,mem,obs,tc,altar,altar_distance))return *goal;
    // An interrupted expensive forecast cannot immediately launch another full
    // search. Preserve execution/communication fuel and the proven contract.
    if(planner_start-fuel_left()>32000||!tc.allow(18000)) {
        const int job=mem.contract.objective;
        if(job>=0&&mem.groups[job].available(tc.round))return {GoalKind::Farm,job};
        return {GoalKind::Home};
    }
#endif
    if (altar < 0 && gated_altar >= 0) {
#if !(DZ_SIEGE || DZ_ECONOMY_V2)
        if (!legacy) mem.legacy_until = tc.round + 100;
        legacy = true;
        altar = gated_altar; altar_distance = gated_distance;
#endif
    }
    if (altar >= 0 && bank_now(obs.bag, altar_distance, obs.submitted, cambc::constants::winning_gems)) return {GoalKind::Bank, altar};
    if (obs.hp < .3f * obs.max_hp || obs.gold >= 150) return {GoalKind::Home};

    DZ_PROF('A');
    auto clear_risk=[&](int index,float extra=0) { return group_clear_risk(world,mem,obs,index,extra); };
    const int occupied_group=world.group_at(obs.p);
    const bool blocks_respawn=occupied_group>=0&&mem.groups[occupied_group].state==GroupState::Respawning;
#if DZ_HAS(CREWS)
    // Z11 v1: slots pair as (0,1), (2,3), ...; the lower living slot leads. The
    // follower joins the leader's group job while healthy; banking, recovery and
    // fight/retreat decisions above stay individual. Unvalidated hypothesis.
    unsigned crew_size=1;
    {
        const auto word=shared_word();
        unsigned mate=world.slot^1u;
        bool mate_alive=mate<world.allies.size()&&mate<protocol::slots&&protocol::slot(word,mate).objective!=protocol::dead;
        if (DZ_ON(CREW_ALL)) {
            // Whole team: the lowest living slot leads; everyone else follows it.
            mate_alive=false;
            for (unsigned slot=0;slot<world.allies.size()&&slot<protocol::slots;++slot)
                if (slot!=world.slot && protocol::slot(word,slot).objective!=protocol::dead) {
                    ++crew_size;
                    if (!mate_alive || slot<mate) { if (slot<world.slot||!mate_alive) mate=slot; mate_alive=true; }
                }
            if (mate_alive && mate>world.slot) mate=world.slot; // This body leads.
            mate_alive=mate_alive&&mate!=world.slot;
        } else crew_size+=mate_alive;
        if (DZ_ON(CREWS) && mate_alive && mate<world.slot && !legacy && !blocks_respawn && obs.hp>=.6f*obs.max_hp) {
            const int job=protocol::slot(word,mate).objective;
            if (protocol::is_group_code(job) && job<static_cast<int>(world.groups.size()) && mem.groups[job].available(tc.round) &&
                world.distance(job,obs.p)<cambc::distance_field::unreachable) {
                if (mem.contract.objective!=job) {
                    auto& b=mem.groups[job];
                    mem.contract.start(job,tc.round,world.distance(job,obs.p),b.hp,b.capture,config::crew_window);
                }
                return {GoalKind::Farm,job};
            }
        }
    }
#endif
    int current = mem.contract.objective;
#if DZ_ECONOMY_V2
    const auto reservation_word=shared_word();
    auto crew_reserved=[&](int group) {
        const auto owner=mem.team.cohort(group,reservation_word,tc.round,world.allies.size());
        return owner.valid&&!(owner.members&(1u<<world.slot));
    };
    if(current>=0&&crew_reserved(current)){mem.contract.objective=-1;mem.leave_crew();current=-1;}
#endif
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
        // Standing on the cleared group is progress: a fresh capture takes the
        // configured time plus an initialization phase in which the timer does
        // not fall, which outlasted the six-round window and abandoned captures
        // one round before completion. Bounded so a contested tile releases.
        if (current>=0 && belief.state==GroupState::Reward && world.group_at(obs.p)==current) {
            if (mem.contract.onsite_since<0) mem.contract.onsite_since=tc.round;
            if (tc.round-mem.contract.onsite_since <= 2*cambc::constants::capture_time+4) mem.contract.checked=tc.round;
        } else if (current>=0) mem.contract.onsite_since=-1;
        // Waiting beside a known respawn is progress too.
        const bool waiting=current>=0 && belief.waitable(tc.round,config::respawn_wait);
        if (waiting && dist<=2) mem.contract.checked=tc.round;
        if (current>=0 && (!DZ_CREW_REACH || dist<cambc::distance_field::unreachable) && (belief.available(tc.round)||waiting) && mem.contract.progressing(tc.round, dist, belief.hp, belief.capture))
            return {blocks_respawn&&current==occupied_group ? GoalKind::YieldSpawn : GoalKind::Farm, current};
        if (current>=0) {
            if (!belief.available(tc.round)) mem.contract.objective = -1;
            else mem.release(tc.round);
        }
    }
    if (tc.round < mem.idle_until && obs.hp >= .9f * obs.max_hp) return {GoalKind::Idle};
    DZ_PROF('K');
    auto word = shared_word();
#if DZ_ECONOMY_V2
    const auto reserved_crew=protocol::compact::lease(word,tc.round);
#endif
    float best = 1e30f; int chosen = -1;
    // Best-first: rank groups by a cheap upper bound on their rate (claims and
    // clear time only lower it; the distance floor never exceeds the exact
    // distance), then price them in that order and stop once no remaining
    // bound can beat the best. Same optimum, but only a few groups are priced:
    // repricing every group each turn cost 30-50k fuel (02the-pack).
    struct Candidate { float bound; unsigned index; bool waitable; };
    static std::vector<Candidate> candidates;
    candidates.clear();
    for (unsigned i = 0; i < world.groups.size(); ++i) {
#if DZ_ECONOMY_V2
        if(reserved_crew.valid&&reserved_crew.objective==static_cast<int>(i)&&!(reserved_crew.members&(1u<<world.slot)))continue;
        if(crew_reserved(i))continue;
#endif
        const auto& belief = mem.groups[i]; const auto& g = world.groups[i];
        // A known respawn is priced at max(travel, wait) instead of ignored:
        // walking 26 tiles past a cluster that returns in 10 rounds wastes time.
        const bool waitable = belief.waitable(tc.round, config::respawn_wait) && g.sdk.gem_value()>0;
        if (!belief.available(tc.round) && !waitable) continue;
        const int floor = world.distance_floor(i, obs.p);
        if (!g.field && floor > 30) continue;
        const int wait = waitable ? belief.ready - tc.round : 0;
        const float value = (g.sdk.gem_value()+gold_weight(tc.round)*g.sdk.gold_value())*half_weight(world,i);
        if (value<=0) continue;
#if DZ_STYLE == 2
        if (world.home.get(g.tiles.front())>14) continue;
#elif DZ_STYLE == 3
        if (!g.cluster) continue;
#endif
        // Legacy (starvation) scoring is nearest-first: rank by the floor.
        const float bound = legacy ? -static_cast<float>(floor) : value/(std::max(floor,wait)+cambc::constants::capture_time+2.f);
        candidates.push_back({bound, i, waitable});
    }
    std::sort(candidates.begin(), candidates.end(), [](const Candidate& x, const Candidate& y) { return x.bound > y.bound; });
    unsigned priced = 0;
#if DZ_CLEAR_TIME_CLOCK
    const auto timing=reset_timing();
#endif
    for (const auto& candidate : candidates) {
        // Each budget check is two SDK host calls; check every eighth group.
        // Check before each pricing: an unpriced cold cache can cost several
        // thousand fuel per group (00vault exhausted with every-eighth checks).
        if (!tc.allow(DZ_ECONOMY_V2?18000:8000)) break;
        if (!legacy && -candidate.bound >= best) break; // Nothing left can win.
        const unsigned i = candidate.index;
        const auto& belief = mem.groups[i]; const auto& g = world.groups[i];
        const bool waitable = candidate.waitable;
        const int dist = world.distance(i, obs.p);
        if (dist >= 65535 || (!g.field && dist > 30)) continue;
        const int wait = waitable ? belief.ready - tc.round : 0;
        int claims = 0;
        for (unsigned slot = 0; slot < world.allies.size() && slot < protocol::slots; ++slot)
            if (slot != world.slot && i < 112 && protocol::slot(word, slot).objective == i) ++claims;
#if DZ_HAS(MARKET) && !DZ_ECONOMY_V2
        if (DZ_ON(MARKET) && claims) {
            // C1: the best bid keeps the group at full value; an outbid body looks elsewhere.
            const unsigned mine=market::bucket(dist);
            bool lost=false;
            for (unsigned slot = 0; slot < world.allies.size() && slot < protocol::slots; ++slot)
                if (slot != world.slot && protocol::slot(word, slot).objective == i && market::outbid(market::bid(word,slot),slot,mine,world.slot)) lost=true;
            if (lost) continue;
            claims=0;
        }
#endif
        // Reward per round of travel, clear and capture, over solo-survivable
        // groups only. A heuristic rate, not the unvalidated ObjModel/auction.
        const float value=(g.sdk.gem_value()+gold_weight(tc.round)*g.sdk.gold_value())*half_weight(world,i)/(1.f+claims);
        float fixed=std::max(dist,wait)+cambc::constants::capture_time+2.f;
        if (legacy) {
            // The pre-gate nearest-group score, used only while starving.
            float score = dist + .03f * g.strength + (g.cluster ? claims * 10.f : claims * 2.f) - (belief.state == GroupState::Reward ? 8.f : 0.f);
            if (score < best) { best = score; chosen = i; }
            continue;
        }
        if (-value/fixed>=best) continue; // Cannot win even with a free clear.
#if DZ_BANK_AWARE_RATE
        int delivery=cambc::distance_field::unreachable;bool unknown_delivery=false;
        for(unsigned a=0;a<world.altars.size();++a)if(altar_open(a)) {
            const int distance=world.delivery_distance(i,a,tc);
            if(distance<0) { unknown_delivery=true;break; }
            delivery=std::min(delivery,distance);
        }
        // A cold/unreachable estimate never invents a hard feasibility veto.
        // Small payouts amortize one bank trip over the configured bag target;
        // current claims divide the expected personal reward. This is a static
        // optimistic travel cost, not a calibrated channel/contest model.
        if(!unknown_delivery&&delivery<cambc::distance_field::unreachable) {
            const float share=g.sdk.gem_value()/(1.f+claims);
            const float fraction=std::clamp((obs.bag+share)/config::bank_bag,0.f,1.f);
            fixed+=fraction*delivery;
        }
        if(-value/fixed>=best)continue;
#endif
        float clear_rounds=0;
        if (belief.state!=GroupState::Reward) {
            DZ_ACC_BEGIN(acc_r);
#if DZ_HAS(CREWS)
            auto risk=clear_risk(static_cast<int>(i),!DZ_ON(CREWS) ? 0.f : DZ_ON(CREW_ALL) ? (crew_size-1)*obs.strength*obs.camp_damage :
                crew_size>1&&(world.slot&1u)==0 ? obs.strength*obs.camp_damage : 0.f);
#else
            auto risk=clear_risk(static_cast<int>(i));
#endif
            DZ_ACC_END(1,acc_r);
            if (!risk.complete() || (g.strength>0 && !clear_survivable(risk,obs.hp,obs.max_hp))) continue;
            clear_rounds=risk.attacks+(DZ_CLEAR_TIME_WORK_ONLY ? 0.f : .25f*g.tiles.size());
#if DZ_CLEAR_TIME_CLOCK
            if(tc.allow(6000+150*g.tiles.size())) {
                const auto clock=group_attack_clock(world,mem,obs,static_cast<int>(i),mem.quantize_out,timing);
                if(clock.complete())clear_rounds=clock.rounds;
            }
#endif
        }
        float score=-value/(fixed+clear_rounds);
        // Enemy within 6 of the group's tile hull (centre + radius): an
        // enemy x tile x group scan was ~50k fuel per turn on 02the-pack.
        bool contested=false;
        for (const auto& e : obs.enemies)
            if (static_cast<int>(e.p.chebyshev_distance(g.center)) <= 6 + g.radius) { contested=true; break; }
#if DZ_HAS(EE)
        if (DZ_ON(EE)) contested=contested||mem.recently_seen_near(g.center,6+g.radius,tc.round,DZ_EE_MEMORY);
#endif
        if (contested) score*=.33f;
        if (score < best) { best = score; chosen = i; }
    }
    DZ_PROF('S');
#if !DZ_ECONOMY_V2
    // One crew decision per team: the lowest living slot leads. A follower
    // that cannot solo the leader's damaging target joins it.
    unsigned leader=world.slot;
    for (unsigned slot=0;slot<world.allies.size()&&slot<protocol::slots;++slot)
        if (slot==world.slot || protocol::slot(word,slot).objective!=protocol::dead) { leader=slot; break; }
    if (!legacy && leader!=world.slot && !blocks_respawn && obs.hp >= .9f * obs.max_hp) {
        const int job=protocol::slot(word,leader).objective;
        if (protocol::is_group_code(job)&&job<static_cast<int>(world.groups.size()) && world.groups[job].strength>0 && mem.groups[job].available(tc.round) &&
#if DZ_ECONOMY_V2
            !crew_reserved(job)&&
#endif
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
            if (!tc.allow(DZ_ECONOMY_V2?18000:8000)) break;
#if DZ_ECONOMY_V2
            if(crew_reserved(i))continue;
#endif
            const auto& belief=mem.groups[i]; const auto& g=world.groups[i];
            if (g.strength<=0 || belief.state==GroupState::Reward || !belief.available(tc.round)) continue;
            if constexpr (DZ_CREW_REACH) {
                if (g.field && g.field->get(obs.p)>=cambc::distance_field::unreachable) continue;
            }
            const int home=world.home.get(g.tiles.front());
            if (home>=cambc::distance_field::unreachable) continue;
            int claims=0;
            for (unsigned slot=0;slot<world.allies.size()&&slot<protocol::slots;++slot)
                if (slot!=world.slot && i<112 && protocol::slot(word,slot).objective==i) ++claims;
            const float value=(g.sdk.gem_value()+gold_weight(tc.round)*g.sdk.gold_value())*(claims?4.f:1.f)/living;
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
        if (crew_choice>=0 && crew_best<best &&
            (!DZ_CREW_REACH || world.distance(crew_choice,obs.p)<cambc::distance_field::unreachable)) {
            auto& b=mem.groups[crew_choice];
            mem.contract.start(crew_choice,tc.round,world.distance(crew_choice,obs.p),b.hp,b.capture,config::crew_window);
            return {GoalKind::Farm,crew_choice};
        }
    }
#endif
    DZ_PROF('L');
    if (chosen < 0) {
        if (blocks_respawn) return {GoalKind::YieldSpawn};
        if constexpr (DZ_IDLE_HELPER) {
            // No solo job won. Reinforce only a nearby, visibly active clear:
            // real ally, matching soft claim, partially damaged awake group,
            // and a survivable crew already present. Never scout/wander toward
            // a stale claim or count proximity alone as productive support.
            if (!legacy&&obs.enemies.empty()&&obs.hp>=.9f*obs.max_hp) {
                LocalMask awake;awake.load(cambc::vision::awake_camp_tiles());
                float best_help=1e30f;int help=-1;
                for (unsigned slot=0;slot<world.allies.size()&&slot<protocol::slots&&tc.allow(8000);++slot) {
                    if (slot==world.slot) continue;
                    const auto job=protocol::slot(word,slot).objective;
                    if (!protocol::is_group_code(job)||job>=world.groups.size()||mem.groups[job].state!=GroupState::Partial||world.groups[job].strength<=0) continue;
#if DZ_ECONOMY_V2
                    if(crew_reserved(job))continue;
#endif
                    const auto ally=std::find_if(obs.allies.begin(),obs.allies.end(),[&](auto& a){return a.sdk==world.allies[slot];});
                    if (ally==obs.allies.end()||ally->hp<.5f*ally->max_hp||obs.p.chebyshev_distance(ally->p)>4) continue;
                    const int distance=world.distance(job,obs.p);
                    if (distance>4||world.distance(job,ally->p)>4) continue;
                    bool active=false;for(auto tile:world.groups[job].tiles) if(awake.test(tile)){active=true;break;}
                    if (!active) continue;
                    unsigned crew=1;for(auto& a:obs.allies) if(a.hp>0&&a.p.chebyshev_distance(obs.p)<=4) ++crew;
                    const auto risk=clear_risk(job,crew_strength(obs,obs.p,4));
                    if (!clear_survivable(risk,obs.hp,obs.max_hp,crew_share(crew))) continue;
                    const float score=distance+risk.attacks;
                    if(score<best_help){best_help=score;help=job;}
                }
                if(help>=0){auto& b=mem.groups[help];mem.contract.start(help,tc.round,world.distance(help,obs.p),b.hp,b.capture,config::crew_window);return {GoalKind::Farm,help};}
            }
        }
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
#if DZ_ECONOMY_V2
Goal safe_goal(StaticWorld& world,Memory& mem,const Observation& obs,const TurnContext& tc) {
    auto goal=crew_action(strategic_goal(world,mem,obs,tc),world,mem,obs,tc);
    if(goal.kind==GoalKind::Bank&&goal.index>=0&&goal.index<static_cast<int>(mem.bank_access.size())) {
        const auto& bank=mem.bank_access[goal.index];const int age=static_cast<int>(tc.round)-bank.round;
        if(obs.enemies.empty()&&bank.current(tc.round,mem.topology_revision,mem.threat_revision,obs.max_hp,obs.camp_factor,bank_duration(std::max(obs.bag,1)))&&
            bank.plan.quality==bank::Quality::Bounded&&bank.plan.travel+bank.channel+1<=bank.until-age) {
            auto& route=mem.bank_route;
            if(route.altar!=goal.index||route.root!=bank.plan.root||route.revision!=mem.topology_revision||route.expires<=static_cast<int>(tc.round)) {
                route.field.reset();route.altar=goal.index;route.root=bank.plan.root;route.revision=mem.topology_revision;
                route.expires=bank.round+bank.until;route.pending=true;
            }
            goal.destination=vec2{route.root.x,route.root.y};
        }
    }
    return goal;
}
#endif
}
