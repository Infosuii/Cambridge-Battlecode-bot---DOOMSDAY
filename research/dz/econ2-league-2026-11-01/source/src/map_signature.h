#pragma once
#include <cambc.h>
#include <cstdint>

namespace dz {
// Static map identity for per-map tables. FNV-1a over dimensions, wall/hole
// counts, altar positions and every camp spawn position (in SDK order). Only
// static data, so both sides and every body compute the same value; the pool
// test checks that all 70 development maps are distinct.
inline std::uint32_t map_signature() {
    std::uint32_t h = 2166136261u;
    auto mix = [&](std::int64_t v) { for (int i = 0; i < 8; ++i) { h ^= static_cast<std::uint8_t>(v >> (8 * i)); h *= 16777619u; } };
    mix(cambc::map::width()); mix(cambc::map::height());
    mix(cambc::map::walls().count()); mix(cambc::map::holes().count());
    for (auto p : cambc::map::altars().positions()) { mix(p.x); mix(p.y); }
    const auto groups = cambc::map::camp_groups();
    mix(static_cast<std::int64_t>(groups.size()));
    for (const auto& g : groups) for (const auto& c : g.camps()) { mix(c.spawn_position().x); mix(c.spawn_position().y); }
    return h;
}
}
