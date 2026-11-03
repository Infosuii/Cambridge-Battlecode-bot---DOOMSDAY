#pragma once
#include "common.h"
#include "gx_config.h"
#if GX_MINT
namespace gx_mint {
inline constexpr int kAt = 144, kBytes = kAt+1+3*5;
inline volatile unsigned action = 1000u + GX_MINT_ARM;
inline constexpr bc::champion_type roles[3] = {
    bc::champion_type::vesper_vale,bc::champion_type::tavi,bc::champion_type::vendetta};
struct Plan {
    int first = -1, second = -1, expires = 0, first_gold = 0, turns = 0;
};

inline Plan read(int role) {
    const auto& m = bc::draft_memory;
    if (role < 0 || role >= 3 || m.size() < kBytes) return {};
    auto get = [&](int i) { return std::to_integer<int>(m.data()[i]); };
    if (get(kAt)!=0xc1) return {};
    const int off = kAt+1+5*role;
    const int first=get(off), second=get(off+1), exp=get(off+2), gold=get(off+3), turns=get(off+4);
    if (first==255 || !exp || exp>95) return {};
    return {first,second==255?-1:second,exp,gold,turns};
}
} // namespace gx_mint
#endif
