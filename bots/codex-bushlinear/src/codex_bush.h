#pragma once
#include <cstdint>
#include <vector>

namespace codex_bush {
// SDK packed row-major bits, verified against is_set on the native engine.
inline bool bit(const std::vector<std::uint8_t>& mask, int i) {
    return (mask[static_cast<std::size_t>(i) >> 3] & (1u << (i & 7))) != 0;
}
inline void mark(std::vector<std::uint8_t>& mask, int i) {
    mask[static_cast<std::size_t>(i) >> 3] |= static_cast<std::uint8_t>(1u << (i & 7));
}
inline void fill(int width, int height, const std::vector<std::uint8_t>& bush,
                 std::vector<std::uint8_t>& seen, std::uint16_t* labels,
                 std::uint16_t id, int root, std::vector<int>& stack) {
    stack.clear();
    mark(seen, root);
    stack.push_back(root);
    while (!stack.empty()) {
        const int at = stack.back();
        stack.pop_back();
        labels[at] = id;
        const int x = at % width, y = at / width;
        const int x0 = x > 0 ? x - 1 : 0, x1 = x + 1 < width ? x + 1 : x;
        const int y0 = y > 0 ? y - 1 : 0, y1 = y + 1 < height ? y + 1 : y;
        for (int yy = y0; yy <= y1; ++yy) for (int xx = x0; xx <= x1; ++xx) {
            const int next = yy * width + xx;
            if (!bit(bush, next) || bit(seen, next)) continue;
            mark(seen, next);
            stack.push_back(next);
        }
    }
}
} // namespace codex_bush
