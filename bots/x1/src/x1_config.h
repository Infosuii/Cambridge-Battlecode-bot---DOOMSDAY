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
