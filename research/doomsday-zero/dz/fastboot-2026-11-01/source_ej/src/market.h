#pragma once
#include "plan.h"
#include <cstdint>
// C1 market claims (research review: auction allocation fits DZ's redundant-job problem with no ML and little fuel).
// Each body publishes, next to its 8-bit claim, a 2-bit bid: its distance bucket to the claimed group. A group goes to
// the lowest bid (ties to the lower slot); the others drop it instead of splitting its value. Default protocol only:
// with DZ_ECONOMY_V2 the high bits carry crew leases, so the market is compiled out there.
namespace dz::market {
#if DZ_HAS(MARKET) && !DZ_ECONOMY_V2
inline constexpr unsigned base = 48, none = 3; // Bits 48-59: six 2-bit bids above the six claim bytes.
constexpr unsigned bucket(int distance) { return distance <= 8 ? 0u : distance <= 16 ? 1u : distance <= 32 ? 2u : none; }
constexpr unsigned bid(std::uint64_t word, unsigned slot) { return slot < 6 ? static_cast<unsigned>((word >> (base + 2 * slot)) & 3u) : none; }
constexpr std::uint64_t with_bid(std::uint64_t word, unsigned slot, unsigned value) {
    if (slot >= 6) return word;
    const unsigned shift = base + 2 * slot;
    return (word & ~(std::uint64_t{3} << shift)) | (std::uint64_t{value & 3u} << shift);
}
// Another slot's claim beats ours: lower bid, or the same bid from a lower slot.
constexpr bool outbid(unsigned theirs, unsigned their_slot, unsigned ours, unsigned our_slot) {
    return theirs < ours || (theirs == ours && their_slot < our_slot);
}
#endif
}
