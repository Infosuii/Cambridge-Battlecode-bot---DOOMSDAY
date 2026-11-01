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
