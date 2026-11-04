// jd-g5070-1104 experiment switches. Every switch defaults to 0; the default build is byte-identical to v92
// (release WASM SHA-256 5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47).
#pragma once
// JD_FUELPROF: per-stage fuel profile (diagnostic only): PROF_CHECK checkpoints record fuel_remaining() (without
// A2_TEL's other instrumentation) and the fuel between consecutive checkpoints is aggregated into 1k-fuel
// histograms per (checkpoint, phase), printed as JDPF lines (common.h a2tel::jdpf).
#ifndef JD_FUELPROF
#define JD_FUELPROF 0
#endif
// JD_FUELPROBE: phase-fuel diagnostic (main.cpp): one JDFP line per unit turn with phase, fuel at entry and exit,
// draft-VM global transfer and host-call cost samples (diagnostic only, never in a scored build).
#ifndef JD_FUELPROBE
#define JD_FUELPROBE 0
#endif
// JD_GOV: whole-turn fuel reservations in runtime_budget.h (FEAT-002), bits for the three stages the baseline profile
// caught suspending (FUEL_BENCH.md): 1 = group-field order preparation admitted only with room for a full field
// (first champion turn on 98x98 maps: every body suspended), 2 = siege line-of-sight table initialisation admitted
// only with its worst case plus the execute and tail reservations (fallback: the unfiltered siege ring this turn),
// 4 = resumable bush-cluster labelling (the existing X1_BUSHPRE mechanism, floor 50k: an unfinished cluster reads as
// unknown and resumes next turn; ward_reveal labelled ~72k in one go).
// Bit 8 = the whole-turn reservation API only (phases, admit_optional), no stage change; it is the default when
// JD_NN_EVENT is set (the event runtime admits its pipeline stages through it).
#ifndef JD_GOV
#if defined(JD_NN_EVENT) && JD_NN_EVENT
#define JD_GOV 8
#else
#define JD_GOV 0
#endif
#endif
#if (JD_GOV & 4) && !defined(X1_BUSHPRE)
#define X1_BUSHPRE 50
#endif
// JD_GOVLOG: diagnostic governor trigger counters (JDGOV lines every 100 rounds).
#ifndef JD_GOVLOG
#define JD_GOVLOG 0
#endif
// JD_MEM: shared-word / draft-buffer codec and region ownership (FEAT-002).
#ifndef JD_MEM
#define JD_MEM 0
#endif
// Memory fixes proven by tools/jd_g5070-1104/tests/mem_test.cpp (each its own switch; MEMORY_SCHEMA.md):
// JD_EVTONCE = N: apply each distinct respawn-event word once per reader and reject decodes more than N rounds ahead
// (an unchanged event read again after 64+ rounds decodes as a phantom future respawn, up to 191 rounds ahead).
#ifndef JD_EVTONCE
#define JD_EVTONCE 0
#endif
// JD_SIGHTAGE: an unchanged enemy sighting keeps ageing on the reader's clock (mod-64 age made it fresh again).
#ifndef JD_SIGHTAGE
#define JD_SIGHTAGE 0
#endif
// JD_MEMLOG: diagnostic trigger counters for JD_EVTONCE / JD_SIGHTAGE (JDMEM lines every 250 rounds).
#ifndef JD_MEMLOG
#define JD_MEMLOG 0
#endif
// JD_NN: neural actor runtime (FEAT-003). JD_NN = Agent 2's A2_NN bits (1 the student picks the farming target
// group, 2 its behaviour head gates banking); the network path (nnrec.cpp, nn_infer.h, jd_nn_weights.h, ported by
// tools/jd_g5070-1104/mk_nn.py from agent2-neural 56b60b96) compiles only when A2_NN != 0.
#ifndef JD_NN
#define JD_NN 0
#endif
#ifndef A2_NN
#define A2_NN JD_NN
#endif
#ifndef A2_NN_MACRO
#define A2_NN_MACRO 0
#endif
#ifndef A2_NN_LAYOUT
#define A2_NN_LAYOUT 2 // the acting network's feature layout (2 = 500 features)
#endif
#ifndef A2_NNREC_LAYOUT
#define A2_NNREC_LAYOUT 2
#endif
#ifndef A2_NNREC
#define A2_NNREC 0
#endif
// JD_NN_EVENT (needs JD_NN & 1): event-driven inference (jd_nn_event.cpp). The network runs, pipelined over the
// spare fuel at the end of turns, only when the committed target finished or became invalid, on respawn, on leaving
// contact, when the bag crosses a bank threshold, on a claim conflict, or every JD_NN_PERIOD rounds; the published
// target is held until then (max JD_NN_MAXDUR rounds). Without a valid decision v92 chooses (fallback).
// JD_NN_ZERO = 1: the same computation at the same cadence, outputs ignored (data-only control).
// JD_NN_LOG = 1: JDN decision / counter lines (benchmarks). JD_NN_REC = 1: NR feature rows of every decision
// (DAgger / on-policy data at the deployed cadence). JD_NN_DUMP = N: golden fixture lines (features + all logits)
// for the first N decisions of each champion.
#ifndef JD_NN_EVENT
#define JD_NN_EVENT 0
#endif
#ifndef JD_NN_ZERO
#define JD_NN_ZERO 0
#endif
#ifndef JD_NN_LOG
#define JD_NN_LOG 0
#endif
#ifndef JD_NN_REC
#define JD_NN_REC 0
#endif
#ifndef JD_NN_DUMP
#define JD_NN_DUMP 0
#endif
#ifndef JD_NN_PERIOD
#define JD_NN_PERIOD 16
#endif
#ifndef JD_NN_MAXDUR
#define JD_NN_MAXDUR 64
#endif
#ifndef JD_NN_STALE
#define JD_NN_STALE 8 // a pipelined decision whose features are older than this many rounds is discarded
#endif
#ifndef JD_NN_HYST
#define JD_NN_HYST 0.5f // periodic replans switch the held target only for a logit gain above this
#endif
#if JD_NN_EVENT && (!(A2_NN & 1) || !JD_GOV)
#error "JD_NN_EVENT needs JD_NN & 1 and the JD_GOV reservation API"
#endif
// JD_CONTACT: contact movement and action ordering (FEAT-004).
#ifndef JD_CONTACT
#define JD_CONTACT 0
#endif
// JD_PROGRESS: no-progress / oscillation / unreachable target detection (FEAT-004).
#ifndef JD_PROGRESS
#define JD_PROGRESS 0
#endif
