// STUB (lead) - owned and extended by agent B. Stable API: nnb::teacher_left(), nnb::credit(), nnb::begin_turn().
// teacher_left() is what every original fuel-gated decision reads. Without kFuelCredit it is exactly
// bc::fuel_remaining(); with kFuelCredit (neutral-proof profile only) neural spend this turn is added back so the
// teacher's admission decisions see the budget they would have had without the neural layer.
#pragma once
#include <cstdint>

#include "cambc.h"
#include "nn_config.h"

namespace nnb {
inline std::uint64_t g_spent = 0; // neural fuel spent this turn (only maintained when kFuelCredit or telemetry)

inline void begin_turn() {
    if constexpr (nncfg::kFuelCredit || nncfg::kTelemetry) g_spent = 0;
}
inline void credit(std::uint64_t spent) {
    if constexpr (nncfg::kFuelCredit || nncfg::kTelemetry) g_spent += spent;
    else (void)spent;
}
inline std::uint64_t teacher_left() {
    if constexpr (nncfg::kFuelCredit) return cambc::fuel_remaining() + g_spent;
    else return cambc::fuel_remaining();
}
} // namespace nnb
