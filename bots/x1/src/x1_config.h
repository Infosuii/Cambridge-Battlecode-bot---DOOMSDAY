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
