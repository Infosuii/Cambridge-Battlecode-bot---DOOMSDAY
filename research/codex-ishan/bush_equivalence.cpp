// Diagnostic-only fixture injected before draft in an isolated native build.
#include "codex_bush.h"
#include <cstdio>

static void codex_check_components() {
    const auto terrain = bc::map::bushes();
    const int width = bc::map::width(), height = bc::map::height(), n = width * height;
    const auto start = bc::fuel_remaining();
    const auto packed = terrain.export_linear_buffer();
    std::vector<std::uint8_t> seen(packed.size(), 0);
    std::vector<std::uint16_t> labels(n, 65535);
    std::vector<int> stack;
    stack.reserve(n);
    int components = 0;
    for (int i = 0; i < n; ++i)
        if (codex_bush::bit(packed, i) && !codex_bush::bit(seen, i))
            codex_bush::fill(width, height, packed, seen, labels.data(),
                             static_cast<std::uint16_t>(components++), i, stack);
    bc::bitboard restored;
    restored.import_linear_buffer(seen);
    const auto optimized_cost = start - bc::fuel_remaining();

    // Independent original SDK-membership flood with its fixed coordinate stack.
    const auto reference_start = bc::fuel_remaining();
    bc::bitboard ref_seen;
    ref_seen.clear();
    std::vector<std::uint16_t> reference(n, 65535);
    std::vector<std::uint32_t> work(n);
    int ref_components = 0;
    for (int root = 0; root < n; ++root) {
        const vec2 origin{root % width, root / width};
        if (!terrain.is_set(origin) || ref_seen.is_set(origin)) continue;
        const int id = ref_components++;
        int count = 0;
        work[count++] = static_cast<std::uint32_t>(origin.x) | static_cast<std::uint32_t>(origin.y) << 16;
        ref_seen.set(origin, true);
        while (count > 0) {
            const auto at = work[--count];
            const int x = static_cast<int>(at & 65535), y = static_cast<int>(at >> 16);
            reference[y * width + x] = static_cast<std::uint16_t>(id);
            const int x0 = x > 0 ? x - 1 : 0, x1 = x + 1 < width ? x + 1 : x;
            const int y0 = y > 0 ? y - 1 : 0, y1 = y + 1 < height ? y + 1 : y;
            for (int yy = y0; yy <= y1; ++yy) for (int xx = x0; xx <= x1; ++xx) {
                const vec2 q{xx, yy};
                if (!terrain.is_set(q) || ref_seen.is_set(q)) continue;
                ref_seen.set(q, true);
                work[count++] = static_cast<std::uint32_t>(xx) | static_cast<std::uint32_t>(yy) << 16;
            }
        }
    }
    const auto reference_cost = reference_start - bc::fuel_remaining();
    int mismatches = 0, packing_mismatches = 0;
    for (int i = 0; i < n; ++i) {
        mismatches += labels[i] != reference[i];
        packing_mismatches += terrain.is_set({i % width, i / width}) != codex_bush::bit(packed, i);
    }
    std::printf("BUSH_EQ tiles=%d components=%d reference_components=%d mismatches=%d packing_mismatches=%d mask_equal=%d optimized_fuel=%llu reference_fuel=%llu\n",
                n, components, ref_components, mismatches, packing_mismatches,
                (restored ^ terrain).is_empty() ? 1 : 0,
                static_cast<unsigned long long>(optimized_cost), static_cast<unsigned long long>(reference_cost));
}
