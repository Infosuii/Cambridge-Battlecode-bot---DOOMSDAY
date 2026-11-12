#pragma once
#include "common.h"
#include <cambc.h>
#include <cstdint>
#include <cstdio>
#include "a2stack_table.h"
#ifndef A2_CFG_DEFAULT
#define A2_CFG_DEFAULT 1
#endif
namespace a2stack {
inline int cfg() {
    static int v = -1;
    if (v >= 0) return v;
    std::uint32_t ng = 0;
    bc::detail::sdk_map_num_camp_groups(&ng);
    const int w = static_cast<int>(bc::map::width()), h = static_cast<int>(bc::map::height()), team = static_cast<int>(bc::detail::sdk_my_team());
#ifdef A2_CFG_FIXED
    v = A2_CFG_FIXED;
#elif defined(A2_CFG_S3)
    unsigned picks = 5;
    try {
        picks = bc::draft::team_size();
    } catch (...) {
    }
    v = picks <= 3 ? A2_CFG_S3 : picks == 4 ? A2_CFG_S4 : A2_CFG_S5;
#else
    v = A2_CFG_DEFAULT;
    for (const auto& r : kRows)
        if (r[0] == w && r[1] == h && r[2] == static_cast<int>(ng) && r[3] == team) v = r[4];
#endif
#ifdef A2_CFG_LOG
    std::printf("A2K %d %d %u %d\n", w, h, ng, team);
#endif
    return v;
}
}
