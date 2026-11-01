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
#define X1_PLAN 0 // Team-plan hook (1 = compiled in; X1_PLAN_ROUND / X1_PLAN_ID pick the plan). 0 = x1 exactly.
#endif
#ifndef X1_PLAN_ROUND
#define X1_PLAN_ROUND -1 // round from which plan X1_PLAN_ID is played (-1 = never)
#endif
#ifndef X1_PLAN_ID
#define X1_PLAN_ID 0 // 1 full map, 2 hoard, 3 fight harder, 4 turtle, 5 stricter home, 6 early-contact answer, 7 fast bank, 8 push
#endif
