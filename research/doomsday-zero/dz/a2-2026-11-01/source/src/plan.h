#pragma once
#include "config.h"
#if DZ_PLAN_TABLE
#include "map_signature.h"
#endif
#include <cstdint>
// Z14 v1 per-map plans (DZ_PLAN_TABLE). Each row: static map signature, draft
// variant (-1 keeps the incumbent choice) and a bit per experiment below. Rows
// come from tools/dz_plan_select.py; an absent map plays the default (0 bits).
// With DZ_PLAN_TABLE 0, DZ_ON(X) is the compile-time DZ_X and nothing here runs.
namespace dz {
enum PlanBit : unsigned { plan_EE, plan_EE_REGROUP, plan_GEAR_SURVIVE, plan_GEAR_PROSPECT, plan_GEAR_HEALTH, plan_CREWS, plan_CREW_ALL, plan_BANK_NEAR_MIN, plan_BANK_BIG, plan_RING_GATES, plan_OPENING_GOLD, plan_GOLD_VALUE, plan_EE2, plan_EE2_BOLD, plan_HOME, plan_HOARD, plan_FIGHT, plan_TURTLE };
#if DZ_PLAN_TABLE
struct PlanRow { std::uint32_t signature; int draft; std::uint32_t bits; };
inline constexpr PlanRow plan_rows[] = {
#include "map_plans.inc"
};
// One row per pool map, always: the lookup then runs the same instructions whatever the table holds, so a screen
// build (every row one config) and the final table play identical code; only data differs.
static_assert(sizeof(plan_rows) / sizeof(plan_rows[0]) == 70, "map_plans.inc needs exactly 70 rows (dz_plan_select.py)");
inline std::uint32_t plan_bits = 0;
inline int plan_draft = -1;
inline bool plan_loaded = false;
// A2 branch hook: volatile with non-zero initialisers, so baseline (round 5000) and branch binaries differ only in
// data and play identically before the switch round (lab lesson: a folded constant shifted the code section).
inline volatile std::uint32_t switch_round = DZ_SWITCH_ROUND;
inline volatile std::uint32_t switch_bits = DZ_SWITCH_BITS;
inline void apply_switch(unsigned round) {
    if (round >= switch_round) plan_bits = switch_bits & 0x7fffffffu;
}
inline void load_plan(std::uint32_t signature) {
    if (plan_loaded) return;
    for (const auto& row : plan_rows) if (row.signature == signature) { plan_bits = row.bits; plan_draft = row.draft; }
    plan_loaded = true;
}
#endif
}
#if DZ_PLAN_TABLE
#define DZ_ON(name) (((::dz::plan_bits >> ::dz::plan_##name) & 1u) != 0)
#else
#define DZ_ON(name) (DZ_##name != 0)
#endif
// Code and state an experiment needs: compiled when the flag or the table is on.
#define DZ_HAS(name) (DZ_##name || DZ_PLAN_TABLE)
namespace dz {
// Gold's weight against gems in job value: 0.1 by default; R250 v76 earns 1.75x DZ's gold (idle bench).
inline float gold_weight(unsigned round) {
    if (DZ_ON(OPENING_GOLD) && round < 250) return .5f;
    if (DZ_ON(GOLD_VALUE)) return .3f;
    return .1f;
}
}
