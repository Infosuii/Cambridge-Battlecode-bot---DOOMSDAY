#pragma once
#include "common.h"
#include "gx_config.h"

#if GX_FIELD_COST
namespace gx_field_cost {
inline constexpr int kAt = 448, kMaxGroups = 120, kHeader = 4;
inline volatile unsigned action = 1000u + GX_FIELD_COST_ARM;

inline int read(std::size_t groups, int group, bool bridges) {
    const auto& m = bc::draft_memory;
    if (group < 0 || groups > kMaxGroups || static_cast<std::size_t>(group) >= groups ||
        m.size() < kAt+kHeader+4*groups) return -1;
    const auto* b = m.data();
    const auto get = [&](int i) { return std::to_integer<unsigned>(b[i]); };
    if (get(kAt) != 0xb2 || get(kAt+1) != groups || (bridges && get(kAt+2) == 0)) return -1;
    const int at = kAt + kHeader + 2*group + (bridges ? static_cast<int>(2*groups) : 0);
    const int n = get(at) | get(at+1)<<8;
    return n == 0xffff ? -1 : n;
}

} // namespace gx_field_cost
#endif
