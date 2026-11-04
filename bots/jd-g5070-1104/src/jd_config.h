// jd-g5070-1104 experiment switches. Every switch defaults to 0; the default build is byte-identical to v92
// (release WASM SHA-256 5704d7ba41acca8f5c369c963cec1719c1285780a532cc797857d8d7e3a06d47).
#pragma once
// JD_FUELPROF: per-phase fuel profile logging (diagnostic only).
#ifndef JD_FUELPROF
#define JD_FUELPROF 0
#endif
// JD_GOV: whole-turn fuel reservations in runtime_budget.h (FEAT-002).
#ifndef JD_GOV
#define JD_GOV 0
#endif
// JD_MEM: shared-word / draft-buffer codec and region ownership (FEAT-002).
#ifndef JD_MEM
#define JD_MEM 0
#endif
// JD_NN: neural actor runtime (FEAT-003); JD_NN_EVENT: event-driven inference cadence.
#ifndef JD_NN
#define JD_NN 0
#endif
#ifndef JD_NN_EVENT
#define JD_NN_EVENT 0
#endif
// JD_CONTACT: contact movement and action ordering (FEAT-004).
#ifndef JD_CONTACT
#define JD_CONTACT 0
#endif
// JD_PROGRESS: no-progress / oscillation / unreachable target detection (FEAT-004).
#ifndef JD_PROGRESS
#define JD_PROGRESS 0
#endif
