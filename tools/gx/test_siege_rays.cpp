// Check the ray table against the previous interpolation for every offset,
// at borders as well as in the interior of a map.
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdlib>

#define GX_SIEGE_RAYS 2
#include "../../bots/gx-siege01/src/gx_siege.h"

int main() {
    for (int cy = 0; cy < 11; ++cy)
        for (int cx = 0; cx < 13; ++cx)
            for (int dy = -4; dy <= 4; ++dy)
                for (int dx = -4; dx <= 4; ++dx) {
                    const int qx = cx + dx, qy = cy + dy;
                    if (qx < 0 || qx >= 13 || qy < 0 || qy >= 11) continue;
                    const auto& ray = gx::kSightRays[(dy + 4) * 9 + dx + 4];
                    const int n = std::max(std::abs(cx - qx), std::abs(cy - qy));
                    assert(ray.count == std::max(0, n - 1));
                    for (int k = 1; k < n; ++k) {
                        const int old_x = qx + ((cx - qx) * k * 2 + (cx >= qx ? n : -n)) / (2 * n);
                        const int old_y = qy + ((cy - qy) * k * 2 + (cy >= qy ? n : -n)) / (2 * n);
                        assert(old_x == cx + ray.x[k - 1] && old_y == cy + ray.y[k - 1]);
                        assert(old_x >= 0 && old_x < 13 && old_y >= 0 && old_y < 11);
                    }
                }
}
