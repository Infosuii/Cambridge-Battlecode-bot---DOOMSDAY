// Synthetic SDK surface, only for deterministic option-generator fixtures.
#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <vector>
struct vec2 { int x=0,y=0; };
inline int cheb(vec2 a,vec2 b) {return std::max(std::abs(a.x-b.x),std::abs(a.y-b.y));}
namespace bc {
namespace constants {inline constexpr unsigned max_rounds=2000;inline constexpr int capture_time=15;}
struct distance_field {std::array<std::uint16_t,4096> value{};};
struct bitboard {std::array<bool,4096> value{};};
}
inline constexpr std::uint16_t kUnreach=65535;
inline int fdist(const bc::distance_field& d,vec2 p) {return d.value[static_cast<std::size_t>(p.y*64+p.x)];}
inline bool bit(const bc::bitboard& d,vec2 p) {return d.value[static_cast<std::size_t>(p.y*64+p.x)];}
