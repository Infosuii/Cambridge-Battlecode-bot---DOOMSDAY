#pragma once
#include "core.h"
#include "protocol.h"
#include <cambc.h>

namespace dz {
struct TurnContext {
    std::uint32_t round;
    std::uint64_t fuel0;
    static TurnContext begin() { return {cambc::round_number(), cambc::fuel_remaining()}; }
    void guard() const { require_current(round, [] { return cambc::round_number(); }); }
    bool allow(std::uint64_t cost) const {
        guard();
        return cambc::fuel_remaining() > cost + config::reserve;
    }
};
struct Counters { unsigned action_errors = 0, module_errors = 0, stale = 0; };
// Every bot-side SDK mutation (including draft and communication) passes through
// this boundary. Callers check legality; the boundary rejects stale resumption.
class Actuator {
    const TurnContext& tc_;
    Counters& counts_;
    unsigned failures_ = 0;
public:
    Actuator(const TurnContext& tc, Counters& counts) : tc_(tc), counts_(counts) {}
    template<class F> bool attempt(F action) {
        if (failures_ >= config::max_action_errors || !tc_.allow(1500)) return false;
        try {
            tc_.guard();
            bool success = true;
            if constexpr (std::is_same_v<std::invoke_result_t<F>, bool>) success = action();
            else action();
            tc_.guard();
            return success;
        } catch (const cambc::error& error) {
            ++failures_; ++counts_.action_errors;
#if DZ_TRACE
            if (counts_.action_errors <= 20) std::printf("DZ_ACTION_ERROR round=%u code=%d %s\n", tc_.round, static_cast<int>(error.code()), error.what());
#endif
            return false;
        }
    }
    bool move(cambc::vec2 p) { return attempt([&] { return cambc::self().move_absolute(p); }); }
    bool attack(const cambc::unit& u) { return attempt([&] { cambc::self().attack(u); }); }
    bool attack(const cambc::altar_lock& u) { return attempt([&] { cambc::self().attack(u); }); }
    bool cast(const cambc::ability& a) { return attempt([&] { return a.use(); }); }
    bool cast(const cambc::ability& a, const cambc::unit& target) {
        return attempt([&] {
            if (const auto* c = dynamic_cast<const cambc::champion*>(&target)) return a.use(*c);
            return a.use(dynamic_cast<const cambc::camp&>(target));
        });
    }
    bool cast(const cambc::ability& a, cambc::vec2 p) { return attempt([&] { return a.use(p); }); }
    bool recall() { return attempt([] { cambc::self().recall(); }); }
    bool cancel_channel() {
        const auto state = cambc::self().state();
        if (state.contains(cambc::champion_state::recalling)) return attempt([] { cambc::self().cancel_recall(); });
        if (state.contains(cambc::champion_state::submitting_gems)) return attempt([] { cambc::self().cancel_submit_gems(); });
        return false;
    }
    bool bank(cambc::vec2 p) { return attempt([&] { cambc::self().submit_gems(p); }); }
    bool buy(cambc::item_type item) { return attempt([&] { cambc::self().buy(item); }); }
    bool ward(cambc::vec2 p) { return attempt([&] { return cambc::self().place_ward(p); }); }
    bool priority(int p) { return attempt([&] { cambc::self().set_priority(p); }); }
    bool pick(cambc::champion_draft p) { return attempt([&] { cambc::draft::pick(p); }); }
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
