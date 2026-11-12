// Six coarse positions (9 bits each), focus target (3 bits), rally camp (7 bits): exactly 64 bits.
#pragma once
#include <cstdint>

namespace team67 {
constexpr int kSlots = 6, kPositionBits = 9, kFocusShift = 54, kRallyShift = 57;
constexpr std::uint64_t kPositionMask = 511, kFocusMask = 7, kRallyMask = 127;
inline unsigned encode(int x, int y) {
    if (x < 0 || y < 0 || x >= 100 || y >= 100) return 0;
    return static_cast<unsigned>(1 + x / 5 + 20 * (y / 5));
}
inline bool position(std::uint64_t memory, int slot, int& x, int& y) {
    if (slot < 0 || slot >= kSlots) return false;
    const int value = static_cast<int>((memory >> (slot * kPositionBits)) & kPositionMask);
    if (value < 1 || value > 400) return false;
    x = ((value - 1) % 20) * 5 + 2;
    y = ((value - 1) / 20) * 5 + 2;
    return true;
}
inline std::uint64_t put_position(std::uint64_t memory, int slot, int x, int y, bool alive) {
    if (slot < 0 || slot >= kSlots) return memory;
    const int shift = slot * kPositionBits;
    return (memory & ~(kPositionMask << shift)) | (static_cast<std::uint64_t>(alive ? encode(x, y) : 0) << shift);
}
inline int focus(std::uint64_t memory) { return static_cast<int>((memory >> kFocusShift) & kFocusMask) - 1; }
inline int rally(std::uint64_t memory) { return static_cast<int>((memory >> kRallyShift) & kRallyMask) - 1; }
inline std::uint64_t put_plan(std::uint64_t memory, int focus_target, int group) {
    const auto keep = memory & ((std::uint64_t{1} << kFocusShift) - 1);
    const unsigned f = focus_target >= 0 && focus_target < 6 ? static_cast<unsigned>(focus_target + 1) : 0;
    const unsigned g = group >= 0 && group < 127 ? static_cast<unsigned>(group + 1) : 0;
    return keep | (static_cast<std::uint64_t>(f) << kFocusShift) | (static_cast<std::uint64_t>(g) << kRallyShift);
}
}
