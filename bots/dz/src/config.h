#pragma once
#include <cstdint>
#ifndef DZ_TRACE
#define DZ_TRACE 0
#endif
// Trace builds also print every goal of one body over a round window.
#ifndef DZ_TRACE_SLOT
#define DZ_TRACE_SLOT 0
#define DZ_TRACE_FROM 100
#define DZ_TRACE_TO 160
#endif
#ifndef DZ_CAMP_SAFETY
#define DZ_CAMP_SAFETY 0
#endif

// Advanced models are deliberately unavailable until their research gates pass.
namespace dz::config {
inline constexpr bool economy_auction = false;
inline constexpr bool engagement_evaluator = false;
inline constexpr bool gear_planner = false;
inline constexpr bool camp_safety = DZ_CAMP_SAFETY != 0;
inline constexpr std::uint64_t full_fuel = 60000, lean_fuel = 25000, reserve = 12000;
inline constexpr std::uint64_t ordinary_turn_fuel = 100000; // CT-3 pinned budget.
inline constexpr int bank_bag = 30, contract_window = 6, crew_window = 40, avoid_rounds = 15, respawn_wait = 15;
inline constexpr int max_action_errors = 3;
}
