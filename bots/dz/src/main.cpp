#include "draft.h"
#include "gear.h"
#include "safemode.h"
#include "model_audit.h"
#include "crew.h"
#include "lifecycle.h"
#if DZ_ECONOMY_V2
#include "siege.h"
#endif

namespace {
void emergency(const dz::StaticWorld& world,const dz::Observation& obs,const dz::TurnContext& tc,dz::Actuator& act) {
    if (dz::tier_for(dz::fuel_left())==dz::Tier::Fallback) { dz::quick_home(world,tc,act); return; }
    auto& me=cambc::self(); auto state=me.state();
    if (state.is_dead()||state.contains(cambc::champion_state::recalling)||
        state.contains(cambc::champion_state::submitting_gems)||state.contains(cambc::champion_state::teleporting)) return;
    const auto p=me.position();
    if (me.gem_count()>0&&dz::channel_safe(world,obs,tc)) {
        for (const auto& altar:world.altars) if (p.chebyshev_distance(altar.tile)<=cambc::constants::submit_gems_range) {
            if (act.bank(altar.tile)) return;
            break;
        }
    }
    if (me.can_move()) for (auto delta:world.home.next_moves_from(p)) {
        auto destination=p+delta;
        if (!obs.is_occupied(destination)) { act.move(destination); break; }
    }
}
}
#if DZ_TRACE
// Per-body time accounting: 0 farm-travel, 1 farm-clear, 2 farm-capture,
// 3 bank, 4 home, 5 retreat, 6 idle, 7 yield, 8 fight, 9 channel, 10 dead.
static std::array<unsigned,11> dz_time{};
static std::array<unsigned,5> dz_prod{}; // work, progress, stall, idle, other
static unsigned dz_exec_calls=0;
#endif
int main() {
    dz::Counters counts;
    if (cambc::is_draft()) dz::draft_loop(counts);
    // Construct inside the boundary: allocations and SDK-backed mask constructors
    // can throw. A failed startup is retried next turn, never a permanent trap.
    std::unique_ptr<dz::StaticWorld> world;
    std::unique_ptr<dz::Memory> mem;
    std::unique_ptr<dz::Observation> obs;
    bool priority_set = false, claim_initialized=false, first_frame=true;
    dz::ModuleHealth observation_health,boot_health,shop_health,camp_health,memory_health,
        planner_health,execution_health,communication_health,field_health,recovery_health;
    for (;;) {
        auto tc = dz::TurnContext::begin(); dz::Actuator act(tc, counts);
#if DZ_TRACE
        dz::trace_cap = world && world->slot==DZ_TRACE_SLOT && tc.round>=DZ_TRACE_FROM && tc.round<DZ_TRACE_TO ? 60000 : 3000;
        // A consistently busy planner may never leave the end-turn spare fuel
        // needed to write buffered diagnostics. Drain them on a fresh budget
        // before producing more, so missing counters cannot mimic a dead bot.
        dz::trace_flush();
#endif
#if DZ_TRACE
        { ::dz::TraceScope dz_trace_scope;
#if DZ_TRACE_PROFILE
        dz::turn_profile.flush(world ? world->slot : 0); dz::turn_profile.begin(tc.round);
#endif
        }
#endif
#if DZ_TRACE
        { ::dz::TraceScope dz_trace_scope;
        if (dz::recovery_sample.valid) {
            const auto& s=dz::recovery_sample;
            ::dz::trace("DZ_LOW_FUEL round=%u slot=%u entry=%llu remaining=%llu moved=%d cleared=%d before=%d after=%d\n",
                s.round,world?world->slot:0,static_cast<unsigned long long>(s.entry),static_cast<unsigned long long>(s.remaining),s.moved,s.cleared,s.before,s.after);
            dz::recovery_sample.valid=false;
        }
        if (tc.round % 250 == 0) {
            ::dz::trace("DZ_TIME round=%u slot=%u %u %u %u %u %u %u %u %u %u %u %u exec=%u/%u linecost_max=%llu mean=%llu prod %u %u %u %u %u\n",
                tc.round,world?world->slot:0,dz_time[0],dz_time[1],dz_time[2],dz_time[3],dz_time[4],dz_time[5],dz_time[6],dz_time[7],dz_time[8],dz_time[9],dz_time[10],
                dz_exec_calls,dz::execute_entries,static_cast<unsigned long long>(dz::trace_line_cost_max),
                static_cast<unsigned long long>(dz::trace_lines?dz::trace_line_cost_sum/dz::trace_lines:0),
                dz_prod[0],dz_prod[1],dz_prod[2],dz_prod[3],dz_prod[4]);
        }
        if (tc.round % 50 == 0 && dz::trace_flush_cost.bytes) ::dz::trace("DZ_FLUSH bytes=%zu fuel=%llu\n",dz::trace_flush_cost.bytes,static_cast<unsigned long long>(dz::trace_flush_cost.fuel));
        if (tc.round % 100 == 0) ::dz::trace("DZ_COUNTS round=%u slot=%u actions=%u modules=%u stale=%u\n",
            tc.round, world ? world->slot : 0, counts.action_errors, counts.module_errors, counts.stale);
        }
#endif
        try {
            if (!world) world = std::make_unique<dz::StaticWorld>();
#if DZ_PLAN_TABLE
            // The turn after boot loads the camps (never the boosted first turn, which can't afford a second camp walk).
            if (!dz::plan_loaded && world->loaded()) dz::load_plan(dz::map_signature(world->groups));
            if (dz::plan_loaded) dz::apply_switch(tc.round);
#endif
            if (!mem) mem = std::make_unique<dz::Memory>();
            if (!obs) obs = std::make_unique<dz::Observation>();
            if (!claim_initialized && dz::module_work(boot_health,tc,counts,"roster",[&]{world->load_roster(tc);})) {
                dz::module_work(communication_health,tc,counts,"communication",[&]{
                    // Guest-local state resets after a fault; shared claims do
                    // not. Clear our old claim before expensive map startup.
                    claim_initialized=act.publish(dz::protocol::with_slot(dz::shared_word(),world->slot,{dz::protocol::idle,false}));
#if DZ_TRACE
                    { ::dz::TraceScope dz_trace_scope;
                    if (claim_initialized) {
                        auto seen=dz::protocol::slot(dz::shared_word(),world->slot);
                        ::dz::trace("DZ_BOOT_CLAIM round=%u slot=%u objective=%u onsite=%d\n",tc.round,world->slot,static_cast<unsigned>(seen.objective),seen.onsite);
                    }
                    }
#endif
                });
            }
            if (first_frame) {
                first_frame=false;
                // A replacement guest gets an ordinary budget. Its SDK startup
                // has already spent part of it; map loading uses the next turn.
                if (tc.fuel0<=dz::config::ordinary_turn_fuel) {
#if DZ_TRACE
                    { ::dz::TraceScope dz_trace_scope;
                    ::dz::trace("DZ_BOOT_DEFER round=%u slot=%u fuel_at_entry=%llu\n",tc.round,world->slot,static_cast<unsigned long long>(tc.fuel0));
                    }
#endif
                    tc.guard(); dz::end_turn_traced(); continue;
                }
            }
            if (world->ready&&dz::tier_for(dz::fuel_left())==dz::Tier::Fallback) {
                dz::module_work(recovery_health,tc,counts,"recovery",[&]{dz::quick_home(*world,tc,act);});
                tc.guard(); dz::end_turn_traced(); continue;
            }
            DZ_PROF('s');
            if (!dz::module_work(observation_health,tc,counts,"observation",[&]{obs->read(tc);})) {
                if (cambc::round_number()==tc.round) dz::end_turn_traced();
                continue;
            }
            if (obs->state.is_dead()) {
#if DZ_SIEGE || DZ_ECONOMY_V2
                if(mem->siege_task.active())mem->siege_task.reset(tc.round,15);
#endif
#if DZ_ECONOMY_V2
                mem->opening_commitment={};mem->shopping_since=-1;mem->siege_depth=0;mem->delivery_trip={};mem->neutral_recovery={};mem->early_opening={};
#if DZ_LIFECYCLE
                mem->lifecycle={};mem->contract.objective=-1;mem->leave_crew();mem->field_needed=-1;
#endif
#endif
#if DZ_TRACE
                { ::dz::TraceScope dz_trace_scope;
                ++dz_time[10];
                }
#endif
                dz::module_work(shop_health,tc,counts,"shop",[&]{dz::shop(tc, act,world.get());});
            }
            else {
                const bool already_ready = world->playable();
                if (!dz::module_work(boot_health,tc,counts,"boot",[&]{
#if DZ_ECONOMY_V2 && DZ_LIFECYCLE
                    if(!world->playable()) {
                        for(unsigned stage=0;stage<32;++stage) {
                            const auto before=dz::fuel_left();world->boot(tc);
                            if(world->playable()||before==dz::fuel_left()||!tc.allow(world->field_budget()+10000))break;
                        }
                    }
#else
                    world->boot(tc);
#endif
                })) {
                    if (cambc::round_number()==tc.round) dz::end_turn_traced();
                    continue;
                }
#if DZ_TRACE
                { ::dz::TraceScope dz_trace_scope;
                if (tc.round <= 8) ::dz::trace("DZ_BOOT round=%u slot=%u ready=%d fuel=%llu\n", tc.round, world->slot, world->ready,
                    static_cast<unsigned long long>(cambc::fuel_remaining()));
                }
#endif
                if (world->playable() && (already_ready
#if DZ_ECONOMY_V2 && DZ_LIFECYCLE
                    ||tc.allow(68000) // Complete memory and the first useful action on a sufficiently funded opening turn.
#endif
                )) {
                    if (!priority_set) priority_set = act.priority(100 - static_cast<int>(world->slot));
                    const bool shop_attempted=shop_health.enabled();
                    const bool shop_ok=dz::module_work(shop_health,tc,counts,"shop",[&]{if (dz::shop(tc,act,world.get())) obs->refresh_self(tc);});
                    // A shop exception can follow a successful purchase. Refresh
                    // before planning with stats that may have changed partially.
                    if (shop_attempted&&!shop_ok && !dz::module_work(observation_health,tc,counts,"observation",[&]{obs->refresh_self(tc);})) {
                        if (cambc::round_number()==tc.round) dz::end_turn_traced();
                        continue;
                    }
                    auto clear_claim=[&] {
                        dz::module_work(communication_health,tc,counts,"communication",[&]{
                            act.publish(dz::protocol::with_slot(dz::shared_word(),world->slot,{dz::protocol::idle,false}));
                        });
                    };
                    bool camps_ok=true;
                    if constexpr (dz::config::camp_safety)
                        camps_ok=dz::module_work(camp_health,tc,counts,"camps",[&]{obs->read_camps(*world,tc);});
                    DZ_PROF('o');
                    if (!camps_ok || dz::tier_for(dz::fuel_left())==dz::Tier::Fallback ||
                        !dz::module_work(memory_health,tc,counts,"memory",[&]{mem->update(*world,tc);})) {
                        emergency(*world,*obs,tc,act);
                        clear_claim();
                    } else {
#if DZ_TRACE
                        { ::dz::TraceScope dz_trace_scope;
                        if (tc.round <= 8) ::dz::trace("DZ_MEMORY round=%u slot=%u fuel=%llu\n", tc.round, world->slot,
                            static_cast<unsigned long long>(cambc::fuel_remaining()));
                        }
#endif
                        DZ_PROF('m');
#if DZ_ECONOMY_V2
                        // A requested cold route is a dependency of the next
                        // bid, not spare-time work after speculative crews.
                        if(mem->field_needed>=0&&!world->groups[mem->field_needed].field)
                            dz::module_work(field_health,tc,counts,"requested-fields",[&]{world->build_one_field(tc,mem->field_needed);});
                        if(mem->field_needed>=0&&world->groups[mem->field_needed].field)mem->field_needed=-1;
#if DZ_LIFECYCLE
                        if(!dz::lifecycle_owns(*mem)) {
#endif
                        if(!DZ_LIFECYCLE||mem->lifecycle.altar>=0)
                            dz::module_work(field_health,tc,counts,"bank-fields",[&]{dz::build_bank_field(*world,*mem,*obs,tc);});
                        if(mem->contract.objective<0&&!mem->siege_task.active()&&obs->enemies.empty()&&!obs->channel())
                            dz::module_work(field_health,tc,counts,"crew-planning",[&]{dz::progress_crew_layout(*world,*mem,tc,false);});
                        bool built_crew_route=false;
                        dz::module_work(field_health,tc,counts,"crew-fields",[&]{built_crew_route=dz::build_crew_field(*world,*mem,*obs,tc);});
                        if (!built_crew_route&&mem->field_needed>=0) {
#else
                        if (mem->field_needed>=0) {
#endif
                            const int requested=mem->field_needed;
                            if (!world->groups[requested].field)
                                dz::module_work(field_health,tc,counts,"fields",[&]{world->build_one_field(tc,requested);});
                            if (world->groups[requested].field) mem->field_needed=-1;
                        }
#if DZ_ECONOMY_V2 && DZ_LIFECYCLE
                        }
#endif
                        dz::Goal goal;
#if DZ_TRACE && DZ_TRACE_PROFILE
                        const auto planner_fuel=::dz::trace_fuel_mark();
#endif
                        if (!dz::module_work(planner_health,tc,counts,"planner",[&]{goal=dz::safe_goal(*world,*mem,*obs,tc);})) {
                            emergency(*world,*obs,tc,act);
                            clear_claim();
                            if (cambc::round_number()==tc.round) dz::end_turn_traced();
                            continue;
                        }
                        DZ_PROF('q');
#if DZ_TRACE && DZ_TRACE_MODEL
                        dz::audit_model(goal,*world,*mem,*obs,tc);
#endif
#if DZ_TRACE
                        { ::dz::TraceScope dz_trace_scope;
#if DZ_TRACE_PROFILE
                        if (tc.round > 8 && planner_fuel-::dz::trace_fuel_mark() > 15000)
                            ::dz::trace("DZ_PLANNER_FUEL round=%u slot=%u used=%llu entry=%llu kind=%d\n",tc.round,world->slot,
                                static_cast<unsigned long long>(planner_fuel-::dz::trace_fuel_mark()),static_cast<unsigned long long>(tc.fuel0),static_cast<int>(goal.kind));
#endif
                        if (DZ_TRACE_FIGHT && !obs->enemies.empty() && world->slot==DZ_TRACE_SLOT && tc.round>=DZ_TRACE_FROM && tc.round<DZ_TRACE_TO) {
                            int nearest=99; unsigned allies6=0; float reach_str=0,reach_hp=0;
                            for (const auto& e:obs->enemies) {
                                const int d=obs->p.chebyshev_distance(e.p);
                                nearest=std::min(nearest,d);
                                if (d<=e.range) { reach_str+=e.strength; reach_hp+=e.hp; }
                            }
                            for (const auto& a:obs->allies) allies6+=obs->p.chebyshev_distance(a.p)<=6;
                            ::dz::trace("DZ_FIGHT round=%u slot=%u kind=%d hp=%.0f max=%.0f enemies=%zu nearest=%d allies6=%u pos=%d,%d reach_str=%.0f reach_hp=%.0f str=%.0f\n",
                                tc.round,world->slot,static_cast<int>(goal.kind),obs->hp,obs->max_hp,obs->enemies.size(),nearest,allies6,obs->p.x,obs->p.y,reach_str,reach_hp,obs->strength);
                        }
                        if (tc.round <= 8 || tc.round % 100 == 0 || (world->slot==DZ_TRACE_SLOT && tc.round>=DZ_TRACE_FROM && tc.round<DZ_TRACE_TO)) ::dz::trace("DZ_GOAL round=%u slot=%u kind=%d index=%d pos=%d,%d bag=%d hp=%.0f altar0=%d\n",
                            tc.round, world->slot, static_cast<int>(goal.kind), goal.index, obs->p.x, obs->p.y, obs->bag, obs->hp,
                            world->altars.empty() ? -1 : world->altar_distance(0, obs->p));
                        if ((tc.round%100==0 || (world->slot==DZ_TRACE_SLOT && tc.round>=DZ_TRACE_FROM && tc.round<DZ_TRACE_TO)) && goal.kind==dz::GoalKind::Farm) {
                            const auto& b=mem->groups[goal.index];
                            ::dz::trace("DZ_FARM round=%u slot=%u state=%d hp=%.0f capture=%d seen=%d checked=%d ready=%d avoid=%d\n",
                                tc.round,world->slot,static_cast<int>(b.state),b.hp,b.capture,b.seen,mem->contract.checked,b.ready,b.avoid_until);
                        }
                        }
#endif
#if DZ_TRACE && DZ_TRACE_PROFILE
                        const auto exec_fuel=::dz::trace_fuel_mark();
#endif
                        DZ_PROF('p');
#if DZ_ECONOMY_V2
                        // Re-check PHYSICAL headroom after diagnostics and crew
                        // layout, before the executor's unconditional SDK reads.
                        if(!tc.allow(8000)) {
                            emergency(*world,*obs,tc,act);clear_claim();
                            tc.guard();dz::end_turn_traced();continue;
                        }
#endif
                        bool executed=dz::module_work(execution_health,tc,counts,"executor",[&] {
                            if (obs->channel()) {
                                if (goal.kind==dz::GoalKind::Retreat && act.cancel_channel()) dz::execute(goal,*world,*mem,*obs,tc,act);
                            } else {
#if DZ_TRACE
                                ++dz_exec_calls;
#endif
                                dz::execute(goal,*world,*mem,*obs,tc,act);
                            }
                        });
                        DZ_PROF('e');
                        if (!executed) emergency(*world,*obs,tc,act);
#if DZ_TRACE && DZ_TRACE_PROFILE
                        { ::dz::TraceScope dz_trace_scope;
                        if (exec_fuel-::dz::trace_fuel_mark()>30000) ::dz::trace("DZ_EXEC_FUEL round=%u slot=%u used=%llu kind=%d index=%d\n",tc.round,world->slot,static_cast<unsigned long long>(exec_fuel-::dz::trace_fuel_mark()),static_cast<int>(goal.kind),goal.index);
                        }
#endif
#if DZ_TRACE
                        { ::dz::TraceScope dz_trace_scope;
                        if (obs->channel()) ++dz_time[9];
                        else if (goal.kind==dz::GoalKind::Farm) {
                            const auto here=cambc::self().position();
                            const bool site=world->distance(goal.index,here)<=std::max(1,obs->range)||world->group_at(here)==goal.index;
                            ++dz_time[!site?0:mem->groups[goal.index].state==dz::GroupState::Reward?2:1];
                        } else ++dz_time[std::min<std::size_t>(10,static_cast<std::size_t>(goal.kind)+2)];
                        {
                            // Productivity: 0 working (at target, channel), 1 progressing
                            // (path distance fell), 2 not progressing, 3 idle, 4 other goal.
                            auto& prod=dz_prod; static int last_target=-2, last_dist=-1;
                            const auto here=cambc::self().position();
                            int target=-1, dist=-1; bool working=obs->channel();
                            if (goal.kind==dz::GoalKind::Farm) {
                                target=goal.index; dist=world->distance(goal.index,here);
                                working|=world->group_at(here)==goal.index||dist<=std::max(1,obs->range);
                            } else if (goal.kind==dz::GoalKind::Bank) {
                                target=1000+goal.index; dist=world->altar_distance(goal.index,here);
                                working|=dist<=1;
                            }
                            unsigned kind=4;
                            if (working) kind=0;
                            else if (target>=0) kind=(target==last_target&&last_dist>=0&&dist<last_dist)||target!=last_target ? 1 : 2;
                            else if (goal.kind==dz::GoalKind::Idle) kind=3;
                            ++prod[kind]; last_target=target; last_dist=dist;
                        }
                        {
                            // Stuck detector: same tile for 30 turns while farming or banking,
                            // excluding legitimate on-site work (clearing, capturing, waiting).
                            static cambc::vec2 last{-1,-1}; static int still=0; static bool reported=false;
                            const auto here=cambc::self().position();
                            const bool working=goal.kind==dz::GoalKind::Farm&&(world->group_at(here)==goal.index||
                                world->distance(goal.index,here)<=std::max(1,obs->range));
                            if (here==last&&!obs->channel()&&(goal.kind==dz::GoalKind::Farm||goal.kind==dz::GoalKind::Bank)&&!working) ++still;
                            else { still=0; reported=false; }
                            last=here;
                            if (still>=30&&!reported) {
                                // Retry on a fresh turn if the trace budget dropped the line.
                                reported=::dz::trace("DZ_STUCK round=%u slot=%u kind=%d index=%d pos=%d,%d fuel=%llu field_budget=%llu has_field=%d dist=%d state=%d\n",
                                    tc.round,world->slot,static_cast<int>(goal.kind),goal.index,here.x,here.y,
                                    static_cast<unsigned long long>(cambc::fuel_remaining()),static_cast<unsigned long long>(world->field_budget()),
                                    goal.kind==dz::GoalKind::Farm?static_cast<bool>(world->groups[goal.index].field):-1,
                                    goal.kind==dz::GoalKind::Farm?world->distance(goal.index,here):world->altar_distance(goal.index,here),
                                    goal.kind==dz::GoalKind::Farm?static_cast<int>(mem->groups[goal.index].state):-1);
                            }
                        }
                        }
#endif
                        dz::module_work(communication_health,tc,counts,"communication",[&] {
                        std::uint8_t objective = dz::protocol::idle;
                        bool onsite = false;
                        if (!executed) objective=dz::protocol::idle;
                        else if (goal.kind == dz::GoalKind::Farm) {
                            objective = dz::protocol::group_code(goal.index);
                            const auto position = cambc::self().position();
                            onsite = world->group_at(position)==goal.index;
                        } else if (goal.kind == dz::GoalKind::Bank) objective = goal.index < 8 ? 112 + goal.index : dz::protocol::idle;
                        else if (goal.kind == dz::GoalKind::Home) {
                            objective=dz::protocol::shop;
#if DZ_ECONOMY_V2
                            // Waiting safely at full-health spawn is available
                            // capacity, not a committed equipment/recovery trip.
                            if(mem->shopping_since<0&&!mem->neutral_recovery.active&&world->home.get(cambc::self().position())==0&&
                                obs->hp>=obs->max_hp-.01f)objective=dz::protocol::idle;
#endif
                        }
                        else if (goal.kind == dz::GoalKind::Retreat) objective = dz::protocol::retreat;
#if DZ_ECONOMY_V2
                        else if(goal.kind==dz::GoalKind::Fight)objective=dz::protocol::fight;
                        const bool recovering_project=mem->crew_execution.recovering&&mem->crew_execution.group>=0&&
                            mem->crew_execution.group==mem->contract.objective&&tc.round<=static_cast<unsigned>(mem->crew_execution.recovery_deadline)&&
                            (goal.kind==dz::GoalKind::Home||goal.kind==dz::GoalKind::Retreat);
                        if(recovering_project)objective=dz::protocol::group_code(mem->crew_execution.group);
                        const bool siege_project=mem->siege_task.active()&&
                            (goal.kind==dz::GoalKind::Farm||goal.kind==dz::GoalKind::Home||goal.kind==dz::GoalKind::Retreat||
                             (goal.kind==dz::GoalKind::YieldSpawn&&goal.destination));
                        const int siege_owner=mem->siege_depth?mem->siege_parents[0].group:mem->siege_task.group;
                        // Preserve the root project while withdrawing or clearing
                        // an access prerequisite. Publishing only the child made
                        // another solo worker take the parent's occupied lane.
                        if(siege_project){objective=dz::protocol::group_code(siege_owner);onsite=world->group_at(cambc::self().position())==siege_owner;}
                        auto message=dz::protocol::with_slot(dz::shared_word(), world->slot, {objective, onsite});
                        const auto old_lease=dz::protocol::compact::lease(message,tc.round,2047);
                        const auto fresh_lease=dz::protocol::compact::lease(message,tc.round);
                        const unsigned leader=mem->economic_capturer;
                        const int offered=goal.kind==dz::GoalKind::Farm?goal.index:recovering_project?mem->crew_execution.group:-1;
                        const bool capture=offered>=0&&mem->groups[offered].state==dz::GroupState::Reward;
                        const auto& sent=mem->crew_publication;
                        const bool relaying=sent.group==offered&&sent.members==mem->economic_crew&&sent.capturer==world->slot&&leader!=world->slot;
                        const bool offering=executed&&offered>=0&&(!siege_project||offered==siege_owner)&&(leader==world->slot||relaying)&&offered<112&&mem->contract.objective==offered&&
                            (std::popcount(mem->economic_crew)>1||capture);
                        const bool changed=sent.group!=offered||sent.members!=mem->economic_crew||sent.capturer!=mem->economic_capturer;
                        const bool pulse=dz::team::publisher(tc.round,world->allies.size())==world->slot&&
                            dz::team::scheduled(tc.round)==dz::team::Kind::Lease;
                        const bool handoff=capture&&fresh_lease.valid&&fresh_lease.objective==offered&&fresh_lease.capturer==world->slot;
                        bool announced=false;
                        if(offering&&(changed||pulse)&&(!dz::team::protected_lease(message,tc.round,world->allies.size())||
                            fresh_lease.leader==world->slot||handoff)) {
                            message=dz::protocol::compact::with_lease(message,mem->economic_crew,mem->economic_capturer,tc.round);
                            announced=true;
                        } else if(old_lease.leader==world->slot&&(!offering||old_lease.objective!=offered||
                            old_lease.members!=mem->economic_crew||old_lease.capturer!=mem->economic_capturer))
                            message=dz::protocol::compact::with_lease(message,0,0,tc.round,false);
                        bool working=false;
                        if(goal.kind==dz::GoalKind::Farm&&mem->contract.objective==goal.index) {
                            const auto& group=mem->groups[goal.index];
                            const bool progress=mem->project_work.update(goal.index,mem->conversions[goal.index],tc.round,
                                world->distance(goal.index,cambc::self().position()),group.hp,group.capture,
                                mem->last_work==static_cast<int>(tc.round),dz::config::contract_window);
                            working=std::popcount(mem->economic_crew)>1||progress;
                        }
                        const auto intent=recovering_project||siege_project?dz::team::Intent::Recover:working?dz::team::Intent::Active:dz::team::Intent::Released;
                        message=dz::team::publish(message,tc.round,world->allies.size(),world->slot,cambc::self().gold_count(),objective,intent);
                        const auto& agreement=mem->crew_agreement;
                        const bool agreement_frame=executed&&!recovering_project&&offered>=0&&agreement.group==offered&&
                            agreement.members==mem->economic_crew&&agreement.announce(tc.round,world->allies.size())&&
                            (!agreement.committed||dz::team::scheduled(tc.round)==dz::team::Kind::Lease);
                        if(agreement_frame&&(!announced||!changed)) {
                            const auto role=agreement.roles[world->slot];
                            message=dz::team::acknowledge(message,tc.round,world->allies.size(),world->slot,
                                agreement.members,agreement.phase,role.dx,role.dy,agreement.can_ready||agreement.committed);
                        }
                        if(executed&&goal.kind==dz::GoalKind::Fight&&mem->fight_focus.round==static_cast<int>(tc.round))
                            message=dz::team::focus(message,tc.round,world->allies.size(),world->slot,mem->fight_focus.target);
                        if(act.publish(message)) {
                            mem->team.observe(message,tc.round,world->allies.size());
                            if(announced)mem->crew_publication={offered,mem->economic_crew,mem->economic_capturer};
                            else if(!offering)mem->crew_publication={};
                        }
#else
                        act.publish(dz::protocol::with_slot(dz::shared_word(), world->slot, {objective, onsite}));
#endif
                        });
                        DZ_PROF('c');
                        dz::module_work(field_health,tc,counts,"fields",[&]{
#if DZ_ECONOMY_V2 && DZ_LIFECYCLE
                            if(!world->ready)world->boot(tc);
#endif
#if DZ_ECONOMY_V2
                            dz::progress_crew_layout(*world,*mem,tc,!DZ_LIFECYCLE);
#endif
                            world->build_one_field(tc,mem->contract.objective);
                        });
                    }
                }
            }
            if (obs->state.is_dead() && world->ready)
                dz::module_work(communication_health,tc,counts,"communication",[&]{
                    act.publish(dz::protocol::with_slot(dz::shared_word(),world->slot,{dz::protocol::dead,false}));
                });
        } catch (const dz::StaleTurn&) { ++counts.stale; continue; }
        catch (const std::exception& error) {
            ++counts.module_errors;
#if DZ_TRACE
            { ::dz::TraceScope dz_trace_scope;
            if (counts.module_errors <= 20) ::dz::trace("DZ_MODULE_ERROR round=%u %s\n", tc.round, error.what());
            }
#endif
            // Best-effort recovery, itself contained. A channel in progress is left
            // intact. Never retry a complex failing module recursively.
            try {
                tc.guard();
                if (world && world->ready && !cambc::self().state().is_dead() && !cambc::self().is_recalling() &&
                    !cambc::self().is_submitting_gems() && !cambc::self().is_teleporting()) {
                    auto p = cambc::self().position();
                    if (world->home.get(p) > 0 && cambc::self().health() < .3f * cambc::self().max_health()) act.recall();
                }
            } catch (const dz::StaleTurn&) { ++counts.stale; continue; }
            catch (...) {}
        }
        catch (...) { ++counts.module_errors; }
        // An exhausted turn resumes here too. Do not surrender its fresh budget.
        if (cambc::round_number() != tc.round) { ++counts.stale; continue; }
        dz::end_turn_traced();
    }
}
