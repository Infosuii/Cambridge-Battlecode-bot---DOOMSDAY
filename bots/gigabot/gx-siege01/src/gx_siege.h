#pragma once

#if GX_SIEGE_RAYS >= 2
namespace gx {
struct SightRay {
    int count;
    int x[3], y[3];
};

constexpr auto sight_rays() {
    std::array<SightRay, 81> table{};
    for (int dy = -4; dy <= 4; ++dy) {
        for (int dx = -4; dx <= 4; ++dx) {
            auto& ray = table[(dy + 4) * 9 + dx + 4];
            const int n = std::max(dx < 0 ? -dx : dx, dy < 0 ? -dy : dy);
            for (int k = 1; k < n; ++k) {
                ray.x[ray.count] = dx + ((-dx) * k * 2 + (dx <= 0 ? n : -n)) / (2 * n);
                ray.y[ray.count] = dy + ((-dy) * k * 2 + (dy <= 0 ? n : -n)) / (2 * n);
                ++ray.count;
            }
        }
    }
    return table;
}

inline constexpr auto kSightRays = sight_rays();
} // namespace gx
#endif
