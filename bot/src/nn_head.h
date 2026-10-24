// nn_head.h (agent B) - the single entry point for every learned decision (CONTRACTS 3.2). Pure: no SDK include.
//
// Every learned decision is a masked choice among K <= 16 candidates (candidate 0 = the teacher's choice, always
// legal) or a bounded value. Semantics:
//   logit_k = prior_k + R * act(r_k / R) for legal k (-inf otherwise); r_k = residual MLP over [shared context h,
//   candidate features, call-site context code]. prior_0 >= prior_k is required (teacher margin) so a zero residual
//   returns candidate 0 exactly; ties go to the lowest index.
//   mode off    : compiled out at the call site (if constexpr); decide() returns {0, false, 0, kOff}.
//   mode shadow : the head runs (and is logged when kTraining) but the teacher's candidate 0 is executed.
//   mode active : argmax of the logits (deployment) or a sample from their softmax (kTraining, logp logged).
//   Any problem (budget refusal, missing/invalid model, schema mismatch, NaN/Inf, empty set, illegal teacher,
//   context unavailable) returns candidate 0 with neural=false and a Reason; fallback is O(1).
//
// Call-site pattern (inside `if constexpr (nncfg::mode(nncfg::H::x) != nncfg::Mode::off)`):
//   teacher choice already computed and valid;
//   if (nnh::admit(bot, H::x, K, kFeatureWorstCase)) {      // BEFORE building features
//       static nnh::Decision d; d.head = H::x; d.K = ...; d.F = ...; fill feat/legal/prior/id/context;
//       const nnh::Result r = nnh::decide(bot, d);           // r.choice indexes the candidates
//   }
// decide() without a preceding admit() admits itself (feature cost 0) - the features were then built unguarded.
#pragma once
#include <cstdint>

#include "nn_config.h"

class Bot;

namespace nnh {

inline constexpr int kMaxK = 16, kMaxF = 24;

enum Reason : std::uint8_t {
    kOk = 0,             // network choice executed (active mode)
    kShadow = 1,         // network ran; teacher executed (shadow mode)
    kOff = 2,            // head is off
    kBudget = 3,         // refused by the fuel admission
    kNoModel = 4,        // no model installed for this head
    kBadModel = 5,       // structural/checksum/NaN failure in the installed weights (sticky for the game)
    kModelPending = 6,   // checksum verification not finished (fuel); retried on later calls
    kNaN = 7,            // non-finite features, priors, observation or outputs
    kEmpty = 8,          // K == 0
    kTeacherIllegal = 9, // candidate 0 not legal
    kEncoderSkipped = 10, // shared context refused/failed for this turn
    kSchemaMismatch = 11, // observation/action schema hash, dimension or F mismatch
    kBadInput = 12,      // K or F out of range, context code out of range
    kBadPrior = 13,      // prior_k > prior_0 for a legal k (teacher margin violated)
    kCaptureFailed = 14, // nnobs::capture returned false
    kReasonCount = 15
};

inline constexpr const char* kReasonName[kReasonCount] = {
    "ok",    "shadow",          "off",         "budget",          "no_model",   "bad_model",
    "model_pending", "nan",     "empty",       "teacher_illegal", "encoder_skipped", "schema_mismatch",
    "bad_input", "bad_prior",   "capture_failed"};

struct Decision {
    nncfg::H head;
    int K = 0;
    int F = 0;                          // this head's candidate feature width (from its schema)
    float feat[kMaxK * kMaxF];          // row-major K x F, normalised/clipped by the candidate builder
    std::uint8_t legal[kMaxK];          // deterministic legality mask (1 legal)
    float prior[kMaxK];                 // teacher prior logit per candidate; prior[0] >= prior[k]
    std::uint32_t id[kMaxK];            // stable identifiers (logged)
    std::uint8_t context = 0;           // call-site context code
};

struct Result {
    int choice;          // index into the candidates (0 = teacher)
    bool neural;         // true iff `choice` came from the network (active mode, no fallback)
    float logp;          // log behaviour probability of `choice` (0 = deterministic; only computed when kTraining)
    std::uint8_t reason; // Reason
    std::int8_t net;     // the network's own pick (argmax or sample) even in shadow mode; -1 when not computed
};

inline constexpr Result fallback(std::uint8_t reason) { return Result{0, false, 0.0f, reason, -1}; }

// Budget gate before feature work. K = candidates that will be built, feature_cost = the builder's measured worst
// case for building them. False = do not build; the teacher choice stands (counted as a budget fallback).
bool admit(const Bot& bot, nncfg::H head, int K, std::uint32_t feature_cost);

// Score and choose (see header comment). `d` may be modified (padding beyond K is ignored).
Result decide(const Bot& bot, Decision& d);

// Value-kind heads (H::value: 0 win_logit, 1 margin, 2 carry_risk; H::belief: sector logits). 0 on any fallback
// and in shadow mode; never NaN.
float value(const Bot& bot, nncfg::H head, int output);

// ts_leaf: bounded residual R * act(r / R) for one leaf feature vector; 0 on fallback / shadow; never NaN.
float leaf(const Bot& bot, const float* feat, int F, std::uint8_t context = 0);

// Call right after nnb::begin_turn() (lead hook): selftest fixtures (kSelfTest), telemetry lines, episode markers.
void turn_start();

// Call from the draft (10x fuel): verifies the installed models' checksums so gameplay turns need not.
void warmup();

// Reason of the last refused/failed decision of `head` this game (telemetry / tests).
std::uint8_t last_reason(nncfg::H head);

} // namespace nnh
