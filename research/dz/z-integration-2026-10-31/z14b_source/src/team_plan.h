#pragma once
#include "plan.h"
#include "static_world.h"
#include <vector>
// A1 whole-team plans (lab4: team-plan switches flip lost games where single decisions don't). Each plan bundles
// existing terms: which half's groups are worth working, and how readily a won local fight is engaged.
namespace dz {
#if DZ_HAS(HOME) || DZ_HAS(TURTLE)
// Static: a group is in the enemy half when its centre is strictly nearer the enemy spawn centroid.
inline bool enemy_half(const StaticWorld& world, unsigned g) {
    static std::vector<signed char> side;
    if (side.size() != world.groups.size()) {
        auto centroid = [](cambc::team t) {
            long long x = 0, y = 0, n = 0;
            for (auto p : cambc::map::spawn_region(t).positions()) { x += p.x; y += p.y; ++n; }
            return vec2{static_cast<int>(x / (n ? n : 1)), static_cast<int>(y / (n ? n : 1))};
        };
        const auto a = centroid(cambc::team::ally), e = centroid(cambc::team::enemy);
        auto d2 = [](vec2 p, vec2 q) { const long long dx = p.x - q.x, dy = p.y - q.y; return dx * dx + dy * dy; };
        side.assign(world.groups.size(), 0);
        for (unsigned i = 0; i < side.size(); ++i) side[i] = d2(world.groups[i].center, e) < d2(world.groups[i].center, a);
    }
    return side[g] != 0;
}
#endif
// Job value multiplier for group g under the active plan (0 drops it).
inline float half_weight([[maybe_unused]] const StaticWorld& world, [[maybe_unused]] unsigned g) {
#if DZ_HAS(HOME) || DZ_HAS(TURTLE)
    if ((DZ_ON(HOME) || DZ_ON(TURTLE)) && enemy_half(world, g)) return DZ_ON(TURTLE) ? 0.f : .3f;
#endif
    return 1.f;
}
// Engage-only scale on our side of the voluntary-fight test (1 = the incumbent rule; retreat is unchanged).
inline float aggression() {
#if DZ_HAS(HOME) || DZ_HAS(FIGHT) || DZ_HAS(TURTLE)
    if (DZ_ON(FIGHT)) return 1.25f;
    if (DZ_ON(TURTLE)) return .65f;
    if (DZ_ON(HOME)) return .8f;
#endif
    return 1.f;
}
}
