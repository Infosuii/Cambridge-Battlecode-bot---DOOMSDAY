#pragma once

#if GX_CAMP_AIM > 0
namespace gx {
struct CampAim {
    vec2 tile;
    int hits;
};

inline CampAim camp_aim(World& w, int gi, vec2 me, vec2 target, int cast_range, int radius, float damage) {
    CampAim best{target, 0};
    if (gi < 0) return best;
    const auto& group = w.groups[static_cast<std::size_t>(gi)];
    auto quote = [&](vec2 aim, int& hits, int& kills) {
        float effective = 0;
        hits = kills = 0;
        for (int j : group.camps) {
            const auto& c = w.camps[static_cast<std::size_t>(j)];
            if (c.dead || cheb(c.pos, aim) > radius) continue;
            ++hits;
            kills += c.hp <= damage;
            effective += std::min(c.hp, damage);
        }
        return effective;
    };
    int old_kills = 0;
    float old_effective = quote(target, best.hits, old_kills);
    if (cheb(me, target) > cast_range) best.hits = 0, old_kills = 0, old_effective = 0;
    if (best.hits == static_cast<int>(group.camps.size()) || group.camps.size() < 3 || group.camps.size() > 18 ||
        !w.enemies.empty() || radius < 1 || radius > 3 ||
        bc::fuel_remaining() < 30000 + 350 * group.camps.size()) return best;
    const int old_hits = best.hits;
    float best_effective = old_effective;
    // Short offsets cover the common two-row groups. Use up to two tiles for
    // a cast whose centre would otherwise be out of range.
    const int shift = std::min(radius, GX_CAMP_AIM >= 2 && best.hits == 0 ? 2 : 1);
    for (int dy = -shift; dy <= shift; ++dy) {
        if (bc::fuel_remaining() < 22000) return best;
        for (int dx = -shift; dx <= shift; ++dx) {
            const vec2 aim{target.x + dx, target.y + dy};
            if ((aim.x < 0 || aim.y < 0 || aim.x >= w.width || aim.y >= w.height) || cheb(me, aim) > cast_range ||
                !bit(w.visible, aim) || bit(w.static_blocked, aim)) continue;
            int hits = 0, kills = 0;
            const float effective = quote(aim, hits, kills);
            if (effective <= best_effective || (hits < old_hits + 2 && kills <= old_kills) ||
                effective < old_effective * 1.12f) continue;
            // Do not wake a second group to gain one extra hit on this one.
            bool foreign = false;
            for (int y = -radius; y <= radius && !foreign; ++y)
                for (int x = -radius; x <= radius && !foreign; ++x) {
                    const int other = w.group_of_camp_tile({aim.x+x, aim.y+y});
                    if (other >= 0 && other != gi) {
                        const auto& g = w.groups[static_cast<std::size_t>(other)];
                        foreign = !g.harmless && g.state == GroupState::alive;
                    }
                }
            if (!foreign) best = {aim, hits}, best_effective = effective;
        }
    }
    return best;
}
} // namespace gx
#endif
