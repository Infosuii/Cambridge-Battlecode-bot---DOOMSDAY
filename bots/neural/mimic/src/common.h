// Build switches for the mimic bot (a local stand-in for a top team; see research/mimic/README.md).
#pragma once

// Which team to imitate: an index into kTeamNames (weights.h), or -1 for all top teams pooled. The draft, the items
// and the perma-recall habit come from team_tables.h under the same name (the pooled "top" row when absent).
#define MIMIC_TEAM -1
// Draft from the team's table (0: the fixed fallback order only).
#define MIMIC_DRAFT 1
// Start a recall at the end of every turn and cancel it at the start of the next, for teams that do this.
#define MIMIC_PERMA_RECALL 1
// Logit bonus for keeping the previous turn's objective (the models are fitted without it; it stops dithering
// between two nearly equal objectives).
#define MIMIC_STICKY 0.5f
// Parity build: print one line per turn with the observation and feature hashes (tools/mimic/parity.py).
#define MIMIC_PARITY 0
// Seed for tie-breaking noise in decisions (0: none). Local runs vary it the same way other bots use NOVA_SEED.
#define NOVA_SEED 1
// Fuel probe: print the fuel spent by each stage of a turn every 25 rounds.
#define MIMIC_FUEL 0
// Trace: print each turn's top objectives (diagnostics only).
#define MIMIC_TRACE 0
