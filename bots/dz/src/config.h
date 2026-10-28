#pragma once
#include <cstdint>
#ifndef DZ_TRACE
#define DZ_TRACE 0
#endif

// Advanced models are deliberately unavailable until their research gates pass.
namespace dz::config {
inline constexpr bool economy_auction = false;
inline constexpr bool engagement_evaluator = false;
inline constexpr bool gear_planner = false;
inline constexpr std::uint64_t full_fuel = 60000, lean_fuel = 25000, reserve = 12000;
inline constexpr int bank_bag = 30, contract_window = 6, avoid_rounds = 15;
inline constexpr int max_action_errors = 3;
}
