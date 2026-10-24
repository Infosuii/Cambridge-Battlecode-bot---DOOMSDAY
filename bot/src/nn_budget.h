// nn_budget.h (agent B) - neural fuel admission, metering and the teacher fuel view.
//
// Stable API (CONTRACTS 3.4/3.5): nnb::begin_turn() at the top of play_turn; nnb::teacher_left() replaces every
// original decision-relevant bc::fuel_remaining() (identical unless nncfg::kFuelCredit); nnb::credit(spent);
// nnb::admit(head, worst_case) BEFORE any feature work; nnb::Meter scopes record actual spend.
//
// Admission rule: fuel_left >= worst_case + kTailReserve + kTeacherReserve[head]  and
//                 used_this_turn + worst_case <= kTurnAllowance.
// Constants come from the generated nn_registry.h (models/budget.json, measured in the engine by agent B).
// With every head off and no credit/telemetry, all functions here compile to nothing / to bc::fuel_remaining().
#pragma once
#include <cstdint>
#include <cstdio>

#if !defined(NN_HOST_TEST)
#include "cambc.h"
#endif
#include "nn_config.h"
#include "nn_registry.h"

namespace nnb {

// ---------------------------------------------------------------- SDK shim (native tests define NN_HOST_TEST)
#if defined(NN_HOST_TEST)
namespace host {
inline std::uint64_t fuel = 100000;
inline std::uint32_t round = 1, champion = 1;
} // namespace host
inline std::uint64_t fuel_left() { return host::fuel; }
inline std::uint32_t round_now() { return host::round; }
inline std::uint32_t champion_now() { return host::champion; }
#else
inline std::uint64_t fuel_left() { return cambc::fuel_remaining(); }
inline std::uint32_t round_now() { return cambc::round_number(); }
// 0 during the draft (no champion yet).
inline std::uint32_t champion_now() {
    return cambc::is_draft() ? 0u : static_cast<std::uint32_t>(static_cast<cambc::handle_champion_t>(cambc::self()));
}
#endif

inline constexpr bool kTrack = nncfg::kAnyHead || nncfg::kFuelCredit || nncfg::kTelemetry;
inline constexpr int kHeads = static_cast<int>(nncfg::H::count);

inline std::uint64_t g_spent = 0; // neural fuel spent this turn (credited back to the teacher when kFuelCredit)
inline std::uint64_t g_used = 0;  // neural fuel charged against kTurnAllowance this turn
inline std::uint32_t g_turn = 0;  // turn serial; begin_turn() increments it (explicit context-cache invalidation)

struct Counters {
    std::uint32_t admitted, refused, fallback, neural;
    std::uint64_t fuel;
};
inline Counters g_cnt[kHeads] = {}; // maintained only when kTelemetry

inline void begin_turn() {
    if constexpr (kTrack) {
        g_spent = 0;
        g_used = 0;
        ++g_turn;
    }
}

inline void credit(std::uint64_t spent) {
    if constexpr (nncfg::kFuelCredit || nncfg::kTelemetry) g_spent += spent;
    else (void)spent;
}

inline std::uint64_t teacher_left() {
    if constexpr (nncfg::kFuelCredit) return fuel_left() + g_spent;
    else return fuel_left();
}

// Record actual neural spend for `head` (allowance, credit, telemetry).
inline void charge(nncfg::H head, std::uint64_t spent) {
    if constexpr (kTrack) {
        g_used += spent;
        credit(spent);
        if constexpr (nncfg::kTelemetry) g_cnt[static_cast<int>(head)].fuel += spent;
    } else {
        (void)head, (void)spent;
    }
}

// Admission before any feature work. O(1): one fuel query and a few compares.
inline bool admit(nncfg::H head, std::uint64_t worst_case) {
    const int h = static_cast<int>(head);
    const std::uint64_t left = fuel_left();
    const std::uint64_t need = worst_case + nnreg::kTailReserve + nnreg::kTeacherReserve[h];
    const bool ok = left >= need && g_used + worst_case <= nnreg::kTurnAllowance;
    if constexpr (nncfg::kTelemetry) {
        if (ok) ++g_cnt[h].admitted;
        else ++g_cnt[h].refused;
    }
    return ok;
}

inline void count_fallback(nncfg::H head, bool neural) {
    if constexpr (nncfg::kTelemetry) {
        if (neural) ++g_cnt[static_cast<int>(head)].neural;
        else ++g_cnt[static_cast<int>(head)].fallback;
    } else {
        (void)head, (void)neural;
    }
}

// Scope meter: charges the fuel spent between construction and destruction to `head`.
struct Meter {
    nncfg::H head;
    std::uint64_t start;
    explicit Meter(nncfg::H h) : head(h), start(fuel_left()) {}
    ~Meter() {
        const std::uint64_t now = fuel_left();
        charge(head, start > now ? start - now : 0);
    }
    Meter(const Meter&) = delete;
    Meter& operator=(const Meter&) = delete;
};

// One summary line per head with activity: "NNTEL <round> <head> adm ref fb neural fuel" (dev profiles only).
inline void print_telemetry(std::uint32_t round) {
    if constexpr (nncfg::kTelemetry) {
        for (int h = 0; h < kHeads; ++h) {
            const Counters& c = g_cnt[h];
            if (!(c.admitted | c.refused | c.fallback | c.neural)) continue;
            std::printf("NNTEL %u %d %u %u %u %u %llu\n", round, h, c.admitted, c.refused, c.fallback, c.neural,
                        static_cast<unsigned long long>(c.fuel));
        }
    } else {
        (void)round;
    }
}

} // namespace nnb
