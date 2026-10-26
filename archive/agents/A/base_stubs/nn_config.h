// GENERATED-STUB (lead): replaced by tools/gen_config.py output. Profile: teacher_exact (every neural head off).
// Keep the API in CONTRACTS.md section 3.1 stable.
#pragma once
#include <cstdint>

#define NN_ANY_HEAD 0
#define NN_STRIP_LAB 0
#define NN_TRAINING 0
#define NN_TELEMETRY 0

namespace nncfg {
enum class Mode : int { off = 0, shadow = 1, active = 2 };
enum class H : int { draft_pick, strategy, objective, role, bank, shop, move, combat, engage, ward, belief, value, ts_leaf, count };
inline constexpr Mode kMode[static_cast<int>(H::count)] = {};
constexpr Mode mode(H h) { return kMode[static_cast<int>(h)]; }
inline constexpr bool kAnyHead = false;
inline constexpr bool kTraining = false;
inline constexpr bool kTelemetry = false;
inline constexpr bool kFuelCredit = false;
inline constexpr bool kSelfTest = false;
inline constexpr bool kStripLab = false;
inline constexpr unsigned kSeed = 0;
inline constexpr const char* kProfile = "teacher_exact";
} // namespace nncfg
