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
#ifndef DZ_TRACE_MODEL
#define DZ_TRACE_MODEL 0 // Diagnostic predictions; never enabled in release.
#endif
#ifndef DZ_TRACE_SHIELD
#define DZ_TRACE_SHIELD 0 // Opt-in single-live Varg shield diagnostic; not production policy.
#endif
#ifndef DZ_TRACE_SPLASH
#define DZ_TRACE_SPLASH 0 // Opt-in exact mixed-group splash reduction; diagnostic only.
#endif
#ifndef DZ_TRACE_HEART
#define DZ_TRACE_HEART 0 // Opt-in single-target missing-health/shield diagnostic.
#endif
#ifndef DZ_TRACE_MODEL_TO
#define DZ_TRACE_MODEL_TO 500
#endif
#ifndef DZ_DRAFT_VARIANT
#define DZ_DRAFT_VARIANT 0
#endif
#ifndef DZ_MAP_DRAFT_TABLE
#define DZ_MAP_DRAFT_TABLE 1 // Keep the confirmed incumbent table; disable only for global lineup trials.
#endif
#ifndef DZ_MAP_DRAFT_MATRIX
#define DZ_MAP_DRAFT_MATRIX 0 // Frozen carrier-policy draft refresh; separate opponent confirmation required.
#endif
#ifndef DZ_MAP_DRAFT_EXTRA
#define DZ_MAP_DRAFT_EXTRA 0 // Frozen four-map Z14 hypothesis; requires separate confirmation.
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
#ifndef DZ_CREW_REACH
#define DZ_CREW_REACH 0 // Experiment: reject proven unreachable crew jobs and contracts.
#endif
#ifndef DZ_CLEAR_TIME_WORK_ONLY
#define DZ_CLEAR_TIME_WORK_ONLY 0 // Experiment: omit uncalibrated per-member time padding.
#endif
#ifndef DZ_CLEAR_TIME_CLOCK
#define DZ_CLEAR_TIME_CLOCK 0 // Experimental attack/reset elapsed clock; survival gate unchanged.
#endif
#ifndef DZ_BANK_AWARE_RATE
#define DZ_BANK_AWARE_RATE 0 // Experiment: amortize static delivery travel in solo job pricing.
#endif
#ifndef DZ_CARRIER_BANK_PRIORITY
#define DZ_CARRIER_BANK_PRIORITY 1 // Bankable carriers retain banking priority; full preservation pools passed.
#endif
#ifndef DZ_ENGAGE_IN_RANGE
#define DZ_ENGAGE_IN_RANGE 0 // Experiment: voluntary fights count only allies in range of the focus.
#endif
#ifndef DZ_FIGHT_GEM_VALUE
#define DZ_FIGHT_GEM_VALUE 0 // Experiment: voluntary chase requires carried gems on its chosen target.
#endif
#ifndef DZ_GEM_TARGET_PRIORITY
#define DZ_GEM_TARGET_PRIORITY 0 // Experiment: visible carried gems contribute to local target value.
#endif
#ifndef DZ_CAPTURE_GEAR
#define DZ_CAPTURE_GEAR 0 // Experiment: Vesper's third same-stat emblem is Capture instead of Jungle.
#endif
#ifndef DZ_CAPTURE_FOURTH
#define DZ_CAPTURE_FOURTH 0 // Experiment: retain the first3 emblems, then one Capture before Power.
#endif
#ifndef DZ_EE
#define DZ_EE 0 // Unvalidated Z10 v1: retreat from losing contact earlier; avoid groups near recent enemy sightings.
#endif
#ifndef DZ_EE_NEAR
#define DZ_EE_NEAR 3 // DZ_EE: retreat once a losing enemy is within its attack range plus this many tiles.
#endif
#ifndef DZ_EE_SCAN
#define DZ_EE_SCAN 10 // DZ_EE: enemies within this Chebyshev distance enter the local fight estimate.
#endif
#ifndef DZ_EE_MEMORY
#define DZ_EE_MEMORY 20 // DZ_EE: rounds a personal enemy sighting keeps pricing nearby jobs down.
#endif
#ifndef DZ_GEAR_SURVIVE
#define DZ_GEAR_SURVIVE 0 // Unvalidated Z9 v1: Jungle-first survival/clear openers instead of Treasure-first.
#endif
#ifndef DZ_GEAR_PROSPECT
#define DZ_GEAR_PROSPECT 0 // Unvalidated Z9 v1: third emblem is Prospector on maps with cluster groups.
#endif
#ifndef DZ_CREWS
#define DZ_CREWS 0 // Unvalidated Z11 v1: fixed slot pairs; the follower takes its leader's camp job, the leader prices pair damage.
#endif
#ifndef DZ_BANK_NEAR_MIN
#define DZ_BANK_NEAR_MIN 0 // Unvalidated Z6 v1: the near-altar bank needs at least 15 gems (not any bag).
#endif
#ifndef DZ_BANK_BIG
#define DZ_BANK_BIG 0 // Unvalidated Z6 v1: the ordinary trip bag is 45 instead of 30.
#endif
#ifndef DZ_RING_GATES
#define DZ_RING_GATES 0 // Unvalidated Z14 v1: an altar whose pocket is ringed by camps (not only its 8 neighbours) is gated.
#endif
#ifndef DZ_CREW_ALL
#define DZ_CREW_ALL 0 // Unvalidated Z11 v1 variant (with DZ_CREWS): one whole-team crew led by the lowest living slot.
#endif
#ifndef DZ_GEAR_HEALTH
#define DZ_GEAR_HEALTH 0 // Unvalidated Z9 v1 variant: health-stat survival emblems (Jungle, Durability, Prospector) for every body.
#endif
#ifndef DZ_EE_REGROUP
#define DZ_EE_REGROUP 0 // Unvalidated Z10 v1: retreat from a losing contact toward the nearest healthy ally within 12, not home.
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
