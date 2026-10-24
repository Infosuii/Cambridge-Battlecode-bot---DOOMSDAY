// nn_head.cpp (agent B) - decide()/value()/leaf(): budget gate, model verification, shared context, scoring, mode,
// fallback, training records. With NN_ANY_HEAD == 0 this translation unit is empty (no code, no data, no
// initialisers): nothing below the #if is compiled.
#include "nn_config.h"

#if NN_ANY_HEAD
#include <cstdio>

#include "nn_budget.h"
#include "nn_head.h"
#include "nn_log.h"
#include "nn_model.h"
#include "nn_obs.h"
#include "nn_rt.h"
#include "nn_schema.h"
#define NN_REGISTRY_WANT_MODELS
#include "nn_registry.h"

namespace nnh {
namespace {

using nncfg::H;
using nncfg::Mode;
constexpr int kH = static_cast<int>(H::count);
static_assert(kH == nnm::kHeads, "head enum and model format disagree");
static_assert(kMaxK <= 64 && kMaxF <= nnm::kMaxF, "kernel buffers");

constexpr int kNumModels = nnreg::kNumModels;
constexpr int kModelSlots = kNumModels > 0 ? kNumModels : 1;

constexpr const nnm::ModelDesc* model_of(int h) {
    return nnreg::kHeadModel[h] < 0 ? nullptr : nnreg::kModels[nnreg::kHeadModel[h]];
}

// Observation compatibility of a model with the compiled observation schema (nn_schema.h, agent C).
constexpr bool obs_ok(const nnm::ModelDesc& m) {
    return m.obs_schema_hash == nnobs::kObsSchemaHash && m.self_dim == nnobs::kSelfGlobalDim &&
           m.ally_rows == nnobs::kAllyRows && m.ally_dim == nnobs::kAllyDim && m.enemy_rows == nnobs::kEnemyRows &&
           m.enemy_dim == nnobs::kEnemyDim && nnm::obs_dim(m) == nnobs::kObsDim;
}

// Compile-time status of every head: kOk, kOff, kNoModel, kBadModel (structure) or kSchemaMismatch.
constexpr std::uint8_t static_status(int h) {
    if (nncfg::kMode[h] == Mode::off) return kOff;
    const nnm::ModelDesc* m = model_of(h);
    if (!m) return kNoModel;
    if (!nnm::desc_ok(*m)) return kBadModel;
    const nnm::HeadDesc& hd = m->head[h];
    if (hd.kind == nnm::Kind::none) return kNoModel;
    if (hd.uses_ctx && !obs_ok(*m)) return kSchemaMismatch;
    if (hd.kind == nnm::Kind::candidate && hd.action_hash != nnreg::kHeadActionHash[h]) return kSchemaMismatch;
    if (hd.uses_ctx && nnreg::kHeadModel[h] != nnreg::kCtxModel) return kSchemaMismatch;
    return kOk;
}
struct StaticTable {
    std::uint8_t s[kH];
};
constexpr StaticTable make_static() {
    StaticTable t{};
    for (int h = 0; h < kH; ++h) t.s[h] = static_status(h);
    return t;
}
constexpr StaticTable kStatic = make_static();

// ---------------------------------------------------------------- per-game / per-turn state (all zero-initialised)
struct Ctx {
    std::uint32_t turn;     // nnb::g_turn of the state below
    std::uint32_t round;    // round of the state below (second invalidation key)
    std::uint32_t champion; // champion handle (0 in the draft)
    std::uint8_t state;     // 0 not computed this turn, 1 ready, 2 failed this turn
    std::uint8_t reason;    // failure reason when state == 2
    std::uint8_t valid;     // turn/round below are meaningful
    std::uint16_t value_ready;
    std::uint32_t calls;    // decisions scored this turn (PRNG stream index)
    std::uint32_t records;  // training records written this turn
    float h[nnm::kMaxCtx];
    float values[kH][nnm::kMaxOut];
};
Ctx g_ctx;
nnobs::RawTurn g_raw;
float g_x[nnobs::kObsDim];
nnm::Scratch g_scratch;
nnm::SegState g_seg[kModelSlots][1 + kH]; // [model][0 = encoder, 1 + head]
std::uint8_t g_model_bad[kModelSlots];
std::uint8_t g_last[kH];
struct Token {
    std::uint32_t turn, round;
    int head; // -1 none
    std::uint8_t valid;
    std::uint64_t start; // fuel at admission: feature building is charged to the head too
} g_token;
bool g_started, g_selftest_done;
std::uint32_t g_last_tel_round;

// Refresh the per-turn state when the turn serial or the round changed (explicit invalidation at begin_turn()).
void touch_turn() {
    const std::uint32_t r = nnb::round_now();
    if (g_ctx.valid && g_ctx.turn == nnb::g_turn && g_ctx.round == r) return;
    g_ctx.valid = 1;
    g_ctx.turn = nnb::g_turn;
    g_ctx.round = r;
    g_ctx.champion = nnb::champion_now();
    g_ctx.state = 0;
    g_ctx.reason = 0;
    g_ctx.value_ready = 0;
    g_ctx.calls = 0;
    g_ctx.records = 0;
}

constexpr std::uint64_t ctx_cost() { return nnreg::kCaptureWorst + nnreg::kObsEncodeWorst + nnreg::kEncoderWorst; }

std::uint64_t decide_cost(int h, int K, int F) {
    std::uint64_t c = nnreg::kHeadFixed[h] + static_cast<std::uint64_t>(K) * nnreg::kHeadPerCand[h];
    if constexpr (nncfg::kTraining)
        c += nnreg::kLogFixed + nnreg::kLogPerByte * static_cast<std::uint64_t>(nnlog::decision_bytes(K, F));
    return c;
}

// Fuel check without telemetry counters (verification, context).
bool fits(int h, std::uint64_t cost) {
    const std::uint64_t left = nnb::fuel_left();
    return left >= cost + nnreg::kTailReserve + nnreg::kTeacherReserve[h] &&
           nnb::g_used + cost <= nnreg::kTurnAllowance;
}

// Verify the weight segments `h` needs (encoder if it reads the context, plus its own). 1 ok, 0 pending, 2 bad.
int verify_for(int mi, int h, bool use_turn_budget) {
    const nnm::ModelDesc& m = *nnreg::kModels[mi];
    const bool ctx = m.head[h].uses_ctx;
    for (int pass = 0; pass < 2; ++pass) {
        const int si = pass == 0 ? 0 : 1 + h;
        if (pass == 0 && !ctx) continue;
        const nnm::Seg& seg = pass == 0 ? m.enc : m.head[h].seg;
        nnm::SegState& st = g_seg[mi][si];
        for (int chunk = 0; chunk < 64 && st.state == 0; ++chunk) {
            const std::uint64_t cost = nnreg::kVerifyPerFloat * nnreg::kVerifyChunk + 200;
            if (use_turn_budget ? !fits(h, cost) : nnb::fuel_left() < cost + 2 * nnreg::kTailReserve) return 0;
            nnm::verify_step(m.blob, seg, st, nnreg::kVerifyChunk);
        }
        if (st.state == 2) {
            g_model_bad[mi] = 1;
            return 2;
        }
        if (st.state == 0) return 0;
    }
    return 1;
}

// Shared context for this turn (capture -> encode -> encoder). Admission already done by the caller.
std::uint8_t ensure_context(const Bot& bot) {
    if (g_ctx.state == 1) return kOk;
    if (g_ctx.state == 2) return g_ctx.reason;
    g_ctx.state = 2;
    if (!nnobs::capture(bot, g_raw)) return g_ctx.reason = kCaptureFailed;
    nnobs::encode(g_raw, g_x);
    if (!nnrt::all_finite(g_x, nnobs::kObsDim)) return g_ctx.reason = kNaN;
    const nnm::ModelDesc& m = *nnreg::kModels[nnreg::kCtxModel];
    nnm::encode(m, g_x, g_ctx.h, g_scratch);
    if (!nnrt::all_finite(g_ctx.h, m.ctx)) return g_ctx.reason = kNaN;
    g_ctx.state = 1;
    if constexpr (nncfg::kTraining) {
        if (g_ctx.records < nnreg::kMaxRecordsPerTurn) {
            ++g_ctx.records;
            nnlog::enqueue_turn_context(nnobs::kObsSchemaHash, static_cast<std::int32_t>(g_ctx.round), g_ctx.champion,
                                      &g_raw, static_cast<std::uint32_t>(sizeof(g_raw)));
        } else {
            ++nnlog::g_dropped;
        }
    }
    return kOk;
}

// Common gate: model status, verification, budget (unless pre-admitted), context. `cost` excludes the context.
std::uint8_t prepare(const Bot& bot, int h, std::uint64_t cost, bool admitted, bool build_ctx) {
    if (kStatic.s[h] != kOk) return kStatic.s[h];
    const int mi = nnreg::kHeadModel[h];
    if (g_model_bad[mi]) return kBadModel;
    const nnm::HeadDesc& hd = nnreg::kModels[mi]->head[h];
    const int v = verify_for(mi, h, true);
    if (v == 2) return kBadModel;
    if (v == 0) return kModelPending;
    if (hd.uses_ctx && g_ctx.state == 2) return g_ctx.reason;
    if (!admitted) {
        const std::uint64_t total = cost + (hd.uses_ctx && g_ctx.state == 0 ? ctx_cost() : 0);
        if (!nnb::admit(static_cast<H>(h), total)) {
            if (hd.uses_ctx && g_ctx.state == 0) g_ctx.state = 2, g_ctx.reason = kEncoderSkipped;
            return kBudget;
        }
    }
    if (hd.uses_ctx && build_ctx) return ensure_context(bot);
    return kOk;
}

Result finish(int h, Result r) {
    g_last[h] = r.reason;
    nnb::count_fallback(static_cast<H>(h), r.neural);
    return r;
}

// ---------------------------------------------------------------- selftest (kSelfTest profiles only)
void print_hash(const char* model, const char* what, int id, const float* v, int n, int extra) {
    const std::uint64_t hsh = nnrt::fnv1a64_f32(nnrt::kFnvOffset, v, n, nullptr);
    std::printf("NNST %s %s %d %016llx %d\n", model, what, id, static_cast<unsigned long long>(hsh), extra);
}

void selftest() {
    for (int mi = 0; mi < kNumModels; ++mi) {
        const nnm::ModelDesc& m = *nnreg::kModels[mi];
        if (!nnm::desc_ok(m) || nnm::obs_dim(m) != nnobs::kObsDim) {
            std::printf("NNST %s skipped\n", m.name);
            continue;
        }
        for (int si = 0; si <= kH; ++si) {
            const nnm::Seg& seg = si == 0 ? m.enc : m.head[si - 1].seg;
            for (int c = 0; c < 4096 && nnm::verify_step(m.blob, seg, g_seg[mi][si], 4096) == 0; ++c) {
            }
        }
        std::printf("NNST %s verify %d\n", m.name, g_seg[mi][0].state);
        nnrt::SplitMix64 rng{0x5E1F7E57ull};
        float* x = g_x;
        const int S = m.self_dim, Ra = m.ally_rows, Da = m.ally_dim, Re = m.enemy_rows, De = m.enemy_dim;
        for (int i = 0; i < nnobs::kObsDim; ++i) x[i] = rng.uniform() * 2.0f - 1.0f;
        float* ally = x + S;
        float* amask = ally + Ra * Da;
        float* enemy = amask + Ra;
        float* emask = enemy + Re * De;
        for (int r = 0; r < Ra; ++r) {
            const bool ok = r % 3 != 1;
            amask[r] = ok ? 1.0f : 0.0f;
            if (!ok)
                for (int j = 0; j < Da; ++j) ally[r * Da + j] = 0.0f;
        }
        for (int r = 0; r < Re; ++r) {
            const bool ok = r % 2 == 0;
            emask[r] = ok ? 1.0f : 0.0f;
            if (!ok)
                for (int j = 0; j < De; ++j) enemy[r * De + j] = 0.0f;
        }
        float h[nnm::kMaxCtx];
        nnm::encode(m, x, h, g_scratch);
        print_hash(m.name, "enc", -1, h, m.ctx, 0);
        for (int hi = 0; hi < kH; ++hi) {
            const nnm::HeadDesc& hd = m.head[hi];
            if (hd.kind == nnm::Kind::none) continue;
            nnrt::SplitMix64 hr{0x5E1F7E57ull + 0x100ull * static_cast<std::uint64_t>(hi + 1)};
            static float feat[kMaxK * kMaxF];
            float prior[kMaxK], logit[kMaxK], y[nnm::kMaxOut];
            std::uint8_t legal[kMaxK];
            const float* hh = hd.uses_ctx ? h : nullptr;
            if (hd.kind == nnm::Kind::candidate) {
                for (int i = 0; i < kMaxK * hd.F; ++i) feat[i] = hr.uniform() * 2.0f - 1.0f;
                for (int k = 0; k < kMaxK; ++k) {
                    legal[k] = k % 5 != 3;
                    prior[k] = k == 0 ? 0.0f : -0.125f * static_cast<float>(k);
                }
                nnm::candidate_logits(m, hd, hh, 0, feat, kMaxK, legal, prior, logit);
                print_hash(m.name, "head", hi, logit, kMaxK, nnrt::masked_argmax(logit, legal, kMaxK));
            } else if (hd.kind == nnm::Kind::value) {
                nnm::value_out(m, hd, hh, y);
                print_hash(m.name, "value", hi, y, hd.n_out, hd.n_out);
            } else {
                for (int i = 0; i < hd.F; ++i) feat[i] = hr.uniform() * 2.0f - 1.0f;
                y[0] = nnm::leaf_out(m, hd, hh, 0, feat);
                print_hash(m.name, "leaf", hi, y, 1, 1);
            }
        }
    }
}

} // namespace

// ---------------------------------------------------------------- public API
bool admit(const Bot& bot, nncfg::H head, int K, std::uint32_t feature_cost) {
    const int h = static_cast<int>(head);
    if (nncfg::kMode[h] == Mode::off) return false;
    const std::uint64_t start = nnb::fuel_left();
    touch_turn();
    if (K <= 0 || K > kMaxK) {
        finish(h, fallback(K == 0 ? kEmpty : kBadInput));
        return false;
    }
    const int F = kStatic.s[h] == kOk ? nnreg::kModels[nnreg::kHeadModel[h]]->head[h].F : kMaxF;
    const std::uint8_t r = prepare(bot, h, decide_cost(h, K, F) + feature_cost, false, false);
    if (r != kOk) {
        nnb::charge(head, start - nnb::fuel_left());
        finish(h, fallback(r));
        return false;
    }
    g_token = Token{g_ctx.turn, g_ctx.round, h, 1, start};
    return true;
}

Result decide(const Bot& bot, Decision& d) {
    const int h = static_cast<int>(d.head);
    if (h < 0 || h >= kH) return fallback(kBadInput);
    if (nncfg::kMode[h] == Mode::off) return fallback(kOff);
    touch_turn();
    const bool admitted = g_token.valid && g_token.head == h && g_token.turn == g_ctx.turn && g_token.round == g_ctx.round;
    g_token.valid = 0;
    // O(1) structural checks first (no fuel query).
    if (d.K == 0) return finish(h, fallback(kEmpty));
    if (d.K < 0 || d.K > kMaxK || d.F <= 0 || d.F > kMaxF) return finish(h, fallback(kBadInput));
    if (!d.legal[0]) return finish(h, fallback(kTeacherIllegal));
    if (kStatic.s[h] != kOk) return finish(h, fallback(kStatic.s[h]));
    const nnm::ModelDesc& m = *nnreg::kModels[nnreg::kHeadModel[h]];
    const nnm::HeadDesc& hd = m.head[h];
    if (hd.kind != nnm::Kind::candidate || d.F != hd.F) return finish(h, fallback(kSchemaMismatch));
    if (hd.n_ctx ? d.context >= hd.n_ctx : d.context != 0) return finish(h, fallback(kBadInput));
    const int K = d.K, F = d.F;
    // Charges everything from admission (feature building included) or from here to the end of the decision.
    nnb::Meter meter(d.head);
    if (admitted) meter.start = g_token.start;
    const std::uint8_t pr = prepare(bot, h, decide_cost(h, K, F), admitted, true);
    if (pr != kOk) return finish(h, fallback(pr));

    // Inputs: finite features/priors, teacher margin.
    if (!nnrt::all_finite(d.feat, K * F)) return finish(h, fallback(kNaN));
    for (int k = 0; k < K; ++k) {
        if (!d.legal[k]) continue;
        if (!nnrt::is_finite(d.prior[k])) return finish(h, fallback(kNaN));
        if (d.prior[k] > d.prior[0]) return finish(h, fallback(kBadPrior));
    }
    float logit[kMaxK];
    nnm::candidate_logits(m, hd, hd.uses_ctx ? g_ctx.h : nullptr, d.context, d.feat, K, d.legal, d.prior, logit);
    for (int k = 0; k < K; ++k)
        if (d.legal[k] && !nnrt::is_finite(logit[k])) return finish(h, fallback(kNaN));

    const std::uint32_t call = g_ctx.calls++;
    const bool active = nncfg::kMode[h] == Mode::active;
    Result r{0, false, 0.0f, kShadow, -1};
    bool sampled = false;
    if constexpr (nncfg::kTraining) {
        if (active) {
            nnrt::SplitMix64 rng = nnrt::decision_stream(nncfg::kSeed, g_ctx.round, g_ctx.champion,
                                                         static_cast<std::uint32_t>(h), call);
            float lp = 0.0f;
            const int pick = nnrt::masked_sample(logit, d.legal, K, rng.uniform(), &lp);
            // net = the deployed (argmax) rule, logged beside the sampled behaviour choice for train/deploy divergence.
            r = Result{pick, true, lp, kOk, static_cast<std::int8_t>(nnrt::masked_argmax(logit, d.legal, K))};
            sampled = true;
        } else {
            r.net = static_cast<std::int8_t>(nnrt::masked_argmax(logit, d.legal, K));
        }
    } else {
        const int best = nnrt::masked_argmax(logit, d.legal, K);
        r.net = static_cast<std::int8_t>(best);
        if (active) r = Result{best, true, 0.0f, kOk, static_cast<std::int8_t>(best)};
    }
    if (r.choice < 0 || r.choice >= K || !d.legal[r.choice]) r = Result{0, false, 0.0f, kNaN, r.net}; // unreachable
    if constexpr (nncfg::kTraining) {
        if (g_ctx.records < nnreg::kMaxRecordsPerTurn) {
            ++g_ctx.records;
            nnlog::DecisionRec rec{nnobs::kObsSchemaHash,
                                   static_cast<std::int32_t>(g_ctx.round),
                                   g_ctx.champion,
                                   static_cast<std::uint16_t>(h),
                                   static_cast<std::uint16_t>(K),
                                   static_cast<std::uint16_t>(F),
                                   static_cast<std::int16_t>(r.choice),
                                   static_cast<std::uint8_t>(nncfg::kMode[h]),
                                   r.reason,
                                   d.context,
                                   static_cast<std::uint8_t>(sampled),
                                   r.logp,
                                   d.prior,
                                   d.legal,
                                   d.id,
                                   d.feat,
                                   hd.action_hash,
                                   static_cast<std::uint16_t>(call),
                                   r.net,
                                   logit};
            nnlog::enqueue_decision(rec);
        } else {
            ++nnlog::g_dropped;
        }
    }
    return finish(h, r);
}

float value(const Bot& bot, nncfg::H head, int output) {
    const int h = static_cast<int>(head);
    if (h < 0 || h >= kH || nncfg::kMode[h] == Mode::off) return 0.0f;
    touch_turn();
    if (kStatic.s[h] != kOk) return finish(h, fallback(kStatic.s[h])), 0.0f;
    const nnm::ModelDesc& m = *nnreg::kModels[nnreg::kHeadModel[h]];
    const nnm::HeadDesc& hd = m.head[h];
    if (hd.kind != nnm::Kind::value || output < 0 || output >= hd.n_out) return finish(h, fallback(kBadInput)), 0.0f;
    const bool active = nncfg::kMode[h] == Mode::active;
    if (g_ctx.value_ready & (1u << h)) return active ? g_ctx.values[h][output] : 0.0f;
    nnb::Meter meter(head);
    const std::uint8_t pr = prepare(bot, h, nnreg::kHeadFixed[h], false, true);
    if (pr != kOk) return finish(h, fallback(pr)), 0.0f;
    nnm::value_out(m, hd, hd.uses_ctx ? g_ctx.h : nullptr, g_ctx.values[h]);
    if (!nnrt::all_finite(g_ctx.values[h], hd.n_out)) return finish(h, fallback(kNaN)), 0.0f;
    g_ctx.value_ready = static_cast<std::uint16_t>(g_ctx.value_ready | (1u << h));
    finish(h, Result{0, active, 0.0f, active ? kOk : kShadow, -1});
    return active ? g_ctx.values[h][output] : 0.0f;
}

float leaf(const Bot& bot, const float* feat, int F, std::uint8_t context) {
    constexpr int h = static_cast<int>(H::ts_leaf);
    if constexpr (nncfg::kMode[h] == Mode::off) {
        (void)bot, (void)feat, (void)F, (void)context;
        return 0.0f;
    } else {
        touch_turn();
        if (kStatic.s[h] != kOk) return finish(h, fallback(kStatic.s[h])), 0.0f;
        const nnm::ModelDesc& m = *nnreg::kModels[nnreg::kHeadModel[h]];
        const nnm::HeadDesc& hd = m.head[h];
        if (hd.kind != nnm::Kind::leaf || F != hd.F || !feat) return finish(h, fallback(kSchemaMismatch)), 0.0f;
        if (hd.n_ctx ? context >= hd.n_ctx : context != 0) return finish(h, fallback(kBadInput)), 0.0f;
        nnb::Meter meter(H::ts_leaf);
        const std::uint8_t pr = prepare(bot, h, nnreg::kHeadFixed[h] + nnreg::kHeadPerCand[h], false, true);
        if (pr != kOk) return finish(h, fallback(pr)), 0.0f;
        if (!nnrt::all_finite(feat, F)) return finish(h, fallback(kNaN)), 0.0f;
        const float y = nnm::leaf_out(m, hd, hd.uses_ctx ? g_ctx.h : nullptr, context, feat);
        if (!nnrt::is_finite(y)) return finish(h, fallback(kNaN)), 0.0f;
        const bool active = nncfg::kMode[h] == Mode::active;
        finish(h, Result{0, active, 0.0f, active ? kOk : kShadow, -1});
        return active ? y : 0.0f;
    }
}

void turn_start() {
    touch_turn();
    if constexpr (nncfg::kSelfTest) {
        if (!g_selftest_done) {
            g_selftest_done = true;
            selftest();
        }
    }
    if constexpr (nncfg::kTraining) {
        const std::uint64_t ck = kNumModels > 0 && nnreg::kCtxModel >= 0 ? nnreg::kModels[nnreg::kCtxModel]->checksum : 0;
        const std::uint16_t flags = static_cast<std::uint16_t>(1u | (nncfg::kFuelCredit ? 2u : 0u));
        if (!g_started) {
            g_started = true;
            nnlog::enqueue_episode(nnobs::kObsSchemaHash, static_cast<std::int32_t>(g_ctx.round), g_ctx.champion,
                                 nnlog::kEpisodeStart, flags, nncfg::kSeed, ck, nnreg::kProfileHash);
        } else if (g_ctx.round % 100 == 0) {
            nnlog::enqueue_episode(nnobs::kObsSchemaHash, static_cast<std::int32_t>(g_ctx.round), g_ctx.champion,
                                 nnlog::kEpisodeHeartbeat, flags, nncfg::kSeed, ck, nnreg::kProfileHash);
        }
    }
    if constexpr (nncfg::kTelemetry) {
        if (g_ctx.round / 100 != g_last_tel_round / 100) {
            g_last_tel_round = g_ctx.round;
            nnb::print_telemetry(g_ctx.round);
        }
    }
}

void idle() {
    // Training records are queued during the turn and written here, at the very end of play_turn, only while the
    // leftover fuel exceeds a reserve: logging never takes fuel the teacher could have used this turn. Records still
    // queued roll over to the next idle() (bounded queue; overflow counts as dropped and is reported in markers).
    if constexpr (nncfg::kTraining) {
        constexpr std::uint64_t kReserve = 4000;
        while (!nnlog::queue_empty()) {
            const std::uint64_t need = kReserve + 64 + 12 * static_cast<std::uint64_t>(nnlog::next_bytes());
            if (nnb::fuel_left() < need) break;
            nnlog::flush_one();
        }
    }
}

void warmup() {
    for (int mi = 0; mi < kNumModels; ++mi) {
        if (g_model_bad[mi]) continue;
        for (int h = 0; h < kH; ++h) {
            if (nnreg::kHeadModel[h] != mi || kStatic.s[h] != kOk) continue;
            if (verify_for(mi, h, false) == 0) return; // out of fuel: continue in later calls
        }
    }
}

std::uint8_t last_reason(nncfg::H head) { return g_last[static_cast<int>(head)]; }

} // namespace nnh
#endif // NN_ANY_HEAD
