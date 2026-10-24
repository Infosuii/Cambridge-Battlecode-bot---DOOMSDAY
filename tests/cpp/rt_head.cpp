// rt_head.cpp (agent B) - native tests of nn_head.cpp (decide/value/leaf, budget gate, cache, fallbacks, records).
// Built by tools/run_cpp_tests.py into a scratch tree prepared with tools/install_models.py for one profile, with
// -DNN_HOST_TEST (nn_budget.h host shim) and the stub nn_schema.h / nn_obs.h. The checks adapt to the compiled
// profile (nncfg::*). Usage: rt_head <variant> where variant names what the tree was built for:
//   zero_active | dev_active | shadow | training | selftest | badsum | nanw | schema
// Prints "PASS <name>" / "FAIL <name> ..." and "SUMMARY"; training records go to stdout as NFS1 lines.
#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>

#include "nn_budget.h"
#include "nn_head.h"
#include "nn_log.h"
#include "nn_obs.h"
#include "nn_rt.h"
#define NN_REGISTRY_WANT_MODELS
#include "nn_registry.h"

class Bot {};

static int g_fail = 0, g_pass = 0;
#define CHECK(cond, name, ...)                                                                                       \
    do {                                                                                                             \
        if (cond) {                                                                                                  \
            ++g_pass;                                                                                                \
            std::fprintf(stderr, "PASS %s\n", name);                                                                 \
        } else {                                                                                                     \
            ++g_fail;                                                                                                \
            std::fprintf(stderr, "FAIL %s ", name);                                                                  \
            std::fprintf(stderr, __VA_ARGS__);                                                                       \
            std::fprintf(stderr, "\n");                                                                              \
        }                                                                                                            \
    } while (0)

// ---------------------------------------------------------------- capture stub
static int g_captures = 0;
static bool g_capture_ok = true;
static float g_obs[nnobs::kObsDim];
bool nnobs::capture(const Bot&, RawTurn& out) {
    ++g_captures;
    std::memcpy(out.x, g_obs, sizeof g_obs);
    return g_capture_ok;
}

static void make_obs(std::uint64_t seed) {
    nnrt::SplitMix64 r{seed};
    for (float& v : g_obs) v = r.uniform() * 2.0f - 1.0f;
    float* amask = g_obs + nnobs::kSelfGlobalDim + nnobs::kAllyRows * nnobs::kAllyDim;
    float* emask = amask + nnobs::kAllyRows + nnobs::kEnemyRows * nnobs::kEnemyDim;
    for (int r2 = 0; r2 < nnobs::kAllyRows; ++r2) amask[r2] = r2 < 3 ? 1.0f : 0.0f;
    for (int r2 = 0; r2 < nnobs::kEnemyRows; ++r2) emask[r2] = r2 < 4 ? 1.0f : 0.0f;
}

static Bot g_bot;
using nncfg::H;

static void new_turn(std::uint32_t round) {
    nnh::idle(); // end of the previous turn: flush queued training records (leftover fuel)
    nnb::host::round = round;
    nnb::host::fuel = 1000000;
    nnb::begin_turn();
}

static void fill(nnh::Decision& d, H head, int K, int F, std::uint64_t seed) {
    d.head = head;
    d.K = K;
    d.F = F;
    d.context = 0;
    nnrt::SplitMix64 r{seed};
    for (int i = 0; i < K * F; ++i) d.feat[i] = r.uniform() * 2.0f - 1.0f;
    for (int k = 0; k < K; ++k) {
        d.legal[k] = 1;
        d.prior[k] = k == 0 ? 0.0f : -0.05f * static_cast<float>(k);
        d.id[k] = 100u + static_cast<std::uint32_t>(k);
    }
}

static const nnm::ModelDesc* model(H h) {
    const int i = nnreg::kHeadModel[static_cast<int>(h)];
    return i < 0 ? nullptr : nnreg::kModels[i];
}

static int head_F(H h) { return model(h) ? model(h)->head[static_cast<int>(h)].F : 24; }

// Reference logits for a decision through the model math directly (context from g_obs).
static void ref_logits(const nnh::Decision& d, float* logit) {
    const nnm::ModelDesc& m = *model(d.head);
    const nnm::HeadDesc& hd = m.head[static_cast<int>(d.head)];
    static nnm::Scratch s;
    float h[nnm::kMaxCtx];
    nnm::encode(m, g_obs, h, s);
    nnm::candidate_logits(m, hd, h, d.context, d.feat, d.K, d.legal, d.prior, logit);
}

// ---------------------------------------------------------------- generic fallback checks (every variant with a model)
static void test_fallbacks(H h) {
    static nnh::Decision d;
    const int F = head_F(h);
    new_turn(10);
    fill(d, h, 0, F, 1);
    CHECK(nnh::decide(g_bot, d).reason == nnh::kEmpty, "fallback_empty_set", "K=0");
    fill(d, h, 5, F, 1);
    d.legal[0] = 0;
    nnh::Result r = nnh::decide(g_bot, d);
    CHECK(r.reason == nnh::kTeacherIllegal && r.choice == 0 && !r.neural, "fallback_teacher_illegal", "reason %d",
          r.reason);
    fill(d, h, 5, F == 24 ? 23 : F + 1, 1);
    CHECK(nnh::decide(g_bot, d).reason == nnh::kSchemaMismatch, "fallback_feature_width_mismatch", "F mismatch");
    fill(d, h, 5, F, 1);
    d.feat[7] = std::nanf("");
    r = nnh::decide(g_bot, d);
    CHECK(r.reason == nnh::kNaN && r.choice == 0, "fallback_nan_feature", "reason %d", r.reason);
    fill(d, h, 5, F, 1);
    d.feat[3] = INFINITY;
    CHECK(nnh::decide(g_bot, d).reason == nnh::kNaN, "fallback_inf_feature", "inf");
    fill(d, h, 5, F, 1);
    d.prior[2] = std::nanf("");
    CHECK(nnh::decide(g_bot, d).reason == nnh::kNaN, "fallback_nan_prior", "nan prior");
    fill(d, h, 5, F, 1);
    d.prior[3] = 0.5f; // above the teacher's prior
    CHECK(nnh::decide(g_bot, d).reason == nnh::kBadPrior, "fallback_teacher_margin", "bad prior");
    fill(d, h, 5, F, 1);
    d.prior[3] = 0.5f;
    d.legal[3] = 0; // an illegal candidate's prior is irrelevant
    CHECK(nnh::decide(g_bot, d).reason != nnh::kBadPrior, "illegal_prior_ignored", "illegal prior checked");
    fill(d, h, 5, F, 1);
    d.context = 200;
    CHECK(nnh::decide(g_bot, d).reason == nnh::kBadInput, "fallback_bad_context_code", "context");
    fill(d, h, 16, F, 1);
    d.K = 17;
    CHECK(nnh::decide(g_bot, d).reason == nnh::kBadInput, "fallback_K_too_large", "K=17");
}

// Budget refusal: O(1) fallback without capture; context skipped for the turn; recovers next turn.
static void test_budget(H h) {
    static nnh::Decision d;
    const int F = head_F(h);
    new_turn(20);
    const int cap0 = g_captures;
    nnb::host::fuel = 3000; // below any worst case + reserves
    const bool adm = nnh::admit(g_bot, h, 8, 500);
    CHECK(!adm && nnh::last_reason(h) == nnh::kBudget, "budget_admit_refused", "admit=%d reason=%d", adm,
          nnh::last_reason(h));
    fill(d, h, 8, F, 2);
    nnh::Result r = nnh::decide(g_bot, d);
    const bool ctx = model(h)->head[static_cast<int>(h)].uses_ctx;
    CHECK(r.choice == 0 && !r.neural && (r.reason == nnh::kBudget || (ctx && r.reason == nnh::kEncoderSkipped)),
          "budget_decide_refused", "reason %d", r.reason);
    CHECK(g_captures == cap0, "budget_refusal_no_feature_work", "capture ran %d times", g_captures - cap0);
    if (ctx) {
        nnb::host::fuel = 1000000; // fuel back, same turn: the context stays skipped this turn (contract 3.3)
        r = nnh::decide(g_bot, d);
        CHECK(r.reason == nnh::kEncoderSkipped && g_captures == cap0, "encoder_skipped_rest_of_turn", "reason %d",
              r.reason);
    }
    new_turn(21);
    r = nnh::decide(g_bot, d);
    CHECK(r.reason == nnh::kOk || r.reason == nnh::kShadow, "budget_recovers_next_turn", "reason %d", r.reason);
    // Per-turn allowance: a huge pre-declared feature cost is refused even with plenty of fuel.
    new_turn(22);
    CHECK(!nnh::admit(g_bot, h, 8, static_cast<std::uint32_t>(nnreg::kTurnAllowance + 1)), "budget_turn_allowance",
          "allowance not enforced");
}

// Shared context cache per (turn, round) with explicit invalidation at begin_turn().
static void test_cache(H h) {
    static nnh::Decision d;
    const int F = head_F(h);
    if (!model(h)->head[static_cast<int>(h)].uses_ctx) return;
    new_turn(30);
    const int c0 = g_captures;
    fill(d, h, 6, F, 3);
    nnh::decide(g_bot, d);
    nnh::decide(g_bot, d);
    CHECK(g_captures == c0 + 1, "context_cached_within_turn", "captures %d", g_captures - c0);
    nnb::begin_turn();
    nnh::decide(g_bot, d);
    CHECK(g_captures == c0 + 2, "context_invalidated_by_begin_turn", "captures %d", g_captures - c0);
    nnb::host::round = 31; // round changed without begin_turn (defensive second key)
    nnh::decide(g_bot, d);
    CHECK(g_captures == c0 + 3, "context_invalidated_by_round", "captures %d", g_captures - c0);
    new_turn(32);
    g_capture_ok = false;
    const nnh::Result r = nnh::decide(g_bot, d);
    g_capture_ok = true;
    CHECK(r.reason == nnh::kCaptureFailed && r.choice == 0, "fallback_capture_failed", "reason %d", r.reason);
}

// Decisions against the reference math: argmax (active), teacher (shadow), padding/permutation properties.
static void test_scoring(H h, bool zero_residual) {
    static nnh::Decision d, e;
    const int F = head_F(h);
    const bool active = nncfg::mode(h) == nncfg::Mode::active;
    bool ok_choice = true, ok_teacher = true, ok_net = true;
    int non_teacher = 0;
    for (int t = 0; t < 200; ++t) {
        new_turn(100 + t);
        make_obs(1000 + t);
        const int K = 1 + t % 16;
        fill(d, h, K, F, 5000 + t);
        for (int k = 1; k < K; ++k) {
            d.legal[k] = (t + k) % 4 != 0;
            d.prior[k] = (t % 3 == 0) ? 0.0f : -0.01f * static_cast<float>((k * 7 + t) % 13); // ties with teacher
        }
        float logit[16];
        ref_logits(d, logit);
        const int best = nnrt::masked_argmax(logit, d.legal, K);
        const nnh::Result r = nnh::decide(g_bot, d);
        if (r.net != best) {
            if (ok_net) std::fprintf(stderr, "  [dbg] head %d t=%d K=%d net=%d best=%d reason=%d\n", static_cast<int>(h), t, K, r.net, best, r.reason);
            ok_net = false;
        }
        if (active && !nncfg::kTraining && (r.choice != best || !r.neural || r.reason != nnh::kOk)) ok_choice = false;
        if (!active && (r.choice != 0 || r.neural || r.reason != nnh::kShadow)) ok_teacher = false;
        if (zero_residual && r.choice != 0) ok_teacher = false;
        if (r.choice != 0) ++non_teacher;
    }
    CHECK(ok_net, "net_choice_equals_reference_argmax", "network pick differs from reference logits");
    if (active && !nncfg::kTraining) CHECK(ok_choice, "active_executes_argmax", "active choice != argmax");
    if (!active) CHECK(ok_teacher, "shadow_executes_teacher", "shadow executed a non-teacher candidate");
    if (zero_residual) CHECK(ok_teacher && non_teacher == 0, "zero_residual_always_teacher", "%d non-teacher", non_teacher);
    if (active && !zero_residual && !nncfg::kTraining)
        CHECK(non_teacher > 0, "dev_model_moves_choices", "dev model never left the teacher (plumbing not exercised)");

    // Padding invariance: extra illegal candidates do not change the logits of the real ones.
    make_obs(77);
    fill(d, h, 5, F, 9);
    e = d;
    e.K = 16;
    for (int k = 5; k < 16; ++k) {
        e.legal[k] = 0;
        e.prior[k] = 9.0f;
        for (int j = 0; j < F; ++j) e.feat[k * F + j] = 123.0f;
    }
    float l5[16], l16[16];
    ref_logits(d, l5);
    ref_logits(e, l16);
    CHECK(std::memcmp(l5, l16, 5 * sizeof(float)) == 0, "padding_invariance_logits", "padding changed logits");
    // Permutation equivariance: permuting candidates 1..K-1 permutes their logits exactly (per-candidate scoring).
    fill(d, h, 8, F, 11);
    e = d;
    const int perm[8] = {0, 5, 3, 7, 1, 2, 6, 4};
    for (int k = 0; k < 8; ++k) {
        e.prior[k] = d.prior[perm[k]];
        e.legal[k] = d.legal[perm[k]];
        std::memcpy(e.feat + k * F, d.feat + perm[k] * F, sizeof(float) * F);
    }
    float a[16], b[16];
    ref_logits(d, a);
    ref_logits(e, b);
    bool eq = true;
    for (int k = 0; k < 8; ++k) eq = eq && std::memcmp(&b[k], &a[perm[k]], 4) == 0;
    CHECK(eq, "permutation_equivariance_logits", "permuted logits differ");
    // Stable ties: identical candidates -> the lowest index (the teacher) wins.
    fill(d, h, 6, F, 13);
    for (int k = 1; k < 6; ++k) std::memcpy(d.feat + k * F, d.feat, sizeof(float) * F), d.prior[k] = d.prior[0];
    new_turn(400);
    const nnh::Result r = nnh::decide(g_bot, d);
    CHECK(r.net == 0 && (nncfg::kTraining || r.choice == 0), "identical_candidates_tie_to_teacher", "net %d choice %d",
          r.net, r.choice);
}

static void test_training(H h) {
    static nnh::Decision d;
    const int F = head_F(h);
    // Sampling sanity: fixed logits, many decisions (each a different PRNG stream) -> empirical ~ softmax.
    make_obs(5);
    fill(d, h, 4, F, 21);
    float logit[16], lp[16];
    ref_logits(d, logit);
    nnrt::masked_log_softmax(logit, d.legal, 4, lp);
    long cnt[4] = {};
    bool logp_ok = true;
    const int N = 4000;
    for (int i = 0; i < N; ++i) {
        new_turn(1000 + i);
        const nnh::Result r = nnh::decide(g_bot, d);
        if (r.choice < 0 || r.choice >= 4) break;
        ++cnt[r.choice];
        if (std::fabs(r.logp - lp[r.choice]) > 1e-6f || !r.neural) logp_ok = false;
    }
    double worst = 0;
    for (int k = 0; k < 4; ++k) {
        const double p = std::exp(double(lp[k]));
        worst = std::fmax(worst, std::fabs(double(cnt[k]) / N - p) / std::sqrt(p * (1 - p) / N + 1e-12));
    }
    CHECK(worst < 5.0, "training_sample_distribution", "z %g counts %ld %ld %ld %ld", worst, cnt[0], cnt[1], cnt[2],
          cnt[3]);
    CHECK(logp_ok, "training_logp_behaviour", "logged logp != log-softmax");
}

static void test_records_bound(H h) {
    static nnh::Decision d;
    const int F = head_F(h);
    new_turn(5000);
    const std::uint32_t w0 = nnlog::g_written, d0 = nnlog::g_dropped;
    fill(d, h, 3, F, 31);
    for (int i = 0; i < 20; ++i) nnh::decide(g_bot, d);
    nnh::idle(); // records are queued during the turn and written at its end
    const std::uint32_t w = nnlog::g_written - w0, dr = nnlog::g_dropped - d0;
    CHECK(w == nnreg::kMaxRecordsPerTurn && dr == 20 + 1 - nnreg::kMaxRecordsPerTurn, "records_bounded_per_turn",
          "written %u dropped %u", w, dr);
}

static void test_values() {
    new_turn(6000);
    make_obs(6);
    const float v = nnh::value(g_bot, H::value, 0);
    const float b = nnh::value(g_bot, H::belief, 3);
    const float bad = nnh::value(g_bot, H::value, 99);
    float lf[16];
    for (int i = 0; i < 16; ++i) lf[i] = 0.1f * i - 0.5f;
    const float l = nnh::leaf(g_bot, lf, head_F(H::ts_leaf), 0);
    const bool active = nncfg::mode(H::value) == nncfg::Mode::active;
    CHECK(std::isfinite(v) && std::isfinite(b) && bad == 0.0f && std::isfinite(l), "value_heads_finite", "v %g b %g", v, b);
    if (!active) CHECK(v == 0.0f && b == 0.0f && l == 0.0f, "value_heads_zero_in_shadow", "shadow returned a value");
    if (active) {
        const nnm::ModelDesc& m = *model(H::value);
        static nnm::Scratch s;
        float h[nnm::kMaxCtx], y[nnm::kMaxOut];
        nnm::encode(m, g_obs, h, s);
        nnm::value_out(m, m.head[static_cast<int>(H::value)], h, y);
        CHECK(v == y[0], "value_matches_reference", "%g vs %g", v, y[0]);
        const float bound = m.head[static_cast<int>(H::ts_leaf)].R;
        CHECK(std::fabs(l) <= bound, "leaf_bounded", "%g", l);
    }
    std::uint8_t lr = nnh::last_reason(H::value);
    CHECK(lr == nnh::kBadInput, "value_bad_output_index", "reason %d", lr);
}

int main(int argc, char** argv) {
    const std::string v = argc > 1 ? argv[1] : "dev_active";
    make_obs(1);
    nnb::host::fuel = 100000000; // the draft-like warmup verifies all segments
    nnh::warmup();
    const H cand = H::move, nectx = H::draft_pick;
    if (v == "badsum" || v == "nanw") {
        new_turn(1);
        static nnh::Decision d;
        fill(d, cand, 4, head_F(cand), 1);
        const nnh::Result r = nnh::decide(g_bot, d);
        fill(d, nectx, 4, head_F(nectx), 1);
        const nnh::Result r2 = nnh::decide(g_bot, d);
        CHECK(r.reason == nnh::kBadModel && r.choice == 0 && !r.neural, "bad_weights_fallback_ctx_head", "reason %d",
              r.reason);
        CHECK(r2.reason == nnh::kBadModel, "bad_weights_whole_model_invalid", "reason %d", r2.reason);
        CHECK(nnh::value(g_bot, H::value, 0) == 0.0f, "bad_weights_value_zero", "value");
    } else if (v == "schema") {
        new_turn(1);
        static nnh::Decision d;
        fill(d, cand, 4, head_F(cand), 1);
        const nnh::Result r = nnh::decide(g_bot, d);
        CHECK(r.reason == nnh::kSchemaMismatch && r.choice == 0, "schema_hash_mismatch_fallback", "reason %d", r.reason);
        fill(d, nectx, 4, head_F(nectx), 1);
        const nnh::Result r2 = nnh::decide(g_bot, d);
        CHECK(r2.reason == nnh::kOk || r2.reason == nnh::kShadow, "schema_mismatch_spares_non_context_head", "reason %d",
              r2.reason);
    } else if (v == "selftest") {
        new_turn(1);
        nnh::turn_start(); // prints NNST lines on stdout
        CHECK(true, "selftest_ran", "%s", "");
    } else {
        const bool zero = v == "zero_active" || v == "shadow";
        for (H h : {H::draft_pick, H::strategy, H::move, H::combat}) {
            test_fallbacks(h);
            test_budget(h);
            test_cache(h);
            test_scoring(h, zero);
        }
        if (v == "training") {
            test_training(H::combat);
            test_records_bound(H::shop);
        } else {
            test_values();
        }
    }
    nnh::idle();
    std::fprintf(stderr, "SUMMARY rt_head_%s pass=%d fail=%d\n", v.c_str(), g_pass, g_fail);
    return g_fail ? 1 : 0;
}
