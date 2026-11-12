#pragma once

#if GX_SHADOW_BAG > 0
namespace gx {
inline const AllyRec* carrier_needing_cover(const World& w, vec2 here) {
    const AllyRec* best = nullptr;
    std::uint32_t largest = GX_SHADOW_BAG - 1;
    for (const auto& ally : w.allies) {
        if (ally.hp <= 0.0f || cheb(here, ally.pos) > 6) continue;
        bool threatened = false;
        for (const auto& enemy : w.enemies)
            threatened |= enemy.hp > 0.0f && !enemy.tributing() && cheb(enemy.pos, ally.pos) <= enemy.range + 3;
        if (!threatened) continue;
        std::uint32_t gems = 0;
        if (cambc::detail::sdk_champion_gems(ally.id, &gems) == 0 && gems > largest)
            best = &ally, largest = gems;
    }
    return best;
}
} // namespace gx
#endif
