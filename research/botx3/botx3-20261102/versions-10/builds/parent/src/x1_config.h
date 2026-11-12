#pragma once
// x1 experiment flags (default 0 = v81hl's behaviour; tools/dz.py --candidate-bot x1 --set X1_FLAG=1).
#ifndef X1_MASTERY
#define X1_MASTERY 0 // Draft: penalise champions x1 plays worst (draft-net score bias).
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
#define X1_SIEGEFUEL 0 // Fuel: fill the siege line-of-sight cache only above X1_SIEGEFUEL k fuel (was 30k), direct bit writes.
#endif
#ifndef X1_WALKRES
#define X1_WALKRES 0 // Fuel: walk_toward's capped path searches keep X1_WALKRES k fuel for the rest of the turn (was 6k; 19 of 29 plan-4 fuel-outs crossed right after a walk).
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
#define X1_ALONE 0 // Isolation: no ally within 5 and an enemy within 10 -> walk to the nearest ally (teammate's untested alone alert).
#endif
#ifndef X1_SECURE
#define X1_SECURE 0 // MAPF kill-securing coordinator: a target killable this round by allies in reach is worth X1_SECURE_MULT x more.
#endif
#ifndef X1_SECURE_MULT
#define X1_SECURE_MULT 3.0f
#endif
#ifndef X1_HUNT_SOLO
#define X1_HUNT_SOLO 0 // Lone hunters: with no ally within 5, hunt only enemies sighted within this many tiles (0 = off).
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
#define X1_ANTIFEED 0 // Anti-feeding: this many team deaths within X1_ANTIFEED_WIN rounds -> the team plays safe (0 = off).
#endif
#ifndef X1_ANTIFEED_WIN
#define X1_ANTIFEED_WIN 150
#endif
#ifndef X1_HEARTFIX
#define X1_HEARTFIX 0 // audit B01: fight forecast with Heart of Ruin dash landing damage/stun and missing-health damage (A2_KITFIX 25 -> 31).
#endif
#ifndef X1_SOAK64
#define X1_SOAK64 0 // audit B02: camp danger counts up to 64 members per group (12 = v81hl).
#endif
#define X1_SOAK_N (X1_SOAK64 ? 64 : 12)
#ifndef X1_PRUNEFIX
#define X1_PRUNEFIX 0 // audit B03: candidate prune bound includes the later campwatch and dominant-group multipliers.
#endif
#ifndef X1_FLEEHOLD
#define X1_FLEEHOLD 0 // audit F01: rounds after a flee during which a champion keeps away from enemies seen within 8 (0 = off).
#endif
#ifndef X1_TEAMWIN
#define X1_TEAMWIN 0 // audit F03: the win-now bank counts the whole team's carried gems.
#endif
#ifndef X1_SIEGE_STRICT
#define X1_SIEGE_STRICT 0 // audit B04: use the siege LOS cache only when every live camp is cached (else the unfiltered ring).
#endif
#ifndef X1_BAGRISK
#define X1_BAGRISK 0 // Bag risk: carrying this many gems with an enemy seen within 10 in 5 rounds -> bank now (0 = off).
#endif
#ifndef X1_FLEEDROP
#define X1_FLEEDROP 0 // audit F01 alt: drop the camp target on a flee and skip it for this many rounds (0 = off).
#endif
#ifndef X1_ECON
#define X1_ECON 0 // Economy multipliers below (1 = compiled in).
#endif
#ifndef X1_WAIT_MULT
#define X1_WAIT_MULT 1.0f // x respawn-wait cost (more = leave for another camp sooner)
#endif
#ifndef X1_STAGE_MULT
#define X1_STAGE_MULT 1.0f // x helper staging timeout
#endif
#ifndef X1_NEED_MULT
#define X1_NEED_MULT 1.0f // x solo camp health budget (more = take more camps alone)
#endif

#ifndef X3_PLAN_END
#define X3_PLAN_END 0
#endif
#ifndef X3_BANKCYCLE
#define X3_BANKCYCLE 0
#endif
#ifndef X3_COVER_SAFE
#define X3_COVER_SAFE 0
#endif
#ifndef X3_TRACE
#define X3_TRACE 0
#endif
#ifndef X3_TEAM
#define X3_TEAM 0
#endif
#ifndef X3_TEAM_FARM
#define X3_TEAM_FARM 1
#endif
#ifndef X3_TEAM_RACE
#define X3_TEAM_RACE 0
#endif
#ifndef X3_DRAFT_PATHS
#define X3_DRAFT_PATHS 0
#endif
#ifndef X3_DRAFT_USE
#define X3_DRAFT_USE 1
#endif
#ifndef X3_ARBITRATION
#define X3_ARBITRATION 0
#endif
#ifndef X3_ARBITER_USE
#define X3_ARBITER_USE 1
#endif
#ifndef X3_BANK_COMMIT
#define X3_BANK_COMMIT 0
#endif
#ifndef X3_BANK_COMMIT_USE
#define X3_BANK_COMMIT_USE 1
#endif
#ifndef X3_MASTERY_FIX
#define X3_MASTERY_FIX 0
#endif
#ifndef X3_MASTERY_FIX_USE
#define X3_MASTERY_FIX_USE 1
#endif
#ifndef X3_BANK_PROBE
#define X3_BANK_PROBE 0
#endif
#ifndef X3_PLAN_NATIVE
#define X3_PLAN_NATIVE 0
#endif
#ifndef X3_PLAN_NATIVE_USE
#define X3_PLAN_NATIVE_USE 1
#endif
#ifndef X3_DRAFT_ROLES
#define X3_DRAFT_ROLES 0
#endif
#ifndef X3_DRAFT_ROLES_USE
#define X3_DRAFT_ROLES_USE 1
#endif
#ifndef X3_SIEGE_ADMIT
#define X3_SIEGE_ADMIT 0
#endif
#ifndef X3_SIEGE_ADMIT_USE
#define X3_SIEGE_ADMIT_USE 1
#endif
#ifndef X3_CHIP_PLAN
#define X3_CHIP_PLAN 0
#endif
#ifndef X3_CHIP_PLAN_USE
#define X3_CHIP_PLAN_USE 1
#endif
