#include "draft.h"

namespace dz {
void draft_loop(Counters& counts) {
    using D = cambc::champion_draft;
    // Research prior only; map-conditioned exhaustive utility is a later gate.
    // All three sizes have a legal frontline, damage/reset kit and banker.
    const std::array order3{D::heart_of_ruin, D::vendetta, D::marcella, D::vesper_vale, D::ryth};
    const std::array order5{D::vesper_vale, D::heart_of_ruin, D::vendetta, D::marcella, D::ryth};
    bool initialized = false;
    for (;;) {
        const auto tc = TurnContext::begin(); Actuator act(tc, counts);
        try {
            auto picks = cambc::draft::current_draft(cambc::team::ally);
            const auto& order = cambc::draft::team_size() == 3 ? order3 : order5;
            auto next = order.front();
            for (auto option : order) if (std::find(picks.begin(), picks.end(), option) == picks.end()) { next = option; break; }
            act.pick(next); // Pick before any optional work, including shared initialization.
            if (!initialized) initialized = act.publish(protocol::empty_word());
        } catch (const StaleTurn&) { ++counts.stale; continue; }
        catch (...) { ++counts.module_errors; }
        if (cambc::round_number() != tc.round) continue;
        cambc::end_turn();
    }
}
}
