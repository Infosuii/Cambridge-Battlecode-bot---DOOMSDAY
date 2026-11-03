#pragma once

#if GX_HOT_CACHE > 0
#include <bit>
namespace gx {
struct HotGroup {
    std::uint64_t members = 0;
    std::optional<bc::bitboard> mask;
};

inline void build_hot_zone(World& w) {
    static std::vector<HotGroup> cache;
    w.hot_zone.clear();
    for (std::size_t gi = 0; gi < w.groups.size(); ++gi) {
        const auto& g = w.groups[gi];
        if (g.state != GroupState::alive || g.harmless) continue;
        std::uint64_t live = 0, injured = 0;
        bool awake = false;
        for (std::size_t k = 0; k < g.camps.size(); ++k) {
            const auto& c = w.camps[static_cast<std::size_t>(g.camps[k])];
            const bool hurt = c.hp < c.max_hp;
            awake |= c.dead || hurt;
            if (!c.dead && c.strength > 0.0f) {
                const std::uint64_t bit = std::uint64_t{1} << k;
                live |= bit;
                if (hurt) injured |= bit;
            }
        }
        const std::uint64_t members = tune::kAwakeZone && awake ? live : injured;
        if (!members) continue;
        if (cache.size() != w.groups.size()) cache.resize(w.groups.size());
        auto& c = cache[gi];
        if (c.members != members) {
            if (!c.mask) c.mask.emplace();
            else c.mask->clear();
            for (std::uint64_t left = members; left; left &= left - 1) {
                const auto& camp = w.camps[static_cast<std::size_t>(g.camps[std::countr_zero(left)])];
                c.mask->draw_chebyshev(camp.pos, static_cast<float>(camp.range));
            }
            c.members = members;
        }
        w.hot_zone |= *c.mask;
    }
}
} // namespace gx
#endif
