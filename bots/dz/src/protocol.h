#pragma once
#include <cstdint>

namespace dz::protocol {
inline constexpr unsigned slots = 6;
inline constexpr std::uint8_t shop = 120, retreat = 121, dead = 126, idle = 127;
struct Slot { std::uint8_t objective; bool onsite; };
constexpr bool is_group_code(unsigned code) { return code<112; }
constexpr std::uint8_t group_code(unsigned index) { return index < 112 ? static_cast<std::uint8_t>(index) : idle; }
constexpr Slot slot(std::uint64_t word, unsigned index) {
    if (index >= slots) return {idle, false};
    auto value = static_cast<std::uint8_t>(word >> (index * 8));
    return {static_cast<std::uint8_t>(value & 127), (value & 128) != 0};
}
constexpr std::uint64_t with_slot(std::uint64_t word, unsigned index, Slot value) {
    if (index >= slots) return word;
    const auto shift = index * 8;
    const auto byte = static_cast<std::uint64_t>((value.objective & 127) | (value.onsite ? 128 : 0));
    return (word & ~(std::uint64_t{255} << shift)) | (byte << shift);
}
constexpr std::uint64_t empty_word() {
    std::uint64_t word = 0;
    for (unsigned i = 0; i < slots; ++i) word = with_slot(word, i, {idle, false});
    return word;
}
// Team messages are preserved but not interpreted in v0: the sketch's parity/TTL
// cannot independently establish age. Do not infer freshness from unchanged bits.
}
