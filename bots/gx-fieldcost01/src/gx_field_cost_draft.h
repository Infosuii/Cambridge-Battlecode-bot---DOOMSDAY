#pragma once
#include "gx_field_cost.h"

#if GX_FIELD_COST
namespace gx_field_cost {
inline std::vector<std::uint8_t> measure() {
    namespace d = bc::detail;
    if (field_chunks() < 49) return {};
    std::uint32_t n = 0;
    if (d::sdk_map_num_camp_groups(&n) != 0 || n < 5 || n > kMaxGroups ||
        bc::constants::draft_memory_bytes < kAt + kHeader + 4*n) return {};
    std::vector<std::uint32_t> handles(n);
    if (d::sdk_map_camp_groups(handles.data(),n,&n) != 0) return {};
    const auto holes = bc::map::holes();
    const auto blocked = bc::map::walls() | holes | bc::map::altars() | bc::map::spawn_region(team::enemy);
    const auto spawn = bc::map::spawn_region(team::ally);
    bc::bitboard visited;
    bc::distance_field f;
    f.compute(blocked,spawn,visited);
    int gem_total = 0, gem_cut = 0;
    std::vector<bc::bitboard> tiles;
    tiles.reserve(n);
    for (auto h : handles) {
        std::uint32_t count = 0, members[64];
        d::camp_group_info group{};
        if (d::sdk_map_camp_group(h,&group) != 0 || d::sdk_map_camp_group_num_camps(h,&count) != 0) return {};
        count = std::min<std::uint32_t>(count,64);
        if (count && d::sdk_map_camp_group_camps(h,members,count,&count) != 0) return {};
        auto& ring = tiles.emplace_back();
        ring.clear();
        bool walk = false;
        for (std::uint32_t i = 0; i < count; ++i) {
            d::camp_info c{};
            if (d::sdk_map_camp_info(members[i],&c) != 0) return {};
            const vec2 p{c.x,c.y};
            set_bit(ring,p);
            walk |= fdist(f,p) != kUnreach;
        }
        gem_total += group.gems;
        if (!walk) gem_cut += group.gems;
    }
    bc::bitboard overlay;
    overlay.clear();
#if A2_BRIDGES
    if (gem_total && gem_cut * 4 >= gem_total && !holes.is_empty()) {
        const auto open = ~blocked;
        overlay = holes & ((open.shift_right(1) & open.shift_right(-1)) |
            (open.shift_up(1) & open.shift_up(-1)) |
            (open.shift_right(1).shift_up(1) & open.shift_right(-1).shift_up(-1)) |
            (open.shift_right(1).shift_up(-1) & open.shift_right(-1).shift_up(1)));
    }
#endif
    const bool bridges = !overlay.is_empty();
    std::vector<std::uint8_t> data(kAt+kHeader+4*n,255);
    std::fill_n(data.begin(),kAt,0);
    data[kAt] = 0xb2;
    data[kAt+1] = static_cast<std::uint8_t>(n);
    data[kAt+2] = bridges;
    data[kAt+3] = 0;
    const auto width = bc::map::width(), height = bc::map::height();
    const auto cap = static_cast<std::uint16_t>(std::min(1000,width+height+16));
    const std::uint64_t worst = 18000 + static_cast<std::uint64_t>(cap+20) * field_chunks();
    for (int mode = 0; mode < 1 + bridges; ++mode) {
        const auto terrain = mode ? blocked & ~overlay : blocked;
        for (std::uint32_t g = 0; g < n; ++g) {
            if (bc::fuel_remaining() < worst + 250000) return data;
            if (tiles[g].is_empty()) continue;
            const int levels = f.compute_with_expansion_count(terrain,tiles[g],visited,cap);
            const auto at = kAt+kHeader + 2*g + 2*n*mode;
            data[at] = static_cast<std::uint8_t>(levels & 255);
            data[at+1] = static_cast<std::uint8_t>(levels >> 8);
        }
    }
    return data;
}
} // namespace gx_field_cost
#endif
