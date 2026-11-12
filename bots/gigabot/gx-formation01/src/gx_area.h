#pragma once
#include "common.h"
#include "gx_config.h"

#if GX_FORMATION
namespace gx_formation {
inline volatile unsigned action = 1000u + GX_FORM_ARM;

struct Spec {
    int range = 0, radius = 0;
    float damage = 0.0f;
    bool stun = false, dash = false;
};

inline const std::array<Spec,2>& specs(bc::champion_type type) {
    struct Entry { bool loaded = false; std::array<Spec,2> values{}; };
    static Entry cache[16];
    auto& entry = cache[std::clamp(static_cast<int>(type),0,15)];
    if (entry.loaded) return entry.values;
    entry.loaded = true;
    try {
        const bc::champion design{type};
        const auto abilities = design.abilities();
        for (int s = 0; s < 2; ++s) {
            const auto& info = abilities[s].info();
            if (!info) continue;
            if (const auto* a = std::get_if<bc::ability_aoe_damage>(&*info)) {
                if (!abilities[s].can_target_enemies() || a->radius < 1.0f) continue;
                entry.values[s] = {static_cast<int>(a->range),static_cast<int>(a->radius),a->modifier,a->duration > 0,false};
            } else if (const auto* a = std::get_if<bc::ability_dash>(&*info)) {
                if (a->radius < 1.0f || (a->modifier <= 0.0f && a->duration <= 0)) continue;
                entry.values[s] = {static_cast<int>(a->range),static_cast<int>(a->radius),a->modifier,a->duration > 0,true};
            }
        }
    } catch (...) {}
    return entry.values;
}

struct Footprint {
    vec2 enemy;
    int reach, radius;
    float risk;
    bool splash;
};

// Chebyshev disks are rectangles. Intersection is a possible spell center that
// covers both friends and can be reached by the visible caster.
inline bool both(const Footprint& f, vec2 a, vec2 b) {
    if (f.splash)
        return cheb(a,b) <= f.radius && std::min(cheb(a,f.enemy),cheb(b,f.enemy)) <= f.reach;
    return std::max({a.x - f.radius,b.x - f.radius,f.enemy.x - f.reach}) <=
           std::min({a.x + f.radius,b.x + f.radius,f.enemy.x + f.reach}) &&
           std::max({a.y - f.radius,b.y - f.radius,f.enemy.y - f.reach}) <=
           std::min({a.y + f.radius,b.y + f.radius,f.enemy.y + f.reach});
}
}  // namespace gx_formation
#endif
