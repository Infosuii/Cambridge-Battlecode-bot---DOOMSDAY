#include "draft.h"
#include "map_signature.h"

namespace dz {
void draft_loop(Counters& counts) {
    using D = cambc::champion_draft;
    // Research prior only; map-conditioned exhaustive utility is a later gate.
    // All three sizes have a legal frontline, damage/reset kit and banker.
    // Candidate lineups for the per-map draft study (DZ_DRAFT_VARIANT):
    // 0 current prior; 1 elite core Vesper/Heart/Vendetta/Marcella; 2 Ryth/
    // Vendetta/Marcella (beat the core on arena/fragment); 3 Vesper/Vendetta/Varg.
    using Order = std::array<D,6>;
    const std::array<Order,4> variants{{
        {D::vendetta, D::varg, D::marcella, D::vesper_vale, D::heart_of_ruin, D::ryth},
        {D::vesper_vale, D::heart_of_ruin, D::vendetta, D::marcella, D::ryth, D::varg},
        {D::ryth, D::vendetta, D::marcella, D::vesper_vale, D::heart_of_ruin, D::varg},
        {D::vesper_vale, D::vendetta, D::varg, D::marcella, D::heart_of_ruin, D::ryth}}};
    // Per-map variant table (signature -> variant), chosen by
    // tools/dz_draft_select.py and confirmed out of sample. Empty = default.
    struct MapDraft { std::uint32_t signature; std::uint8_t variant; };
    static constexpr MapDraft map_drafts[] = {
#include "map_drafts.inc"
    };
    int variant = DZ_DRAFT_VARIANT % 4;
    try {
        const auto signature = map_signature(); // First draft turn: 10x budget.
        for (const auto& row : map_drafts) if (row.signature == signature && DZ_DRAFT_VARIANT == 0) variant = row.variant;
#if DZ_TRACE
        std::printf("DZ_SIG signature=%u variant=%d\n", signature, variant);
#endif
    } catch (...) {}
    const Order order3 = variants[variant];
    Order order5 = order3;
    if (variant == 0) order5 = {D::vendetta, D::varg, D::vesper_vale, D::marcella, D::heart_of_ruin, D::ryth};
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
        catch (const std::exception& error) {
            ++counts.module_errors;
#if DZ_TRACE
            std::printf("DZ_MODULE_ERROR round=%u module=draft %s\n",tc.round,error.what());
#endif
        }
        catch (...) {
            ++counts.module_errors;
#if DZ_TRACE
            std::printf("DZ_MODULE_ERROR round=%u module=draft unknown exception\n",tc.round);
#endif
        }
        if (cambc::round_number() != tc.round) continue;
        cambc::end_turn();
    }
}
}
