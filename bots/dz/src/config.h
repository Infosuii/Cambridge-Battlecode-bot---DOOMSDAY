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
#ifndef DZ_TRACE_FIGHT
#define DZ_TRACE_FIGHT 0 // Per-turn enemy-contact lines in the trace window.
#endif
#ifndef DZ_TRACE_PROFILE
#define DZ_TRACE_PROFILE 0 // Opt-in profiler; runner overrides live in config.h.
#endif
#ifndef DZ_DRAFT_VARIANT
#define DZ_DRAFT_VARIANT 0
#endif
#ifndef DZ_LOCAL_MASKS
#define DZ_LOCAL_MASKS 1
#endif
#ifndef DZ_CAMP_SAFETY
#define DZ_CAMP_SAFETY 0
#endif
#ifndef DZ_PATH_REACH_ONLY
#define DZ_PATH_REACH_ONLY 0 // Paused reach-only scoring regressed the v65 release pool.
#endif
#ifndef DZ_FAILED_MOVE_MEMORY
#define DZ_FAILED_MOVE_MEMORY 0 // Local failed-step retries avoid stale hard obstacles.
#endif
#ifndef DZ_MOVE_RETRY
#define DZ_MOVE_RETRY 1
#endif
#ifndef DZ_RETRY_STREAK
#define DZ_RETRY_STREAK 1 // Repair persistent travel blockages, not ordinary traffic.
#endif
#ifndef DZ_RETRY_DETOUR
#define DZ_RETRY_DETOUR 1 // Re-route around SDK-rejected tiles in this turn only.
#endif
#ifndef DZ_SHORT_BLOCK_MEMORY
#define DZ_SHORT_BLOCK_MEMORY 0
#endif
#ifndef DZ_LATE_FIELD_GATE
#define DZ_LATE_FIELD_GATE 0 // Trace builds always gate their added work below.
#endif
#ifndef DZ_PERSONAL_PROGRESS
#define DZ_PERSONAL_PROGRESS 0 // Experimental: a teammate's banking is not this body's work.
#endif
#ifndef DZ_IDLE_HELPER
#define DZ_IDLE_HELPER 0 // Experimental: reinforce a visible active clear instead of idling.
#endif
#ifndef DZ_JOB_GEAR
#define DZ_JOB_GEAR 0 // Experimental: cluster jobs can justify Prospector over Treasure.
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
