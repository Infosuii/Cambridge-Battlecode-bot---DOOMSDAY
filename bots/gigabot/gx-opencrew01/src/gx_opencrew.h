#pragma once
#include "common.h"
#include "gx_config.h"

#if GX_OPEN_CREW
namespace gx_crew {

inline constexpr int kOffset = 240, kBody = 6, kSteps = 2, kStride = 4, kVariants = 4;
inline constexpr int kBytes = kOffset + kVariants * (2 + kBody * kSteps * kStride);
inline constexpr int kUntil = 145;
inline volatile unsigned action = 1000u + GX_CREW_ARM;

struct Step {
    int group = -1, ready = 0, expires = 0, need = 1;
};

inline Step read(int bodies, int slot, int step) {
    const auto& m = bc::draft_memory;
    if (bodies < 3 || bodies > 6 || slot < 0 || slot >= bodies || step < 0 || step >= kSteps) return {};
    const int offset = kOffset + (bodies - 3) * (2 + kBody * kSteps * kStride);
    const int at = offset + 2 + (slot * kSteps + step) * kStride;
    if (m.size() < kBytes) return {};
    auto get = [&](int i) { return std::to_integer<int>(m.data()[i]); };
    if (get(offset) != 0x93 || get(offset+1) != bodies || get(at) == 255) return {};
    const int g = get(at), ready = get(at+1), expires = get(at+2), need = get(at+3);
    if (need < 1 || need > 3 || expires <= ready || expires > kUntil) return {};
    return {g,ready,expires,need};
}

}  // namespace gx_crew
#endif
