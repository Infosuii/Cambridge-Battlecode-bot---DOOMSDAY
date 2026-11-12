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
#ifndef DZ_TRACE_DRAFTMEM
#define DZ_TRACE_DRAFTMEM 0 // Trace-only probe: draft writes the map signature to draft memory; play reads it back.
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
#ifndef DZ_PLAN_TABLE
#define DZ_PLAN_TABLE 0 // Unvalidated Z14 v1: per-map draft variant and experiment bits from map_plans.inc (plan.h).
#endif
#ifndef DZ_STYLE
#define DZ_STYLE 0 // Z13 evaluation opponents only (tools/dz_styles.py): 1 rusher, 2 turtle, 3 cluster farmer. Never a candidate.
#endif
#ifndef DZ_OPENING_GOLD
#define DZ_OPENING_GOLD 0 // Unvalidated Z12 v1: jobs value gold at 0.5 per gem before round 250 (then 0.1).
#endif
#ifndef DZ_GOLD_VALUE
#define DZ_GOLD_VALUE 0 // Unvalidated Z6 v1 lambda_gold: jobs value gold at 0.3 per gem all game.
#endif
#ifndef DZ_EE2
#define DZ_EE2 0 // Z10 v2 (V-M2 model): retreat only above P(death within 4 rounds) 0.15; engage won fights below 0.04.
#endif
#ifndef DZ_EE2_BOLD
#define DZ_EE2_BOLD 0 // Z10 v2 variant (with DZ_EE2): retreat threshold 0.30 instead of 0.15.
#endif
#ifndef DZ_SWITCH_ROUND
#define DZ_SWITCH_ROUND 5000 // A2 branch hook (DZ_PLAN_TABLE): from this round plan bits become DZ_SWITCH_BITS; 5000 = never.
#endif
#ifndef DZ_SWITCH_BITS
#define DZ_SWITCH_BITS 2147483648 // Bit 31 is ignored; it keeps the initialiser non-zero so no branch value folds.
#endif
#ifndef DZ_EE3
#define DZ_EE3 0 // Unvalidated B1: engage/retreat on the expected exchange of two contact models (ours, enemy's).
#endif
#ifndef DZ_GOLD_FIT
#define DZ_GOLD_FIT 0 // Unvalidated A3: gold 0.18 gems before R250, then 0.1 (within-cell fit, 35k games, research/dz/a3-*).
#endif
#ifndef DZ_FOCUS
#define DZ_FOCUS 0 // Unvalidated B3: attack-target score x(1 + 0.75 x allies that can also reach the target).
#endif
#ifndef DZ_CLEAR_BOLD
#define DZ_CLEAR_BOLD 0 // Unvalidated: camp clears accepted at 1.1x expected damage + 5% max HP (was 1.25x + 10%).
#endif
#ifndef DZ_DRAFT_MASTERY
#define DZ_DRAFT_MASTERY 0 // Unvalidated F8: pick order by DZ's own per-champion results (Ryth, Marcella, Vesper, Varg, Vendetta, Heart).
#endif
#ifndef DZ_ALTAR_LOCK
#define DZ_ALTAR_LOCK 0 // Unvalidated E-series denial: carry one altar lock; lock an altar a visible enemy is tributing at (lock.h).
#endif
#ifndef DZ_ALTAR_LOCK_ANY
#define DZ_ALTAR_LOCK_ANY 0 // With DZ_ALTAR_LOCK: also lock enemy-side altars and altars an enemy carrier approaches (lock.h v2).
#endif
#ifndef DZ_EARLY_JOBS
#define DZ_EARLY_JOBS 0 // Fuel/tempo: play starts once camps, masks, home and group stats are ready; altar fields follow, one per turn.
#endif
#ifndef DZ_FAST_BOOT
#define DZ_FAST_BOOT 0 // Fuel: boot runs each step in the same turn while tc.allow() covers it (no per-step returns, no 25k caps).
#endif
#ifndef DZ_FIELD_METER
#define DZ_FIELD_METER 0 // Fuel: field_budget() = max(formula, worst measured field compute + 1/8); every compute is metered.
#endif
#ifndef DZ_FAST_FIGHT
#define DZ_FAST_FIGHT 0 // Fuel only: event-stepped simulate_fight, bit-identical results (host-tested). Unvalidated in play.
#endif
#ifndef DZ_LOCAL_FIGHT
#define DZ_LOCAL_FIGHT 0 // Fuel-NEGATIVE as written: the radius-7 BFS cost more than the field it replaced (dz-ee3v4*-hot). Off.
#endif
#ifndef DZ_MARKET
#define DZ_MARKET 0 // Unvalidated C1: group claims carry a distance bid; outbid bodies drop the group (market.h).
#endif
#ifndef DZ_HOME
#define DZ_HOME 0 // Unvalidated A1 team plan: enemy-half groups priced x0.3, engage aggression x0.8 (lab home plan).
#endif
#ifndef DZ_HOARD
#define DZ_HOARD 0 // Unvalidated A1 team plan: carry 48 gems (bank bag x1.6) before an ordinary bank trip.
#endif
#ifndef DZ_FIGHT
#define DZ_FIGHT 0 // Unvalidated A1 team plan: engage aggression x1.25 (no unseen-reinforcement margin).
#endif
#ifndef DZ_TURTLE
#define DZ_TURTLE 0 // Unvalidated A1 team plan: own-half groups only, engage aggression x0.65.
#endif
#ifndef DZ_JOB_GEAR
#define DZ_JOB_GEAR 0 // Experimental: cluster jobs can justify Prospector over Treasure.
#endif
#ifndef DZ_ECONOMY_V2
#define DZ_ECONOMY_V2 0 // Integrated Z6-Z11 economy/gear/combat/lease candidate; unpromoted development only.
#endif
#ifndef DZ_SIEGE
#define DZ_SIEGE 0 // Persistent gate waves with a reserved escape and heal-return; development only.
#endif

// Selected release keeps these off. Development candidates do not establish
// model calibration, competitive parity or release admission.
namespace dz::config {
inline constexpr bool economy_auction = DZ_ECONOMY_V2 != 0;
inline constexpr bool engagement_evaluator = DZ_ECONOMY_V2 != 0;
inline constexpr bool gear_planner = DZ_ECONOMY_V2 != 0;
inline constexpr bool camp_safety = DZ_CAMP_SAFETY != 0;
inline constexpr std::uint64_t full_fuel = 60000, lean_fuel = 25000, reserve = 12000;
inline constexpr std::uint64_t ordinary_turn_fuel = 100000; // CT-3 pinned budget.
inline constexpr int bank_bag = 30, contract_window = 6, crew_window = 40, avoid_rounds = 15, respawn_wait = 15;
inline constexpr int max_action_errors = 3;
}
