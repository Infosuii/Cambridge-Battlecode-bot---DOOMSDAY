#include "draft.h"
#include "gear.h"
#include "safemode.h"

int main() {
    dz::Counters counts;
    if (cambc::is_draft()) dz::draft_loop(counts);
    // Construct inside the boundary: allocations and SDK-backed mask constructors
    // can throw. A failed startup is retried next turn, never a permanent trap.
    std::unique_ptr<dz::StaticWorld> world;
    std::unique_ptr<dz::Memory> mem;
    std::unique_ptr<dz::Observation> obs;
    bool priority_set = false;
    for (;;) {
        auto tc = dz::TurnContext::begin(); dz::Actuator act(tc, counts);
#if DZ_TRACE
        if (tc.round % 100 == 0) std::printf("DZ_COUNTS round=%u slot=%u actions=%u modules=%u stale=%u\n",
            tc.round, world ? world->slot : 0, counts.action_errors, counts.module_errors, counts.stale);
#endif
        try {
            if (!world) world = std::make_unique<dz::StaticWorld>();
            if (!mem) mem = std::make_unique<dz::Memory>();
            if (!obs) obs = std::make_unique<dz::Observation>();
            obs->read(tc);
            if (obs->state.is_dead()) { dz::fixed_shop(tc, act); }
            else {
                const bool already_ready = world->ready;
                world->boot(tc);
#if DZ_TRACE
                if (tc.round <= 8) std::printf("DZ_BOOT round=%u slot=%u ready=%d fuel=%llu\n", tc.round, world->slot, world->ready,
                    static_cast<unsigned long long>(cambc::fuel_remaining()));
#endif
                if (world->ready && already_ready) {
                    if (!priority_set) priority_set = act.priority(100 - static_cast<int>(world->slot));
                    if (dz::fixed_shop(tc, act)) obs->refresh_self(tc);
                    if constexpr (dz::config::camp_safety) obs->read_camps(*world,tc);
                    if (dz::tier_for(cambc::fuel_remaining()) == dz::Tier::Fallback) {
                        // Hard-budget escape: no memory scan, field build or full planner.
                        bool banking=false;
                        if (!obs->channel() && obs->bag>0 && dz::danger(obs->p,*obs)==0) {
                            for (const auto& altar:world->altars) if (obs->p.chebyshev_distance(altar.tile)<=cambc::constants::submit_gems_range) {
                                banking=act.bank(altar.tile); break;
                            }
                        }
                        if (!banking && !obs->channel() && cambc::self().can_move()) {
                            for (auto delta : world->home.next_moves_from(obs->p)) {
                                auto p = obs->p + delta;
                                if (!obs->occupied.is_set(p)) { act.move(p); break; }
                            }
                        }
                    } else {
                        mem->update(*world, tc);
#if DZ_TRACE
                        if (tc.round <= 8) std::printf("DZ_MEMORY round=%u slot=%u fuel=%llu\n", tc.round, world->slot,
                            static_cast<unsigned long long>(cambc::fuel_remaining()));
#endif
                        const auto goal = dz::safe_goal(*world, *mem, *obs, tc);
#if DZ_TRACE
                        if (tc.round <= 8 || tc.round % 100 == 0) std::printf("DZ_GOAL round=%u slot=%u kind=%d index=%d pos=%d,%d bag=%d hp=%.0f altar0=%d\n",
                            tc.round, world->slot, static_cast<int>(goal.kind), goal.index, obs->p.x, obs->p.y, obs->bag, obs->hp,
                            world->altars.empty() ? -1 : world->altar_distance(0, obs->p));
                        if (tc.round%100==0 && goal.kind==dz::GoalKind::Farm) {
                            const auto& b=mem->groups[goal.index];
                            std::printf("DZ_FARM round=%u slot=%u state=%d hp=%.0f capture=%d seen=%d checked=%d\n",
                                tc.round,world->slot,static_cast<int>(b.state),b.hp,b.capture,b.seen,mem->contract.checked);
                        }
#endif
                        if (obs->channel()) {
                            if (goal.kind == dz::GoalKind::Retreat) {
                                if (act.cancel_channel()) dz::execute(goal, *world, *mem, *obs, tc, act);
                            }
                        } else dz::execute(goal, *world, *mem, *obs, tc, act);
                        std::uint8_t objective = dz::protocol::idle;
                        bool onsite = false;
                        if (goal.kind == dz::GoalKind::Farm) {
                            objective = dz::protocol::group_code(goal.index);
                            const auto position = cambc::self().position();
                            onsite = world->group_at(position)==goal.index;
                        } else if (goal.kind == dz::GoalKind::Bank) objective = goal.index < 8 ? 112 + goal.index : dz::protocol::idle;
                        else if (goal.kind == dz::GoalKind::Home) objective = dz::protocol::shop;
                        else if (goal.kind == dz::GoalKind::Retreat) objective = dz::protocol::retreat;
                        act.publish(dz::protocol::with_slot(dz::shared_word(), world->slot, {objective, onsite}));
                        world->build_one_field(tc, mem->contract.objective);
                    }
                }
            }
            if (obs->state.is_dead() && world->ready)
                act.publish(dz::protocol::with_slot(dz::shared_word(), world->slot, {dz::protocol::dead, false}));
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
