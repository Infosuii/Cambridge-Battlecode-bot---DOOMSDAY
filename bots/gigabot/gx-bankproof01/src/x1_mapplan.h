// Per-map team plan for x3 (X1_MAPPLAN): competition maps without a ladder fit, best plan from the per-map search
// (tools/x3_mapplan_search.sh, tools/x3_mapplan_table.py). Fingerprint as ladfit.h: width, height, camp groups, gems.
#pragma once
#include <cstdint>
namespace x1_mapplan {
struct Row { int w, h, groups; std::uint32_t gems; int id, round; };
inline constexpr Row kRows[] = {{0, 0, 0, 0u, 0, -1}};
} // namespace x1_mapplan
