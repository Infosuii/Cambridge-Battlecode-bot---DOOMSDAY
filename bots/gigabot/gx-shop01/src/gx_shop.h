#pragma once

#if GX_SHOP_MILESTONE > 0
namespace gx {
int milestone_gold(bc::champion_type type) {
    const auto counts = bc::self().item_count();
    const auto plan = build_for(type);
    bool first_complete = false;
    for (const auto& step : plan) {
        int owned = static_cast<int>(counts[step.item]);
        const auto emblem = step.item.result();
        const int combine = emblem ? std::max(1, static_cast<int>(step.item.combine_count())) : 1;
        if (emblem) owned += combine * static_cast<int>(counts[*emblem]);
        if (owned < step.total) {
            if (!emblem) return 0;
            const int want = std::min(step.total - owned, combine - owned % combine);
            const int reserve = first_complete ? 20 : 0; // shop can top up a lock and a crystal first
            return want * static_cast<int>(step.item.cost()) + reserve;
        }
        first_complete = true;
    }
    return 0;
}
} // namespace gx
#endif
