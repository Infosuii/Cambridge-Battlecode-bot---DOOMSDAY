#pragma once
#include <array>

namespace codex_siege {
struct Offset { int x, y; };
struct Ray {
    std::array<Offset, 3> offsets{};
    int count = 0;
};

inline constexpr auto rays = [] {
    std::array<Ray, 81> result{};
    for (int dy = -4; dy <= 4; ++dy) {
        for (int dx = -4; dx <= 4; ++dx) {
            const int ax = dx < 0 ? -dx : dx;
            const int ay = dy < 0 ? -dy : dy;
            const int n = ax > ay ? ax : ay;
            auto& ray = result[(dy + 4) * 9 + dx + 4];
            for (int k = 1; k < n; ++k) {
                ray.offsets[ray.count++] = {
                    (-dx * k * 2 + (dx <= 0 ? n : -n)) / (2 * n),
                    (-dy * k * 2 + (dy <= 0 ? n : -n)) / (2 * n),
                };
            }
        }
    }
    return result;
}();
}
