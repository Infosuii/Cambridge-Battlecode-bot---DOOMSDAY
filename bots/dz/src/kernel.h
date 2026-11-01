#pragma once
#include "core.h"
#include "protocol.h"
#include <cambc.h>
#include "trace.h"

namespace dz {
// End the turn; trace builds first write buffered trace lines from spare fuel.
inline void end_turn_traced() {
#if DZ_TRACE
    trace_flush(cambc::round_number()>=cambc::constants::max_rounds?0:30000);
#endif
    cambc::end_turn();
}
struct TurnContext {
    std::uint32_t round;
    std::uint64_t fuel0;
#if DZ_ECONOMY_V2
    std::uint64_t protected_fuel=0;
    TurnContext keep(std::uint64_t fuel) const {auto result=*this;result.protected_fuel=std::max(result.protected_fuel,fuel);return result;}
#endif
    static TurnContext begin() { trace_meter.reset(); return {cambc::round_number(), fuel_left()}; }
    void guard() const { require_current(round, [] { return cambc::round_number(); }); }
    bool allow(std::uint64_t cost) const {
        guard();
        return fuel_left() > cost + config::reserve
#if DZ_ECONOMY_V2
            +protected_fuel
#endif
            ;
    }
};
struct Counters { unsigned action_errors = 0, module_errors = 0, stale = 0; };
template<class Work>
bool module_work(ModuleHealth& health,const TurnContext& tc,Counters& counts,[[maybe_unused]] const char* name,Work work) {
    return guarded_module(health,[&] {
        tc.guard();
        try { work(); }
        catch (...) { tc.guard(); throw; } // A resumed SDK error is still a stale turn.
        tc.guard();
    },[&]([[maybe_unused]] const char* error) {
        ++counts.module_errors;
#if DZ_TRACE
        ::dz::trace("DZ_MODULE_ERROR round=%u body=%d module=%s failures=%u disabled=%d %s\n",
            tc.round,cambc::detail::cached_my_champion,name,health.failures,!health.enabled(),error);
#endif
    });
}
// Every bot-side SDK mutation (including draft and communication) passes through
// this boundary. Callers check legality; the boundary rejects stale resumption.
class Actuator {
    const TurnContext& tc_;
    Counters& counts_;
    ActionBudget budget_;
    unsigned failures_ = 0;
    ActionHistory history_;
    bool last_move_blocked_=false;
    static bool channel(cambc::champion_state s) {
        return s.contains(cambc::champion_state::recalling) || s.contains(cambc::champion_state::submitting_gems) ||
            s.contains(cambc::champion_state::teleporting);
    }
    bool can_attack() const {
        auto& me = cambc::self(); auto s = me.state();
        return !s.is_dead() && !channel(s) && s.contains(cambc::champion_state::can_attack) &&
            !me.restrictions().contains(cambc::buff_restrictions::attack);
    }
    template<class F> bool cast_checked(const cambc::ability& a, F use) {
        return attempt([&] {
            if (!a.info()) return false;
            const bool exclusive = std::visit([](const auto& p) { return p.exclusive_with_movement; }, *a.info());
            auto& me = cambc::self(); auto s = me.state();
            if (s.is_dead() || a.cooldown() > 0 || !history_.may_cast(s.contains(cambc::champion_state::can_cast),
                me.restrictions().contains(cambc::buff_restrictions::cast), channel(s), exclusive)) return false;
            tc_.guard();
            bool success = use(); history_.record_cast(success, exclusive); return success;
        });
    }
public:
    Actuator(const TurnContext& tc, Counters& counts) : tc_(tc), counts_(counts),budget_(ActionBudget::Normal) {}
    void use_emergency_budget() { budget_=ActionBudget::Emergency; }
    template<class F> bool attempt(F action,[[maybe_unused]] const char* name="action") {
        tc_.guard();
        if (failures_ >= config::max_action_errors || !action_budget_available(fuel_left(),budget_)) return false;
        try {
            tc_.guard();
            bool success = true;
            if constexpr (std::is_same_v<std::invoke_result_t<F>, bool>) success = action();
            else action();
            tc_.guard();
            return success;
        } catch (const cambc::error& error) {
            tc_.guard();
            ++failures_; ++counts_.action_errors;
#if DZ_TRACE
            if (counts_.action_errors <= 20) ::dz::trace("DZ_ACTION_ERROR round=%u action=%s code=%d %s\n", tc_.round, name, static_cast<int>(error.code()), error.what());
#endif
            return false;
        }
    }
    bool move(cambc::vec2 p) {
        last_move_blocked_=false;
        return attempt([&] {
            auto& me = cambc::self(); auto s = me.state();
            if (s.is_dead() || !cambc::map::is_in_bounds(p) || me.position().chebyshev_distance(p) != 1 ||
                !history_.may_move(s.contains(cambc::champion_state::can_move),
                    me.restrictions().contains(cambc::buff_restrictions::move), channel(s))) return false;
            tc_.guard(); bool success = me.move_absolute(p); last_move_blocked_=!success;
            history_.record_move(success); return success;
        });
    }
    bool last_move_blocked() const { return last_move_blocked_; }
    bool attack(const cambc::unit& u) {
        return attempt([&] {
            if (!can_attack() || !u.is_visible() || u.health() <= 0 ||
                cambc::self().position().chebyshev_distance(u.position()) > cambc::self().attack_range()) return false;
            tc_.guard(); cambc::self().attack(u); return true;
        });
    }
    bool attack(const cambc::altar_lock& u) {
        return attempt([&] {
            if (!u.is_enemy() || !can_attack() ||
                cambc::self().position().chebyshev_distance(u.position()) > cambc::self().attack_range()) return false;
            tc_.guard(); cambc::self().attack(u); return true;
        });
    }
    bool cast(const cambc::ability& a) { return cast_checked(a, [&] { return a.use(); }); }
    bool cast(const cambc::ability& a, const cambc::unit& target) {
        return cast_checked(a, [&] {
            if (const auto* c = dynamic_cast<const cambc::champion*>(&target)) return a.use(*c);
            return a.use(dynamic_cast<const cambc::camp&>(target));
        });
    }
    bool cast(const cambc::ability& a, cambc::vec2 p) { return cast_checked(a, [&] { return a.use(p); }); }
    bool recall() { return attempt([&] {
        auto& me=cambc::self(); auto state=me.state();
        if (state.is_dead()||channel(state)||me.buffs().has_stun()) return false;
        tc_.guard(); me.recall(); return true;
    },"recall"); }
    bool cancel_channel() {
        const auto state = cambc::self().state();
        if (state.contains(cambc::champion_state::recalling)) return attempt([] { cambc::self().cancel_recall(); });
        if (state.contains(cambc::champion_state::submitting_gems)) return attempt([] { cambc::self().cancel_submit_gems(); });
        return false;
    }
    bool bank(cambc::vec2 p) { return attempt([&] {
        auto& me=cambc::self(); auto state=me.state();
        if (state.is_dead()||channel(state)||me.buffs().has_stun()||me.gem_count()==0 ||
            me.position().chebyshev_distance(p)>cambc::constants::submit_gems_range) return false;
        for (const auto& lock:cambc::vision::altar_locks(cambc::team::enemy)) if (lock.position()==p &&
            (!can_attack() || me.position().chebyshev_distance(p)>me.attack_range())) return false;
        tc_.guard(); me.submit_gems(p); return true;
    },"bank"); }
    bool buy(cambc::item_type item) { return attempt([&] { cambc::self().buy(item); }); }
    bool ward(cambc::vec2 p) { return attempt([&] { return cambc::self().place_ward(p); }); }
    bool priority(int p) { return attempt([&] { cambc::self().set_priority(p); }); }
    bool pick(cambc::champion_draft p) { return attempt([&] { cambc::draft::pick(p); }); }
    bool draft_bytes(std::span<const std::byte> bytes) { return attempt([&] { cambc::draft_memory=bytes; }); }
    bool publish(std::uint64_t word) {
        return attempt([&] { cambc::shared_memory.write(0, std::span<const std::uint64_t>(&word, 1)); });
    }
};
inline std::uint64_t shared_word() {
    std::uint64_t word{};
    cambc::shared_memory.read(0, std::span<std::uint64_t>(&word, 1));
    return word;
}
}
