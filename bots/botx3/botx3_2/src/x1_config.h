#pragma once
// x1 experiment flags (default 0 = v81hl's behaviour; tools/dz.py --candidate-bot x1 --set X1_FLAG=1).
#ifndef X1_MASTERY
#define X1_MASTERY 1
#endif
#ifndef X1_FUEL_PROBE
#define X1_FUEL_PROBE 0 // Diagnostics: 1 = no gated-altar/sole-group behaviours (A2_GATE_FROM/A2_SOLE_FROM off); 2 = no DP plan.
#endif
#if X1_FUEL_PROBE == 1
#define A2_GATE_FROM 100000
#define A2_SOLE_FROM 100000
#elif X1_FUEL_PROBE == 2
#define A2_DP_UNTIL 0
#endif
#ifndef X1_TEL
#define X1_TEL 0 // Diagnostics: v81hl's A2_TEL telemetry (A2SUS fuel-suspension trails) on.
#endif
#if X1_TEL
#define A2_TEL 1
#endif
#ifndef X1_BUSHPRE
#define X1_BUSHPRE 15
#endif
#ifndef X1_BUSHPRE_LAZY
#define X1_BUSHPRE_LAZY 60
#endif
#ifndef X1_SIEGEFUEL
#define X1_SIEGEFUEL 55
#endif
#ifndef X1_WALKRES
#define X1_WALKRES 10
#endif
#define X1_WALK_RESERVE (X1_WALKRES ? static_cast<std::uint64_t>(X1_WALKRES) * 1000 : rb::kTailReserve)
#ifndef X1_WALKTAIL
#define X1_WALKTAIL 3
#endif
#ifndef X1_FAST_SIEGE
#define X1_FAST_SIEGE 1 // Fuel: cache the siege line-of-sight ring per alive-camp set (same decisions, no per-turn scan).
#endif
#ifndef A2_CAMPWATCH
#define A2_CAMPWATCH 1 // x1 base (2026-11-01): v81hl's switched-off camp watch, +7 wins vs v81hl, 338/560 league wins with fast siege.
#endif
#ifndef X1_ALONE
#define X1_ALONE 1
#endif
#ifndef X1_SECURE
#define X1_SECURE 1
#endif
#ifndef X1_SECURE_MULT
#define X1_SECURE_MULT 3.0f
#endif
#ifndef X1_HUNT_SOLO
#define X1_HUNT_SOLO 5
#endif
#ifndef X1_PLAN
#define X1_PLAN 1
#endif
#ifndef X1_PLAN_ROUND
#define X1_PLAN_ROUND 150
#endif
#ifndef X1_PLAN_ID
#define X1_PLAN_ID 4
#endif
#ifndef X1_ANTIFEED
#define X1_ANTIFEED 3
#endif
#ifndef X1_ANTIFEED_WIN
#define X1_ANTIFEED_WIN 150
#endif
#ifndef X1_HEARTFIX
#define X1_HEARTFIX 1
#endif
#ifndef X1_SOAK64
#define X1_SOAK64 1
#endif
#define X1_SOAK_N (X1_SOAK64 ? 64 : 12)
#ifndef X1_PRUNEFIX
#define X1_PRUNEFIX 1
#endif
#ifndef X1_FLEEHOLD
#define X1_FLEEHOLD 8
#endif
#ifndef X1_TEAMWIN
#define X1_TEAMWIN 1
#endif
#ifndef X1_SIEGE_STRICT
#define X1_SIEGE_STRICT 1
#endif
#ifndef X1_BAGRISK
#define X1_BAGRISK 60
#endif
#ifndef X1_FLEEDROP
#define X1_FLEEDROP 25
#endif
#ifndef X1_ECON
#define X1_ECON 1
#endif
#ifndef X1_WAIT_MULT
#define X1_WAIT_MULT 1.5f
#endif
#ifndef X1_STAGE_MULT
#define X1_STAGE_MULT 0.5f
#endif
#ifndef X1_NEED_MULT
#define X1_NEED_MULT 1.3f
#endif

#ifndef X3_PLAN_END
#define X3_PLAN_END 500
#endif
#ifndef X3_BANKCYCLE
#define X3_BANKCYCLE 3
#endif
#ifndef X3_COVER_SAFE
#define X3_COVER_SAFE 1
#endif
#ifndef X3_TRACE
#define X3_TRACE 0
#endif
#ifndef X3_TEAM
#define X3_TEAM 14
#endif
#ifndef X3_TEAM_FARM
#define X3_TEAM_FARM 1
#endif
#ifndef X3_TEAM_RACE
#define X3_TEAM_RACE 1
#endif
#ifndef X3_DRAFT_PATHS
#define X3_DRAFT_PATHS 1
#endif
#ifndef X3_DRAFT_USE
#define X3_DRAFT_USE 1
#endif

#ifndef A2_BURST2
#define A2_BURST2 1
#endif

#ifndef A2_TS_VIS
#define A2_TS_VIS 1
#endif

#ifndef V58_LOCKS
#define V58_LOCKS 1
#endif

#ifndef A2_DISENGAGE
#define A2_DISENGAGE 1
#endif

#ifndef A2_BELIEF
#define A2_BELIEF 1
#endif

#ifndef APEX_PLAN
#define APEX_PLAN 1
#endif
