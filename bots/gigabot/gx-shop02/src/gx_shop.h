#pragma once

#if GX_SHOP_MILESTONE > 0
namespace gx {
int milestone_gold(bc::champion_type type) {
    const auto counts = bc::self().item_count();
    const auto plan = build_for(type);
    for (const auto& step : plan) {
        int owned = static_cast<int>(counts[step.item]);
        const auto emblem = step.item.result();
        const int combine = emblem ? std::max(1, static_cast<int>(step.item.combine_count())) : 1;
        if (emblem) owned += combine * static_cast<int>(counts[*emblem]);
        if (owned < step.total) {
            if (!emblem) return 0;
            const int want = std::min(step.total - owned, combine - owned % combine);
            return want * static_cast<int>(step.item.cost());
        }
        return 0; // Only the opening emblem changes the trip.
    }
    return 0;
}
} // namespace gx
#endif
