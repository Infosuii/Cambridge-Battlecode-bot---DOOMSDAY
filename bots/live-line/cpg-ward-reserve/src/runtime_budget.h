// Fuel governor (A2_GOV, Agent 2): cheap deterministic admission for optional stages, distance-field searches capped
// at the depth the remaining fuel can pay for, and per-stage counters.
//
// Rules: a check costs a few instructions and one host call; no unsigned underflow; admission compares a stage's
// worst-case cost (not an average) plus the reserve the rest of the turn needs against the fuel left. A refused or
// capped stage must leave coherent state: the caller takes its documented fallback (no move, a greedy step, the
// formula verdict) and never publishes a half-built result.
#pragma once

#include <algorithm>
#include <cstdint>

#include "common.h"

namespace rb {

#if JD_GOV
// JD_GOV (FEAT-002) adds stages for the whole-turn reservations below. kTactical, kRoute, kNN and kPlanCache are the
// admission points for later work (tactical search, route search, neural inference, plan caches); kFieldOrder,
// kSiegeInit and kWardLabel are the three stages the baseline profile caught suspending (research FUEL_BENCH.md).
enum Stage : int {
    kWalk, kWalkTerrain, kThreatPath, kWardAhead, kTactical, kRoute, kNN, kPlanCache, kFieldOrder, kSiegeInit, kWardLabel,
    kStages
};
inline constexpr const char* kStageName[kStages] = {"walk", "walk_terrain", "threat_path", "ward_ahead", "tactical",
    "route", "nn", "plan_cache", "field_order", "siege_init", "ward_label"};
#else
enum Stage : int { kWalk, kWalkTerrain, kThreatPath, kWardAhead, kStages };
inline constexpr const char* kStageName[kStages] = {"walk", "walk_terrain", "threat_path", "ward_ahead"};
#endif

// Counters: ran = admitted with room to spare, capped = admitted with a binding depth cap, skipped = refused.
inline std::uint32_t ran[kStages], capped[kStages], skipped[kStages];

// Fuel the rest of a turn needs after a movement stage: everything after farm or fight movement (ward drop, altar
// prelock, priority, guarded field building) measured under 1k; the margin covers one more small helper.
inline constexpr std::uint64_t kTailReserve = 6000;
// Engine search cost model: (levels + 16) x chunks plus a fixed overhead (world.cpp, measured to 0.3%).
inline constexpr std::uint64_t kSearchFixed = 3000;

inline std::uint64_t left() { return bc::fuel_remaining(); }

// True when `cost` can start and still leave `reserve`.
inline bool fits(std::uint64_t cost, std::uint64_t reserve) {
    const std::uint64_t l = left();
    return l >= reserve && l - reserve >= cost;
}

inline bool admit(Stage s, std::uint64_t cost, std::uint64_t reserve) {
    if (fits(cost, reserve)) {
        ++ran[s];
        return true;
    }
    ++skipped[s];
    return false;
}

#if JD_GOV
// Whole-turn reservations (JD_GOV). A turn runs observe -> decide -> execute -> tail. Each phase's reservation is
// the fuel its mandatory work needs at the 99th percentile (JD_FUELPROF profile, diag-fprof-04: observe p99 ~20k,
// decide's own checks keep 35k, execute walk p99 ~23k, tail p99 ~5k). Optional work in a phase is admitted only when
// its worst case still leaves the reservations of every LATER phase; the caller takes its documented fallback when
// refused. Phases only move forward within a turn; begin_turn() resets.
struct Reserve {
    std::uint64_t observe, decide, execute, tail;
};
enum Phase : int { kObserve, kDecide, kExecute, kTail };
inline constexpr Reserve kReserve{20000, 25000, 20000, kTailReserve};
inline int phase = kObserve;
inline void begin_turn() { phase = kObserve; }
inline void enter(Phase p) {
    if (p > phase) phase = p;
}
// Fuel the phases after `p` still need.
inline constexpr std::uint64_t mandatory_after(int p) {
    return (p < kDecide ? kReserve.decide : 0) + (p < kExecute ? kReserve.execute : 0) + (p < kTail ? kReserve.tail : 0);
}
// Admit optional work of worst-case cost `worst` in the current phase (unsigned-safe, same rule as fits()).
inline bool admit_optional(Stage s, std::uint64_t worst) { return admit(s, worst, mandatory_after(phase)); }
// End optional work: true once the fuel left is below the tail reservation (the rest of the turn must stay cheap).
inline bool turn_guard() { return left() < kReserve.tail; }
#endif

// Deepest search the remaining fuel can pay for while keeping `reserve`; 0 when not even a short one fits.
inline std::uint16_t search_cap(std::uint64_t reserve) {
    const std::uint64_t chunks = std::max<std::uint64_t>(field_chunks(), 1);
    const std::uint64_t l = left();
    if (l <= reserve + kSearchFixed) return 0;
    const std::uint64_t levels = (l - reserve - kSearchFixed) / chunks;
    return levels <= 16 ? 0 : static_cast<std::uint16_t>(std::min<std::uint64_t>(levels - 16, 65534));
}

} // namespace rb
