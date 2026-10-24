// TEST STUB (agent B) of agent C's generated nn_schema.h - same shape as CONTRACTS 3.3; dimensions equal the
// fallback in configs/model/fs_v1.json. Copied into scratch build trees as nn_schema.h by tools/run_cpp_tests.py and
// the fuel probe; never placed in bot/src.
#pragma once
#include <cstdint>

namespace nnobs {
inline constexpr std::uint32_t kObsSchemaHash = 0x00000000u;
inline constexpr int kSelfGlobalDim = 64;
inline constexpr int kAllyRows = 5;
inline constexpr int kAllyDim = 16;
inline constexpr int kEnemyRows = 8;
inline constexpr int kEnemyDim = 16;
inline constexpr int kObsDim = kSelfGlobalDim + kAllyRows * kAllyDim + kAllyRows + kEnemyRows * kEnemyDim + kEnemyRows;
} // namespace nnobs
