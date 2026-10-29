#include "draft.h"
#include "gear.h"
#include "safemode.h"

namespace {
void emergency(const dz::StaticWorld& world,const dz::Observation& obs,const dz::TurnContext& tc,dz::Actuator& act) {
    if (dz::tier_for(cambc::fuel_remaining())==dz::Tier::Fallback) { dz::quick_home(world,tc,act); return; }
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
        if (!obs.occupied.is_set(destination)) { act.move(destination); break; }
    }
}
}
#if DZ_TRACE
// Per-body time accounting: 0 farm-travel, 1 farm-clear, 2 farm-capture,
// 3 bank, 4 home, 5 retreat, 6 idle, 7 yield, 8 fight, 9 channel, 10 dead.
static std::array<unsigned,11> dz_time{};
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
        if (dz::recovery_sample.valid) {
            const auto& s=dz::recovery_sample;
            std::printf("DZ_LOW_FUEL round=%u slot=%u entry=%llu remaining=%llu moved=%d cleared=%d before=%d after=%d\n",
                s.round,world?world->slot:0,static_cast<unsigned long long>(s.entry),static_cast<unsigned long long>(s.remaining),s.moved,s.cleared,s.before,s.after);
            dz::recovery_sample.valid=false;
        }
        if (tc.round % 250 == 0) {
            std::printf("DZ_TIME round=%u slot=%u",tc.round,world?world->slot:0);
            for (auto t:dz_time) std::printf(" %u",t);
            std::printf("\n");
        }
        if (tc.round % 100 == 0) std::printf("DZ_COUNTS round=%u slot=%u actions=%u modules=%u stale=%u\n",
            tc.round, world ? world->slot : 0, counts.action_errors, counts.module_errors, counts.stale);
#endif
        try {
            if (!world) world = std::make_unique<dz::StaticWorld>();
            if (!mem) mem = std::make_unique<dz::Memory>();
            if (!obs) obs = std::make_unique<dz::Observation>();
            if (!claim_initialized && dz::module_work(boot_health,tc,counts,"roster",[&]{world->load_roster(tc);})) {
                dz::module_work(communication_health,tc,counts,"communication",[&]{
                    // Guest-local state resets after a fault; shared claims do
                    // not. Clear our old claim before expensive map startup.
                    claim_initialized=act.publish(dz::protocol::with_slot(dz::shared_word(),world->slot,{dz::protocol::idle,false}));
#if DZ_TRACE
                    if (claim_initialized) {
                        auto seen=dz::protocol::slot(dz::shared_word(),world->slot);
                        std::printf("DZ_BOOT_CLAIM round=%u slot=%u objective=%u onsite=%d\n",tc.round,world->slot,static_cast<unsigned>(seen.objective),seen.onsite);
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
                    std::printf("DZ_BOOT_DEFER round=%u slot=%u fuel_at_entry=%llu\n",tc.round,world->slot,static_cast<unsigned long long>(tc.fuel0));
#endif
                    tc.guard(); cambc::end_turn(); continue;
                }
            }
            if (world->ready&&dz::tier_for(cambc::fuel_remaining())==dz::Tier::Fallback) {
                dz::module_work(recovery_health,tc,counts,"recovery",[&]{dz::quick_home(*world,tc,act);});
                tc.guard(); cambc::end_turn(); continue;
            }
            if (!dz::module_work(observation_health,tc,counts,"observation",[&]{obs->read(tc);})) {
                if (cambc::round_number()==tc.round) cambc::end_turn();
                continue;
            }
            if (obs->state.is_dead()) {
#if DZ_TRACE
                ++dz_time[10];
#endif
                dz::module_work(shop_health,tc,counts,"shop",[&]{dz::fixed_shop(tc, act);});
            }
            else {
                const bool already_ready = world->ready;
                if (!dz::module_work(boot_health,tc,counts,"boot",[&]{world->boot(tc);})) {
                    if (cambc::round_number()==tc.round) cambc::end_turn();
                    continue;
                }
#if DZ_TRACE
                if (tc.round <= 8) std::printf("DZ_BOOT round=%u slot=%u ready=%d fuel=%llu\n", tc.round, world->slot, world->ready,
                    static_cast<unsigned long long>(cambc::fuel_remaining()));
#endif
                if (world->ready && already_ready) {
                    if (!priority_set) priority_set = act.priority(100 - static_cast<int>(world->slot));
                    const bool shop_attempted=shop_health.enabled();
                    const bool shop_ok=dz::module_work(shop_health,tc,counts,"shop",[&]{if (dz::fixed_shop(tc,act)) obs->refresh_self(tc);});
                    // A shop exception can follow a successful purchase. Refresh
                    // before planning with stats that may have changed partially.
                    if (shop_attempted&&!shop_ok && !dz::module_work(observation_health,tc,counts,"observation",[&]{obs->refresh_self(tc);})) {
                        if (cambc::round_number()==tc.round) cambc::end_turn();
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
                    if (!camps_ok || dz::tier_for(cambc::fuel_remaining())==dz::Tier::Fallback ||
                        !dz::module_work(memory_health,tc,counts,"memory",[&]{mem->update(*world,tc);})) {
                        emergency(*world,*obs,tc,act);
                        clear_claim();
                    } else {
#if DZ_TRACE
                        if (tc.round <= 8) std::printf("DZ_MEMORY round=%u slot=%u fuel=%llu\n", tc.round, world->slot,
                            static_cast<unsigned long long>(cambc::fuel_remaining()));
#endif
                        dz::Goal goal;
#if DZ_TRACE
                        const auto planner_fuel=cambc::fuel_remaining();
#endif
                        if (!dz::module_work(planner_health,tc,counts,"planner",[&]{goal=dz::safe_goal(*world,*mem,*obs,tc);})) {
                            emergency(*world,*obs,tc,act);
                            clear_claim();
                            if (cambc::round_number()==tc.round) cambc::end_turn();
                            continue;
                        }
#if DZ_TRACE
                        if (tc.round > 8 && planner_fuel-cambc::fuel_remaining() > 15000)
                            std::printf("DZ_PLANNER_FUEL round=%u slot=%u used=%llu entry=%llu kind=%d\n",tc.round,world->slot,
                                static_cast<unsigned long long>(planner_fuel-cambc::fuel_remaining()),static_cast<unsigned long long>(tc.fuel0),static_cast<int>(goal.kind));
                        if (!obs->enemies.empty()) {
                            int nearest=99; unsigned allies6=0; float reach_str=0,reach_hp=0;
                            for (const auto& e:obs->enemies) {
                                const int d=obs->p.chebyshev_distance(e.p);
                                nearest=std::min(nearest,d);
                                if (d<=e.range) { reach_str+=e.strength; reach_hp+=e.hp; }
                            }
                            for (const auto& a:obs->allies) allies6+=obs->p.chebyshev_distance(a.p)<=6;
                            std::printf("DZ_FIGHT round=%u slot=%u kind=%d hp=%.0f max=%.0f enemies=%zu nearest=%d allies6=%u pos=%d,%d reach_str=%.0f reach_hp=%.0f str=%.0f\n",
                                tc.round,world->slot,static_cast<int>(goal.kind),obs->hp,obs->max_hp,obs->enemies.size(),nearest,allies6,obs->p.x,obs->p.y,reach_str,reach_hp,obs->strength);
                        }
                        if (tc.round <= 8 || tc.round % 100 == 0 || (world->slot==DZ_TRACE_SLOT && tc.round>=DZ_TRACE_FROM && tc.round<DZ_TRACE_TO)) std::printf("DZ_GOAL round=%u slot=%u kind=%d index=%d pos=%d,%d bag=%d hp=%.0f altar0=%d\n",
                            tc.round, world->slot, static_cast<int>(goal.kind), goal.index, obs->p.x, obs->p.y, obs->bag, obs->hp,
                            world->altars.empty() ? -1 : world->altar_distance(0, obs->p));
                        if (tc.round%100==0 && goal.kind==dz::GoalKind::Farm) {
                            const auto& b=mem->groups[goal.index];
                            std::printf("DZ_FARM round=%u slot=%u state=%d hp=%.0f capture=%d seen=%d checked=%d\n",
                                tc.round,world->slot,static_cast<int>(b.state),b.hp,b.capture,b.seen,mem->contract.checked);
                        }
#endif
                        bool executed=dz::module_work(execution_health,tc,counts,"executor",[&] {
                            if (obs->channel()) {
                                if (goal.kind==dz::GoalKind::Retreat && act.cancel_channel()) dz::execute(goal,*world,*mem,*obs,tc,act);
                            } else dz::execute(goal,*world,*mem,*obs,tc,act);
                        });
                        if (!executed) emergency(*world,*obs,tc,act);
#if DZ_TRACE
                        if (obs->channel()) ++dz_time[9];
                        else if (goal.kind==dz::GoalKind::Farm) {
                            const auto here=cambc::self().position();
                            const bool site=world->distance(goal.index,here)<=std::max(1,obs->range)||world->group_at(here)==goal.index;
                            ++dz_time[!site?0:mem->groups[goal.index].state==dz::GroupState::Reward?2:1];
                        } else ++dz_time[std::min<std::size_t>(10,static_cast<std::size_t>(goal.kind)+2)];
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
                        else if (goal.kind == dz::GoalKind::Home) objective = dz::protocol::shop;
                        else if (goal.kind == dz::GoalKind::Retreat) objective = dz::protocol::retreat;
                        act.publish(dz::protocol::with_slot(dz::shared_word(), world->slot, {objective, onsite}));
                        });
                        dz::module_work(field_health,tc,counts,"fields",[&]{world->build_one_field(tc,mem->contract.objective);});
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
            if (counts.module_errors <= 20) std::printf("DZ_MODULE_ERROR round=%u %s\n", tc.round, error.what());
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
        cambc::end_turn();
    }
}
