// nn_model.h (agent B) - compact model description and the pure forward pass of the shared encoder and heads.
// No SDK. A model is one constexpr f32 blob (python/nfs/export.py writes nn_weights_<model>.h) plus a ModelDesc
// holding dimensions and offsets into it. Layout and order are specified in agents/B/REPORT.md ("Model format") and
// implemented identically by python/nfs/export.py (layout()) and python/nfs/models (PolicyNet).
//
// Observation layout (CONTRACTS 3.3): x = [self_global (S) | ally rows (Ra x Da) | ally mask (Ra) |
//                                          enemy rows (Re x De) | enemy mask (Re)], mask valid iff > 0.5.
// Encoder: g = act(x_sg @ G1 + b); a_r = act(ally_r @ A1 + b), e_r = act(enemy_r @ E1 + b) for valid rows only;
//          h = act([g, mean(a), max(a), mean(e), max(e)] @ C1 + b)                      (h: ctx values in [-1, 1])
// Candidate head: u = b1 + h @ Wh + emb[context]; r_k = act(u + f_k @ Wf) @ w2 + b2; logit_k = prior_k + R*act(r_k/R)
// Value head:     y = act(b1 + h @ Wh) @ W2 + b2            (n_out raw outputs)
// Leaf head:      like a candidate head with one candidate and no prior: R * act(r / R)
#pragma once

#include <cstdint>

#include "nn_rt.h"

namespace nnm {

inline constexpr std::uint32_t kArchVersion = 1;
inline constexpr int kHeads = 13; // == nncfg::H::count (checked in nn_head.cpp)
inline constexpr int kMaxHidden = 64, kMaxCtx = 64, kMaxEntity = 32, kMaxRows = 32, kMaxEntityDim = 64,
                     kMaxSelfDim = 256, kMaxOut = 16, kMaxF = 24, kMaxCtxCodes = 16;
inline constexpr std::uint32_t kNone = 0xFFFFFFFFu;

enum class Status : std::uint8_t { untrained = 0, teacher_initialized = 1, trained = 2, validated = 3 };
enum class Kind : std::uint8_t { none = 0, candidate = 1, value = 2, leaf = 3 };

struct Seg {
    std::uint32_t begin, end; // [begin, end) in floats
    std::uint64_t checksum;   // fnv1a64 over the little-endian bytes of blob[begin, end)
};

// y = b + x @ W, W row-major [in][out] at blob offset w, bias at offset b.
struct Lin {
    std::uint32_t w, b;
    std::uint16_t in, out;
};

struct HeadDesc {
    Kind kind;
    std::uint8_t uses_ctx; // reads the shared context h
    std::uint16_t F;       // candidate / leaf feature width (0 for value heads)
    std::uint16_t hidden;
    std::uint16_t n_ctx;   // call-site context codes (embedding rows), 0 = none
    std::uint16_t n_out;   // 1 for candidate / leaf heads
    float R;               // residual bound (candidate / leaf)
    std::uint32_t wh;      // [ctx][hidden] or kNone
    std::uint32_t wf;      // [F][hidden] or kNone
    std::uint32_t emb;     // [n_ctx][hidden] or kNone
    std::uint32_t b1;      // [hidden]
    std::uint32_t w2;      // [hidden][n_out]
    std::uint32_t b2;      // [n_out]
    std::uint32_t action_hash; // schema hash of this head's candidate features (0 = value head / unspecified)
    Seg seg;
};

struct ModelDesc {
    const char* name;
    std::uint32_t arch_version;
    Status status;
    std::uint32_t obs_schema_hash;
    std::uint32_t action_schema_hash;
    std::uint16_t self_dim, ally_rows, ally_dim, enemy_rows, enemy_dim;
    std::uint16_t g_hidden, e_hidden, ctx;
    Lin g1, a1, e1, c1;
    Seg enc;
    HeadDesc head[kHeads];
    std::uint32_t n_params;
    std::uint64_t checksum; // whole blob
    const float* blob;
};

inline constexpr int obs_dim(const ModelDesc& m) {
    return m.self_dim + m.ally_rows * m.ally_dim + m.ally_rows + m.enemy_rows * m.enemy_dim + m.enemy_rows;
}

// Structural validity (bounds and offsets); evaluated at compile time for installed models.
inline constexpr bool lin_ok(const Lin& l, std::uint32_t n) {
    return l.w != kNone && l.b != kNone && l.w + std::uint32_t(l.in) * l.out <= n && l.b + l.out <= n;
}
inline constexpr bool head_ok(const ModelDesc& m, const HeadDesc& h) {
    if (h.kind == Kind::none) return true;
    const std::uint32_t n = m.n_params;
    if (h.hidden == 0 || h.hidden > kMaxHidden || h.n_out == 0 || h.n_out > kMaxOut || h.F > kMaxF ||
        h.n_ctx > kMaxCtxCodes)
        return false;
    if (h.kind != Kind::value && (h.n_out != 1 || h.F == 0 || !(h.R > 0.0f))) return false;
    if (h.uses_ctx ? (h.wh == kNone || h.wh + std::uint32_t(m.ctx) * h.hidden > n) : h.wh != kNone) return false;
    if (h.F ? (h.wf == kNone || h.wf + std::uint32_t(h.F) * h.hidden > n) : h.wf != kNone) return false;
    if (h.n_ctx ? (h.emb == kNone || h.emb + std::uint32_t(h.n_ctx) * h.hidden > n) : h.emb != kNone) return false;
    if (h.b1 == kNone || h.b1 + h.hidden > n || h.w2 == kNone || h.w2 + std::uint32_t(h.hidden) * h.n_out > n ||
        h.b2 == kNone || h.b2 + h.n_out > n)
        return false;
    return h.seg.begin <= h.seg.end && h.seg.end <= n;
}
inline constexpr bool desc_ok(const ModelDesc& m) {
    if (m.arch_version != kArchVersion || m.blob == nullptr || m.n_params == 0) return false;
    if (m.self_dim == 0 || m.self_dim > kMaxSelfDim || m.ally_rows > kMaxRows || m.enemy_rows > kMaxRows ||
        m.ally_dim > kMaxEntityDim || m.enemy_dim > kMaxEntityDim || m.g_hidden == 0 || m.g_hidden > kMaxHidden ||
        m.e_hidden == 0 || m.e_hidden > kMaxEntity || m.ctx == 0 || m.ctx > kMaxCtx)
        return false;
    const std::uint32_t n = m.n_params;
    if (!lin_ok(m.g1, n) || !lin_ok(m.a1, n) || !lin_ok(m.e1, n) || !lin_ok(m.c1, n)) return false;
    if (m.g1.in != m.self_dim || m.g1.out != m.g_hidden || m.a1.in != m.ally_dim || m.a1.out != m.e_hidden ||
        m.e1.in != m.enemy_dim || m.e1.out != m.e_hidden || m.c1.in != m.g_hidden + 4 * m.e_hidden ||
        m.c1.out != m.ctx)
        return false;
    if (!(m.enc.begin <= m.enc.end && m.enc.end <= n)) return false;
    for (int i = 0; i < kHeads; ++i)
        if (!head_ok(m, m.head[i])) return false;
    return true;
}

// ---------------------------------------------------------------- forward pass
struct Scratch {
    float g[kMaxHidden];
    float ent[kMaxRows * kMaxEntity];
    float cat[kMaxHidden + 4 * kMaxEntity];
    std::uint8_t mask[kMaxRows];
};

// Embed valid rows of one entity block and pool them into mean (E) and max (E).
inline void entity_pool(const ModelDesc& m, const Lin& l, const float* rows, const float* maskf, int R, int D,
                        Scratch& s, float* mean, float* mx) {
    const float* W = m.blob + l.w;
    const float* b = m.blob + l.b;
    const int E = l.out;
    for (int r = 0; r < R; ++r) {
        s.mask[r] = maskf[r] > 0.5f ? 1 : 0;
        if (!s.mask[r]) continue;
        float* e = s.ent + r * E;
        nnrt::dense(rows + r * D, D, W, b, E, e);
        nnrt::act_n(e, E);
    }
    nnrt::pool_mean_max(s.ent, s.mask, R, E, mean, mx);
}

// Shared encoder: x (obs_dim floats) -> h (ctx floats).
inline void encode(const ModelDesc& m, const float* x, float* h, Scratch& s) {
    const int S = m.self_dim, Ra = m.ally_rows, Da = m.ally_dim, Re = m.enemy_rows, De = m.enemy_dim;
    const int G = m.g_hidden, E = m.e_hidden;
    const float* ally = x + S;
    const float* ally_mask = ally + Ra * Da;
    const float* enemy = ally_mask + Ra;
    const float* enemy_mask = enemy + Re * De;
    nnrt::dense(x, S, m.blob + m.g1.w, m.blob + m.g1.b, G, s.cat);
    nnrt::act_n(s.cat, G);
    entity_pool(m, m.a1, ally, ally_mask, Ra, Da, s, s.cat + G, s.cat + G + E);
    entity_pool(m, m.e1, enemy, enemy_mask, Re, De, s, s.cat + G + 2 * E, s.cat + G + 3 * E);
    nnrt::dense(s.cat, G + 4 * E, m.blob + m.c1.w, m.blob + m.c1.b, m.ctx, h);
    nnrt::act_n(h, m.ctx);
}

// Per-decision part of a head shared by all its candidates: u = b1 + h @ Wh + emb[context].
inline void head_pre(const ModelDesc& m, const HeadDesc& hd, const float* h, int context, float* u) {
    const int H = hd.hidden;
    for (int o = 0; o < H; ++o) u[o] = m.blob[hd.b1 + o];
    if (hd.uses_ctx) nnrt::dense_acc(h, m.ctx, m.blob + hd.wh, H, u);
    if (hd.n_ctx) {
        const float* e = m.blob + hd.emb + context * H;
        for (int o = 0; o < H; ++o) u[o] = u[o] + e[o];
    }
}

// Raw residual of one candidate: act(u + f @ Wf) @ w2 + b2.
inline float head_residual(const ModelDesc& m, const HeadDesc& hd, const float* u, const float* f) {
    float z[kMaxHidden];
    const int H = hd.hidden;
    for (int o = 0; o < H; ++o) z[o] = u[o];
    nnrt::dense_acc(f, hd.F, m.blob + hd.wf, H, z);
    nnrt::act_n(z, H);
    return nnrt::dot(z, m.blob + hd.w2, H, m.blob[hd.b2]);
}

// Candidate logits for K candidates (feat row-major K x F); illegal entries are -inf and are not evaluated.
inline void candidate_logits(const ModelDesc& m, const HeadDesc& hd, const float* h, int context, const float* feat,
                             int K, const std::uint8_t* legal, const float* prior, float* logit) {
    float u[kMaxHidden];
    head_pre(m, hd, h, context, u);
    for (int k = 0; k < K; ++k) {
        if (!legal[k]) {
            logit[k] = nnrt::kNegInf;
            continue;
        }
        const float r = head_residual(m, hd, u, feat + k * hd.F);
        logit[k] = prior[k] + nnrt::bounded(r, hd.R);
    }
}

// Value-kind head: n_out raw outputs.
inline void value_out(const ModelDesc& m, const HeadDesc& hd, const float* h, float* y) {
    float u[kMaxHidden];
    head_pre(m, hd, h, 0, u);
    nnrt::act_n(u, hd.hidden);
    nnrt::dense(u, hd.hidden, m.blob + hd.w2, m.blob + hd.b2, hd.n_out, y);
}

// Leaf head: bounded residual R * act(r / R) for one feature vector.
inline float leaf_out(const ModelDesc& m, const HeadDesc& hd, const float* h, int context, const float* f) {
    float u[kMaxHidden];
    head_pre(m, hd, h, context, u);
    return nnrt::bounded(head_residual(m, hd, u, f), hd.R);
}

// ---------------------------------------------------------------- resumable segment verification
// state: 0 = not started / in progress, 1 = verified, 2 = bad (checksum mismatch or non-finite value).
struct SegState {
    std::uint32_t pos;
    std::uint8_t state;
    std::uint8_t started;
    std::uint8_t finite_bad;
    std::uint64_t hash;
};

// Advance verification by at most max_floats; returns the resulting state.
inline int verify_step(const float* blob, const Seg& seg, SegState& st, std::uint32_t max_floats) {
    if (st.state) return st.state;
    if (!st.started) st.started = 1, st.pos = seg.begin, st.hash = nnrt::kFnvOffset, st.finite_bad = 0;
    const std::uint32_t left = seg.end - st.pos;
    const std::uint32_t n = left < max_floats ? left : max_floats;
    bool finite = true;
    st.hash = nnrt::fnv1a64_f32(st.hash, blob + st.pos, static_cast<int>(n), &finite);
    if (!finite) st.finite_bad = 1;
    st.pos += n;
    if (st.pos >= seg.end) st.state = (st.hash == seg.checksum && !st.finite_bad) ? 1 : 2;
    return st.state;
}

} // namespace nnm
