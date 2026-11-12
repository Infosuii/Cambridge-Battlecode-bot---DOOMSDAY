#pragma once

#if GX_HOT_CACHE > 0
#include <bit>
namespace gx {
struct HotGroup {
    std::uint64_t members = 0;
    std::optional<bc::bitboard> mask;
};

inline bool add_cached_hot_group(World& w, const GroupRec& g) {
    static std::vector<HotGroup> cache;
    if (g.camps.size() < 8) return false;
    const auto gi = static_cast<std::size_t>(&g - w.groups.data());
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
    if (!members) return true;
    if (cache.size() != w.groups.size()) cache.resize(w.groups.size());
    auto& c = cache[gi];
    if (c.members != members) {
        // A turn can suspend while drawing; do not leave an old valid key
        // pointing at a partially rebuilt mask.
        c.members = 0;
        if (!c.mask) c.mask.emplace();
        else c.mask->clear();
        for (std::uint64_t left = members; left; left &= left - 1) {
            const auto& camp = w.camps[static_cast<std::size_t>(g.camps[std::countr_zero(left)])];
            c.mask->draw_chebyshev(camp.pos, static_cast<float>(camp.range));
        }
        c.members = members;
    }
    w.hot_zone |= *c.mask;
#if GX_HOT_CACHE >= 2
    static bool gx_logged = false;
    if (!gx_logged) {
        gx_logged = true;
        std::printf("GXHOT checked members=%zu\n",g.camps.size());
    }
#endif
    return true;
}
} // namespace gx
#endif
