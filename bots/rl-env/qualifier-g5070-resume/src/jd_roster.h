#pragma once
#include <array>
#include <cstdint>
#include <span>
namespace jd_roster {
// ABI: marker 0x58, body count, six champion_type values. Empty/invalid => marker 0.
inline std::array<std::uint8_t,8> encode(std::span<const std::uint8_t> picks) {
    std::array<std::uint8_t,8> out{};
    if (picks.empty() || picks.size() > 5) return out;
    std::uint16_t seen=0;
    for (auto pick:picks) {
        if (pick>11 || (seen & (1u<<pick))) return {};
        seen |= 1u<<pick;
        if (pick==3) { out[2+out[1]++]=3; out[2+out[1]++]=4; }
        else out[2+out[1]++]=pick>=4 ? pick+1 : pick;
    }
    out[0]=0x58;
    return out;
}
}
