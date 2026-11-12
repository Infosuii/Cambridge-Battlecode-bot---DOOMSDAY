// Neural bot forward pass (agent2/lab/nn_model.py Net, weights from nn_export.py in nn_weights.h). Input: the int16
// features of nnrec.cpp. Output: logits per head (pointer heads over present entities, absent ones at -1e9).
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>
#include "nn_weights.h"
#if defined(__wasm_simd128__) && defined(A2_NN_FAST) && A2_NN_FAST
#include <wasm_simd128.h>
#endif

#ifndef NNW_HAS_NTYPE
// weights exported before per-block category counts: every category field is a champion type
namespace nnw {
inline constexpr int kg_ntype = kNT, ks_ntype = kNT, ka_ntype = kNT, ke_ntype = kNT, kc_ntype = kNT, kl_ntype = kNT;
}
#endif

namespace nn {
inline constexpr int kMaxEnt = 10, kE = nnw::kEnc;
// entity counts come from the exported weights (500-feature network: 5 allies, 8 enemies, 10 camps, 4 altars;
// version 3: 24 camps)
inline constexpr int kNA = nnw::ka_n, kNE = nnw::ke_n, kNC = nnw::kc_n, kNL = nnw::kl_n;
struct Out {
    float behaviour[8], step[9], cast[3], cast_pre[2], utility[6], shop[88];
    float option[5]; // RL-only residual head: 0 none, 1 hunt, 2 home, 3 regroup, 4 bank now
    float target[kNC + 1], attack[kNE + kNC + 1], cast_tgt[1 + kNA + kNE + kNC + 9];
};

#if defined(__wasm_simd128__) && defined(A2_NN_FAST) && A2_NN_FAST
// input-major copy of a weight matrix ([in][out]), made once per matrix on first use
inline const float* transposed(const float* W, int in, int out) {
#ifdef NNW_HAS_T
    if (const float* t = nnw::transposed_of(W)) return t; // exported input-major copy (no work at run time)
#endif
    struct E { const float* w; float* t; };
    static E cache[64];
    static int n = 0;
    for (int k = 0; k < n; ++k)
        if (cache[k].w == W) return cache[k].t;
    float* t = new float[static_cast<std::size_t>(in) * static_cast<std::size_t>(out)];
    for (int o = 0; o < out; ++o)
        for (int i = 0; i < in; ++i) t[i * out + o] = W[o * in + i];
    if (n < 64) cache[n++] = {W, t};
    return t;
}
#endif

inline void dense(const float* W, const float* b, const float* x, int in, int out, float* y, bool relu) {
#if defined(__wasm_simd128__) && defined(A2_NN_FAST) && A2_NN_FAST
    if (out % 4 == 0 && out <= 128) {
        // input-major (E120): each input is broadcast once and updates 4 outputs per multiply-add; inputs that are 0
        // (after a ReLU, or an unset one-hot) are skipped. Same sums as the row loop, in another order.
        const float* T = transposed(W, in, out);
        v128_t acc[32];
        for (int k = 0; k < out / 4; ++k) acc[k] = wasm_v128_load(b + 4 * k);
        for (int i = 0; i < in; ++i) {
            if (x[i] == 0.0f) continue;
            const v128_t xv = wasm_f32x4_splat(x[i]);
            const float* t = T + i * out;
            for (int k = 0; k < out / 4; ++k) acc[k] = wasm_f32x4_add(acc[k], wasm_f32x4_mul(wasm_v128_load(t + 4 * k), xv));
        }
        const v128_t zero = wasm_f32x4_splat(0.0f);
        for (int k = 0; k < out / 4; ++k) wasm_v128_store(y + 4 * k, relu ? wasm_f32x4_pmax(acc[k], zero) : acc[k]);
        return;
    }
    // 4-wide multiply-adds along each row (output counts that are not a multiple of 4)
    for (int o = 0; o < out; ++o) {
        const float* w = W + o * in;
        v128_t acc = wasm_f32x4_splat(0.0f);
        int i = 0;
        for (; i + 4 <= in; i += 4) acc = wasm_f32x4_add(acc, wasm_f32x4_mul(wasm_v128_load(w + i), wasm_v128_load(x + i)));
        float s = b[o] + wasm_f32x4_extract_lane(acc, 0) + wasm_f32x4_extract_lane(acc, 1) + wasm_f32x4_extract_lane(acc, 2) +
                  wasm_f32x4_extract_lane(acc, 3);
        for (; i < in; ++i) s += w[i] * x[i];
        y[o] = relu ? std::max(0.0f, s) : s;
    }
#else
    for (int o = 0; o < out; ++o) {
        const float* w = W + o * in;
        float s = b[o];
        for (int i = 0; i < in; ++i) s += w[i] * x[i];
        y[o] = relu ? std::max(0.0f, s) : s;
    }
#endif
}

// signed log1p of an int16 feature; A2_NN_FAST reads the exported tables (no log1p call), or, with older weights, memoises
// |v| < 4096 in a table (each entry computed on first use; 0 = not yet computed, and log1p(0) = 0 anyway)
#ifdef NNW_HAS_SLOG
inline float slogi(int v) {
    const int a = v < 0 ? -v : v;
    if (a < 4096) return v < 0 ? -nnw::kSlog[a] : nnw::kSlog[a];
    // E123: interpolated. Nearest-step values (off by up to 0.002) are multiplied by 1 / sd on the way in, and some large features barely vary: logits were off by up to 6.8.
    const int i = a >> 4;
    const float l0 = nnw::kSlog16[i], l = l0 + static_cast<float>(a & 15) * (nnw::kSlog16[i + 1] - l0) * 0.0625f;
    return v < 0 ? -l : l;
}
#endif
inline float slog(float v) {
#if defined(A2_NN_FAST) && A2_NN_FAST && defined(NNW_HAS_SLOG)
    return slogi(static_cast<int>(v));
#elif defined(A2_NN_FAST) && A2_NN_FAST
    static float tab[4096];
    const int a = static_cast<int>(v < 0 ? -v : v);
    float l;
    if (a < 4096) {
        if (tab[a] == 0.0f && a > 0) tab[a] = std::log1p(static_cast<float>(a));
        l = tab[a];
    } else {
        l = std::log1p(static_cast<float>(a));
    }
    return v < 0 ? -l : l;
#else
    return v < 0 ? -std::log1p(-v) : std::log1p(v);
#endif
}

// one entity block: prep (signed log, standardise, one-hot category: champion type, or the ladder map id) + encoder
// layers -> emb [n][kE]
template <int N, int W, int NKEEP, int TYPEF, int NTYPE, int LAYERS>
inline void encode(const std::int16_t* f, const int* keep, const float* mu, const float* sd, const float* const* Ws,
                   const float* const* bs, const int* ins, float emb[][kE], bool* present, bool always, int e0 = 0, int e1 = N) {
    for (int e = e0; e < e1; ++e) {
        const std::int16_t* r = f + e * W;
        present[e] = always || r[0] != 0;
        if (!present[e]) continue;
        float x[NKEEP + NTYPE + 1] = {};
        for (int i = 0; i < NKEEP; ++i) {
            const float v = static_cast<float>(r[keep[i]]);
            x[i] = (slog(v) - mu[i]) / sd[i];
        }
        int d = NKEEP;
        if (TYPEF >= 0) {
            const int t = std::clamp<int>(r[TYPEF], 0, NTYPE - 1);
            x[NKEEP + t] = 1.0f;
            d += NTYPE;
        }
        float h[2][kE];
        const float* in = x;
        for (int l = 0; l < LAYERS; ++l) {
            dense(Ws[l], bs[l], in, ins[l], kE, h[l & 1], true);
            in = h[l & 1];
        }
        std::copy(in, in + kE, emb[e]);
        (void)d;
    }
}


inline void pool(const float emb[][kE], const bool* present, int n, float* mean, float* mx) {
#if defined(__wasm_simd128__) && defined(A2_NN_FAST) && A2_NN_FAST
    if constexpr (kE % 4 == 0) {
        v128_t sm[kE / 4], mv[kE / 4];
        for (int k = 0; k < kE / 4; ++k) sm[k] = wasm_f32x4_splat(0.0f), mv[k] = wasm_f32x4_splat(-1e30f);
        int cnt = 0;
        for (int e = 0; e < n; ++e) {
            if (!present[e]) continue;
            ++cnt;
            for (int k = 0; k < kE / 4; ++k) {
                const v128_t v = wasm_v128_load(emb[e] + 4 * k);
                sm[k] = wasm_f32x4_add(sm[k], v), mv[k] = wasm_f32x4_pmax(mv[k], v);
            }
        }
        const v128_t inv = wasm_f32x4_splat(cnt ? 1.0f / static_cast<float>(cnt) : 0.0f), zero = wasm_f32x4_splat(0.0f);
        for (int k = 0; k < kE / 4; ++k) {
            wasm_v128_store(mean + 4 * k, wasm_f32x4_mul(sm[k], inv));
            wasm_v128_store(mx + 4 * k, cnt ? mv[k] : zero);
        }
        return;
    }
#endif
    int c = 0;
    for (int j = 0; j < kE; ++j) mean[j] = 0.0f, mx[j] = -1e30f;
    for (int e = 0; e < n; ++e) {
        if (!present[e]) continue;
        ++c;
        for (int j = 0; j < kE; ++j) mean[j] += emb[e][j], mx[j] = std::max(mx[j], emb[e][j]);
    }
    for (int j = 0; j < kE; ++j) {
        mean[j] = c ? mean[j] / static_cast<float>(c) : 0.0f;
        if (!c) mx[j] = 0.0f;
    }
}

// pointer logits: q = Wq z + bq; logit_i = <Wk emb_i + bk, q> / sqrt(kE) = (<emb_i, Wk^T q> + <bk, q>) / sqrt(kE)
inline void pointer(const float* z, const float* qW, const float* qb, const float* kW, const float* kb, const float* const* ents,
                    const bool* pres, int n, const float* extra, int nextra, float* out) {
    float q[kE], r[kE] = {};
    dense(qW, qb, z, nnw::kTrunk, kE, q, false);
    float c0 = 0.0f;
    for (int o = 0; o < kE; ++o) {
        c0 += kb[o] * q[o];
        for (int i = 0; i < kE; ++i) r[i] += kW[o * kE + i] * q[o];
    }
    const float sc = 1.0f / std::sqrt(static_cast<float>(kE));
    for (int i = 0; i < n + nextra; ++i) {
        if (i < n && !pres[i]) { out[i] = -1e9f; continue; }
        const float* e = i < n ? ents[i] : extra + (i - n) * kE;
        float s = c0;
        for (int j = 0; j < kE; ++j) s += e[j] * r[j];
        out[i] = s * sc;
    }
}

// head mask for forward(): the bot reads only behaviour (bank gate), target and option; the rest feed training only
inline constexpr unsigned kHBeh = 1, kHTarget = 2, kHOption = 4, kHMicro = 8, kHAll = 15;

#ifdef A2_NN_PROF
// stage fuel profile (A2_NN_PROF, E120): mean fuel per forward of each stage, printed every 200 forwards
inline void prof(int stage) {
    static std::uint64_t last = 0, sum[12] = {}, calls = 0;
    const std::uint64_t now = bc::fuel_remaining();
    if (stage > 0) sum[stage] += last - now;
    else ++calls;
    last = bc::fuel_remaining();
    if (stage == 10 && calls % 200 == 0) {
        auto m = [&](int s) { return static_cast<unsigned long long>(sum[s] / calls); };
        std::printf("NNPROF glob %llu self %llu ally %llu enemy %llu camp %llu altar %llu pool %llu trunk %llu beh+opt %llu target %llu\n",
                    m(1), m(2), m(3), m(4), m(5), m(6), m(7), m(8), m(9), m(10));
    }
}
#define NN_PROF(s) prof(s)
#else
#define NN_PROF(s)
#endif

template <class Tag = void>
inline void forward(const std::int16_t* f, Out& o, unsigned heads = kHAll, float* z_out = nullptr) {
    using namespace nnw;
    float eg[1][kE], es[1][kE], ea[kNA][kE], ee[kNE][kE], ec[kNC][kE], el[kNL][kE];
    bool pg[1], ps[1], pa[kNA], pe[kNE], pc[kNC], pl[kNL];
#define LAYER_ARRAYS(X)                                                                                                      const float* X##W[] = {k##X##_W0, k##X##_W1v};                                                                         const float* X##B[] = {k##X##_b0, k##X##_b1v};                                                                         const int X##I[] = {k##X##_in0, kE};
    LAYER_ARRAYS(g) LAYER_ARRAYS(s) LAYER_ARRAYS(a) LAYER_ARRAYS(e) LAYER_ARRAYS(c) LAYER_ARRAYS(l)
#undef LAYER_ARRAYS
    NN_PROF(0);
    encode<kg_n, kg_w, kg_nkeep, kg_type, kg_ntype, kg_layers>(f + kg_off, kg_keep, kg_mu, kg_sd, gW, gB, gI, eg, pg, true);
    NN_PROF(1);
    encode<ks_n, ks_w, ks_nkeep, ks_type, ks_ntype, ks_layers>(f + ks_off, ks_keep, ks_mu, ks_sd, sW, sB, sI, es, ps, true);
    NN_PROF(2);
    encode<ka_n, ka_w, ka_nkeep, ka_type, ka_ntype, ka_layers>(f + ka_off, ka_keep, ka_mu, ka_sd, aW, aB, aI, ea, pa, false);
    NN_PROF(3);
    encode<ke_n, ke_w, ke_nkeep, ke_type, ke_ntype, ke_layers>(f + ke_off, ke_keep, ke_mu, ke_sd, eW, eB, eI, ee, pe, false);
    NN_PROF(4);
    encode<kc_n, kc_w, kc_nkeep, kc_type, kc_ntype, kc_layers>(f + kc_off, kc_keep, kc_mu, kc_sd, cW, cB, cI, ec, pc, false);
    NN_PROF(5);
    encode<kl_n, kl_w, kl_nkeep, kl_type, kl_ntype, kl_layers>(f + kl_off, kl_keep, kl_mu, kl_sd, lW, lB, lI, el, pl, false);
    NN_PROF(6);
    float x[kTrunkIn];
    int d = 0;
    std::copy(eg[0], eg[0] + kE, x + d), d += kE;
    std::copy(es[0], es[0] + kE, x + d), d += kE;
    pool(ea, pa, kNA, x + d, x + d + kE), d += 2 * kE;
    pool(ee, pe, kNE, x + d, x + d + kE), d += 2 * kE;
    pool(ec, pc, kNC, x + d, x + d + kE), d += 2 * kE;
    pool(el, pl, kNL, x + d, x + d + kE), d += 2 * kE;
    NN_PROF(7);
    float h0[kTrunk], h1[kTrunk];
    dense(kT_W0, kT_b0, x, kTrunkIn, kTrunk, h0, true);
    dense(kT_W1, kT_b1, h0, kTrunk, kTrunk, h1, true);
#ifdef A2_NN_DBGX
    {
        // E123: intermediate values of the first A2_NN_DBGX forwards, to compare with PyTorch (nnd_check.py)
        static int shown = 0;
        if (shown++ < A2_NN_DBGX) {
            std::printf("NNX");
            for (int i = 0; i < kTrunkIn; ++i) std::printf(" %.4f", x[i]);
            std::printf("\nNNH");
            for (int i = 0; i < kTrunk; ++i) std::printf(" %.4f", h0[i]);
            for (int i = 0; i < kTrunk; ++i) std::printf(" %.4f", h1[i]);
            std::printf("\n");
        }
    }
#endif
    NN_PROF(8);
    const float* z = h1;
    if (z_out) std::copy(h1, h1 + kTrunk, z_out);
    if (heads & kHBeh) dense(kH_behaviour_W, kH_behaviour_b, z, kTrunk, 8, o.behaviour, false);
    if (heads & kHMicro) {
        dense(kH_step_W, kH_step_b, z, kTrunk, 9, o.step, false);
        dense(kH_cast_W, kH_cast_b, z, kTrunk, 3, o.cast, false);
        dense(kH_cast_pre_W, kH_cast_pre_b, z, kTrunk, 2, o.cast_pre, false);
        dense(kH_utility_W, kH_utility_b, z, kTrunk, 6, o.utility, false);
        dense(kH_shop_W, kH_shop_b, z, kTrunk, 88, o.shop, false);
    }
#ifdef NNW_HAS_OPTION
    if (heads & kHOption) dense(kH_option_W, kH_option_b, z, kTrunk, 5, o.option, false);
    else o.option[0] = 1e9f, o.option[1] = o.option[2] = o.option[3] = o.option[4] = 0.0f;
#else
    o.option[0] = 1e9f, o.option[1] = o.option[2] = o.option[3] = o.option[4] = 0.0f; // no option head: always "none"
#endif
    NN_PROF(9);
    if (heads & kHTarget) {
        const float* ents[kNC];
        for (int i = 0; i < kNC; ++i) ents[i] = ec[i];
        pointer(z, kP_target_qW, kP_target_qb, kP_target_kW, kP_target_kb, ents, pc, kNC, kP_target_E, 1, o.target);
    }
    NN_PROF(10);
    if (heads & kHMicro) {
        const float* ents[kNE + kNC];
        bool pr[kNE + kNC];
        for (int i = 0; i < kNE; ++i) ents[i] = ee[i], pr[i] = pe[i];
        for (int i = 0; i < kNC; ++i) ents[kNE + i] = ec[i], pr[kNE + i] = pc[i];
        pointer(z, kP_attack_qW, kP_attack_qb, kP_attack_kW, kP_attack_kb, ents, pr, kNE + kNC, kP_attack_E, 1, o.attack);
    }
    if (heads & kHMicro) {
        const float* ents[1 + kNA + kNE + kNC];
        bool pr[1 + kNA + kNE + kNC];
        ents[0] = es[0], pr[0] = true;
        for (int i = 0; i < kNA; ++i) ents[1 + i] = ea[i], pr[1 + i] = pa[i];
        for (int i = 0; i < kNE; ++i) ents[1 + kNA + i] = ee[i], pr[1 + kNA + i] = pe[i];
        for (int i = 0; i < kNC; ++i) ents[1 + kNA + kNE + i] = ec[i], pr[1 + kNA + kNE + i] = pc[i];
        pointer(z, kP_cast_tgt_qW, kP_cast_tgt_qb, kP_cast_tgt_kW, kP_cast_tgt_kb, ents, pr, 1 + kNA + kNE + kNC, kP_cast_tgt_E, 9,
                o.cast_tgt);
    }
}

template <int N>
inline int argmax(const float (&v)[N]) {
    return static_cast<int>(std::max_element(v, v + N) - v);
}

// Two-timescale decision (A2_NN_ZEVERY, E120): target logits from this turn's camp features and a kept trunk output z
inline void target_fresh(const std::int16_t* f, const float* z, Out& o) {
    using namespace nnw;
    float ec[kNC][kE];
    bool pc[kNC];
    const float* cW[] = {kc_W0, kc_W1v};
    const float* cB[] = {kc_b0, kc_b1v};
    const int cI[] = {kc_in0, kE};
    encode<kc_n, kc_w, kc_nkeep, kc_type, kc_ntype, kc_layers>(f + kc_off, kc_keep, kc_mu, kc_sd, cW, cB, cI, ec, pc, false);
    const float* ents[kNC];
    for (int i = 0; i < kNC; ++i) ents[i] = ec[i];
    pointer(z, kP_target_qW, kP_target_qb, kP_target_kW, kP_target_kb, ents, pc, kNC, kP_target_E, 1, o.target);
}

#if defined(A2_NN_Q16) && A2_NN_Q16
// E124: the deployed network in 16-bit fixed point. Fuel counts instructions and an instruction does the same work whatever its width, so i16x8 does 8 multiply-adds where f32x4 does 4.
// Inputs Q11 (clamped to +-7.8), weights Q14, q15mulr_sat + add_sat: encoder Q10, trunk layer 0 Q9, layer 1 Q8, q Q7, r Q6. nn_q16_check.py: same blend decision on 99.78% of recorded rows, logits off by 0.04 on average.
// Kept sums collect up to 1 unit of rounding per update: a camp or self sum is rebuilt every kQReset updates, trunk layer 0's when live_rebuild is called.
#ifndef A2_NN_EPSQ
#define A2_NN_EPSQ 0 // changes of a trunk input up to this many units (Q10) are left for later
#endif
static_assert(kE % 8 == 0 && nnw::kTrunk % 8 == 0, "A2_NN_Q16 needs multiples of 8");
inline constexpr int kQReset = 32;
template <int NKEEP>
struct CacheQ {
    v128_t acc[kE / 8];
    std::int16_t xq[NKEEP], raw[NKEEP];
    int upd = 0;
    bool ok = false;
};
using CampCache = CacheQ<nnw::kc_nkeep>;
struct Live {
    CacheQ<nnw::ks_nkeep> sc;
    std::int16_t eg[1][kE], es[1][kE], ea[kNA][kE], ee[kNE][kE], ec[kNC][kE], el[kNL][kE];
    bool pg[1], ps[1], pa[kNA], pe[kNE], pc[kNC], pl[kNL];
    std::int16_t x[nnw::kTrunkIn], acc0[nnw::kTrunk], r[kE];
    std::int32_t c0 = 0;
    int beh = -1;
    bool z_ok = false, x_ok = false;
    std::vector<CampCache> cache;
};
// value as Q11, no float-to-int checks (one SIMD instruction)
inline int qin(float v) {
    const int q = wasm_i32x4_extract_lane(wasm_i32x4_trunc_sat_f32x4(wasm_f32x4_splat(v * 2048.0f)), 0);
    return q > 16000 ? 16000 : q < -16000 ? -16000 : q;
}
template <int OUT>
inline void add_col16(v128_t* a, const short* t, const v128_t xv) {
#pragma clang loop unroll(full)
    for (int k = 0; k < OUT / 8; ++k) a[k] = wasm_i16x8_add_sat(a[k], wasm_i16x8_q15mulr_sat(wasm_v128_load(t + 8 * k), xv));
}
template <int OUT>
inline void dense16(const short* T, const short* b, const std::int16_t* x, int in, std::int16_t* y, bool relu) {
    v128_t a[OUT / 8];
#pragma clang loop unroll(full)
    for (int k = 0; k < OUT / 8; ++k) a[k] = b ? wasm_v128_load(b + 8 * k) : wasm_i16x8_splat(0);
    for (int i = 0; i < in; ++i, T += OUT) {
        if (x[i] == 0) continue;
        add_col16<OUT>(a, T, wasm_i16x8_splat(x[i]));
    }
    const v128_t zero = wasm_i16x8_splat(0);
#pragma clang loop unroll(full)
    for (int k = 0; k < OUT / 8; ++k) wasm_v128_store(y + 8 * k, relu ? wasm_i16x8_max(a[k], zero) : a[k]);
}
template <int N, int W, int NKEEP, int TYPEF, int NTYPE>
inline void encode16(const std::int16_t* f, const int* keep, const float* mu, const float* sd, const short* T, const short* b, std::int16_t emb[][kE], bool* present, bool always) {
    const v128_t zero = wasm_i16x8_splat(0);
    for (int e = 0; e < N; ++e) {
        const std::int16_t* r = f + e * W;
        present[e] = always || r[0] != 0;
        if (!present[e]) continue;
        v128_t a[kE / 8];
#pragma clang loop unroll(full)
        for (int k = 0; k < kE / 8; ++k) a[k] = wasm_v128_load(b + 8 * k);
        for (int i = 0; i < NKEEP; ++i) {
            const int q = qin((slogi(r[keep[i]]) - mu[i]) / sd[i]);
            if (q != 0) add_col16<kE>(a, T + i * kE, wasm_i16x8_splat(static_cast<short>(q)));
        }
        if constexpr (TYPEF >= 0) add_col16<kE>(a, T + (NKEEP + std::clamp<int>(r[TYPEF], 0, NTYPE - 1)) * kE, wasm_i16x8_splat(2048));
#pragma clang loop unroll(full)
        for (int k = 0; k < kE / 8; ++k) wasm_v128_store(emb[e] + 8 * k, wasm_i16x8_max(a[k], zero));
    }
}
inline void pool16(const std::int16_t emb[][kE], const bool* present, int n, std::int16_t* mean, std::int16_t* mx) {
    int cnt = 0;
    for (int e = 0; e < n; ++e) cnt += present[e];
    v128_t sm[kE / 8], mv[kE / 8];
#pragma clang loop unroll(full)
    for (int k = 0; k < kE / 8; ++k) sm[k] = wasm_i16x8_splat(0), mv[k] = wasm_i16x8_splat(0);
    if (cnt) {
        const v128_t inv = wasm_i16x8_splat(static_cast<short>(cnt == 1 ? 32767 : 32768 / cnt));
        for (int e = 0; e < n; ++e) {
            if (!present[e]) continue;
#pragma clang loop unroll(full)
            for (int k = 0; k < kE / 8; ++k) {
                const v128_t v = wasm_v128_load(emb[e] + 8 * k);
                sm[k] = wasm_i16x8_add_sat(sm[k], wasm_i16x8_q15mulr_sat(v, inv)), mv[k] = wasm_i16x8_max(mv[k], v);
            }
        }
    }
#pragma clang loop unroll(full)
    for (int k = 0; k < kE / 8; ++k) wasm_v128_store(mean + 8 * k, sm[k]), wasm_v128_store(mx + 8 * k, mv[k]);
}
// one kept encoder sum: only the inputs that changed
template <int NKEEP>
inline void kept_sum(CacheQ<NKEEP>& c, const std::int16_t* r, const int* keep, const float* mu, const float* sd, const short* T, const short* b, std::int16_t* out, const short* type_col) {
    v128_t a[kE / 8];
    if (!c.ok) {
        std::fill(c.xq, c.xq + NKEEP, static_cast<std::int16_t>(0));
        std::fill(c.raw, c.raw + NKEEP, static_cast<std::int16_t>(-32768));
        c.upd = 0;
    }
    if (!c.ok || c.upd >= kQReset) {
#pragma clang loop unroll(full)
        for (int k = 0; k < kE / 8; ++k) a[k] = wasm_v128_load(b + 8 * k);
        if (type_col) add_col16<kE>(a, type_col, wasm_i16x8_splat(2048));
        for (int i = 0; i < NKEEP; ++i)
            if (c.xq[i]) add_col16<kE>(a, T + i * kE, wasm_i16x8_splat(c.xq[i]));
        c.upd = 0, c.ok = true;
    } else {
#pragma clang loop unroll(full)
        for (int k = 0; k < kE / 8; ++k) a[k] = c.acc[k];
    }
    for (int i = 0; i < NKEEP; ++i) {
        const std::int16_t v = r[keep[i]];
        if (v == c.raw[i]) continue;
        const int q = qin((slogi(v) - mu[i]) / sd[i]), dq = q - c.xq[i];
        c.raw[i] = v;
        if (dq == 0) continue;
        add_col16<kE>(a, T + i * kE, wasm_i16x8_splat(static_cast<short>(dq)));
        c.xq[i] = static_cast<std::int16_t>(q);
    }
    ++c.upd;
    const v128_t zero = wasm_i16x8_splat(0);
#pragma clang loop unroll(full)
    for (int k = 0; k < kE / 8; ++k) {
        c.acc[k] = a[k];
        wasm_v128_store(out + 8 * k, wasm_i16x8_max(a[k], zero));
    }
}
inline void live_camps(const std::int16_t* f, Live& lv, std::size_t n_groups) {
    using namespace nnw;
    if (lv.cache.size() != n_groups) lv.cache.assign(n_groups, CampCache{});
    for (int e = 0; e < kNC; ++e) {
        const std::int16_t* r = f + kc_off + e * kc_w;
        lv.pc[e] = r[0] != 0;
        if (!lv.pc[e]) continue;
        kept_sum(lv.cache[static_cast<std::size_t>(r[1])], r, kc_keep, kc_mu, kc_sd, kc_W0_TQ, kc_b0Q, lv.ec[e], nullptr);
    }
}
inline void live_in(Live& lv, int d, int n, const std::int16_t* nx) {
    using namespace nnw;
    v128_t a[kTrunk / 8];
#pragma clang loop unroll(full)
    for (int k = 0; k < kTrunk / 8; ++k) a[k] = wasm_v128_load(lv.acc0 + 8 * k);
    const short* T = kT_W0_TQ + d * kTrunk;
    for (int i = 0; i < n; ++i, T += kTrunk) {
        const int dv = nx[i] - lv.x[d + i];
        if (dv <= A2_NN_EPSQ && dv >= -(A2_NN_EPSQ)) continue;
        add_col16<kTrunk>(a, T, wasm_i16x8_splat(static_cast<short>(dv)));
        lv.x[d + i] = nx[i];
    }
#pragma clang loop unroll(full)
    for (int k = 0; k < kTrunk / 8; ++k) wasm_v128_store(lv.acc0 + 8 * k, a[k]);
}
// rebuild trunk layer 0's kept sum from its inputs: the rounding it collected goes away (about 10k fuel, every so often)
inline void live_rebuild(Live& lv) {
    using namespace nnw;
    v128_t a[kTrunk / 8];
#pragma clang loop unroll(full)
    for (int k = 0; k < kTrunk / 8; ++k) a[k] = wasm_v128_load(kT_b0Q + 8 * k);
    const short* T = kT_W0_TQ;
    for (int i = 0; i < kTrunkIn; ++i, T += kTrunk)
        if (lv.x[i]) add_col16<kTrunk>(a, T, wasm_i16x8_splat(lv.x[i]));
#pragma clang loop unroll(full)
    for (int k = 0; k < kTrunk / 8; ++k) wasm_v128_store(lv.acc0 + 8 * k, a[k]);
}
// block b: 0 global, 1 self, 2 allies, 3 enemies, 4 camps (their embeddings come from live_camps), 5 altars
inline void live_block(const std::int16_t* f, Live& lv, int b) {
    using namespace nnw;
    if (!lv.x_ok) {
        std::fill(lv.x, lv.x + kTrunkIn, static_cast<std::int16_t>(0));
        std::copy(kT_b0Q, kT_b0Q + kTrunk, lv.acc0);
        lv.x_ok = true;
    }
    std::int16_t p[2 * kE];
    if (b == 0) {
        encode16<kg_n, kg_w, kg_nkeep, kg_type, kg_ntype>(f + kg_off, kg_keep, kg_mu, kg_sd, kg_W0_TQ, kg_b0Q, lv.eg, lv.pg, true);
        live_in(lv, 0, kE, lv.eg[0]);
    } else if (b == 1) {
        const std::int16_t* r = f + ks_off;
        kept_sum(lv.sc, r, ks_keep, ks_mu, ks_sd, ks_W0_TQ, ks_b0Q, lv.es[0], ks_W0_TQ + (ks_nkeep + std::clamp<int>(r[ks_type], 0, ks_ntype - 1)) * kE);
        lv.ps[0] = true;
        live_in(lv, kE, kE, lv.es[0]);
    } else if (b == 2) {
        encode16<ka_n, ka_w, ka_nkeep, ka_type, ka_ntype>(f + ka_off, ka_keep, ka_mu, ka_sd, ka_W0_TQ, ka_b0Q, lv.ea, lv.pa, false);
        pool16(lv.ea, lv.pa, kNA, p, p + kE);
        live_in(lv, 2 * kE, 2 * kE, p);
    } else if (b == 3) {
        encode16<ke_n, ke_w, ke_nkeep, ke_type, ke_ntype>(f + ke_off, ke_keep, ke_mu, ke_sd, ke_W0_TQ, ke_b0Q, lv.ee, lv.pe, false);
        pool16(lv.ee, lv.pe, kNE, p, p + kE);
        live_in(lv, 4 * kE, 2 * kE, p);
    } else if (b == 4) {
        pool16(lv.ec, lv.pc, kNC, p, p + kE);
        live_in(lv, 6 * kE, 2 * kE, p);
    } else {
        encode16<kl_n, kl_w, kl_nkeep, kl_type, kl_ntype>(f + kl_off, kl_keep, kl_mu, kl_sd, kl_W0_TQ, kl_b0Q, lv.el, lv.pl, false);
        pool16(lv.el, lv.pl, kNL, p, p + kE);
        live_in(lv, 8 * kE, 2 * kE, p);
    }
}
inline std::int32_t dot16(const short* a, const std::int16_t* b) {
    v128_t s = wasm_i32x4_splat(0);
#pragma clang loop unroll(full)
    for (int k = 0; k < kE / 8; ++k) s = wasm_i32x4_add(s, wasm_i32x4_dot_i16x8(wasm_v128_load(a + 8 * k), wasm_v128_load(b + 8 * k)));
    return wasm_i32x4_extract_lane(s, 0) + wasm_i32x4_extract_lane(s, 1) + wasm_i32x4_extract_lane(s, 2) + wasm_i32x4_extract_lane(s, 3);
}
inline void live_top(Live& lv) {
    using namespace nnw;
    std::int16_t h0[kTrunk], h1[kTrunk], q[kE];
    const v128_t zero = wasm_i16x8_splat(0);
#pragma clang loop unroll(full)
    for (int k = 0; k < kTrunk / 8; ++k) wasm_v128_store(h0 + 8 * k, wasm_i16x8_max(wasm_v128_load(lv.acc0 + 8 * k), zero));
    dense16<kTrunk>(kT_W1_TQ, kT_b1Q, h0, kTrunk, h1, true);
    dense16<kE>(kP_target_qW_TQ, kP_target_qbQ, h1, kTrunk, q, false);
    dense16<kE>(kP_target_kWQ, nullptr, q, kE, lv.r, false); // r = Wk^T q
    lv.c0 = dot16(kP_target_kbQ, q);                         // Q9 x Q7 = Q16
    lv.z_ok = true;
}
inline constexpr int kLiveStages = 7;                                // (the staged design is float only)
inline void live_stage(const std::int16_t*, Live&, int) {}
// target logits from the kept pointer vector and the camp embeddings in lv: Q10 x Q6 = Q16
inline void live_target(const Live& lv, Out& o) {
    const float sc = 1.0f / (65536.0f * std::sqrt(static_cast<float>(kE)));
    for (int i = 0; i < kNC; ++i) o.target[i] = lv.pc[i] ? static_cast<float>(dot16(lv.ec[i], lv.r) + lv.c0) * sc : -1e9f;
    o.target[kNC] = static_cast<float>(dot16(nnw::kP_target_EQ, lv.r) + lv.c0) * sc;
}
#elif defined(A2_NN_LIVE) && A2_NN_LIVE
// Real-fuel forward (A2_NN_LIVE, E121, the student's one-layer encoders): the same sums as forward() with compile-time
// sizes, so the accumulators are wasm locals (fuel counts instructions). A camp's embedding is kept per group and only
// the inputs that changed since the last decision are added in. The trunk's summary is kept as the target pointer's
// vector, so a turn short of fuel can score the camps alone.
static_assert(nnw::kc_layers == 1 && nnw::kg_layers == 1 && kE % 4 == 0 && nnw::kTrunk % 4 == 0, "A2_NN_LIVE needs the student");
struct CampCache {
    v128_t acc[kE / 4];
    float x[nnw::kc_nkeep];
    std::int16_t raw[nnw::kc_nkeep];
    bool ok = false;
};
#ifndef A2_NN_EPS
#define A2_NN_EPS 0.0f // E124: changes smaller than this in the kept sums are left for later (0: exact)
#endif
struct SelfCache {
    v128_t acc[kE / 4];
    float x[nnw::ks_nkeep];
    std::int16_t raw[nnw::ks_nkeep];
    bool ok = false;
};
struct Live {
    SelfCache sc;
    v128_t acc1[nnw::kTrunk / 4];
    bool acc1_ok = false;
    float eg[1][kE], es[1][kE], ea[kNA][kE], ee[kNE][kE], ec[kNC][kE], el[kNL][kE];
    bool pg[1], ps[1], pa[kNA], pe[kNE], pc[kNC], pl[kNL];
    float x[nnw::kTrunkIn], acc0[nnw::kTrunk], h0[nnw::kTrunk], h1[nnw::kTrunk], r[kE], c0 = 0.0f;
    int beh = -1, beh_next = -1;
    bool z_ok = false, x_ok = false;
    std::vector<CampCache> cache;
};
template <int OUT>
inline void add_col(v128_t* a, const float* t, const v128_t xv) {
#pragma clang loop unroll(full)
    for (int k = 0; k < OUT / 4; ++k) a[k] = wasm_f32x4_add(a[k], wasm_f32x4_mul(wasm_v128_load(t + 4 * k), xv));
}
template <int OUT>
inline void dense_t(const float* T, const float* b, const float* x, int in, float* y, bool relu) {
    v128_t a[OUT / 4];
#pragma clang loop unroll(full)
    for (int k = 0; k < OUT / 4; ++k) a[k] = wasm_v128_load(b + 4 * k);
    for (int i = 0; i < in; ++i, T += OUT) {
        if (x[i] == 0.0f) continue;
        add_col<OUT>(a, T, wasm_f32x4_splat(x[i]));
    }
    const v128_t zero = wasm_f32x4_splat(0.0f);
#pragma clang loop unroll(full)
    for (int k = 0; k < OUT / 4; ++k) wasm_v128_store(y + 4 * k, relu ? wasm_f32x4_pmax(a[k], zero) : a[k]);
}
// a block of a one-layer encoder: T is the input-major weights (kept inputs, then the category one-hot column)
template <int N, int W, int NKEEP, int TYPEF, int NTYPE>
inline void encode_t(const std::int16_t* f, const int* keep, const float* mu, const float* sd, const float* T, const float* b,
                     float emb[][kE], bool* present, bool always) {
    const v128_t zero = wasm_f32x4_splat(0.0f);
    for (int e = 0; e < N; ++e) {
        const std::int16_t* r = f + e * W;
        present[e] = always || r[0] != 0;
        if (!present[e]) continue;
        v128_t a[kE / 4];
#pragma clang loop unroll(full)
        for (int k = 0; k < kE / 4; ++k) a[k] = wasm_v128_load(b + 4 * k);
        for (int i = 0; i < NKEEP; ++i) {
            const float v = (slogi(r[keep[i]]) - mu[i]) / sd[i];
            if (v != 0.0f) add_col<kE>(a, T + i * kE, wasm_f32x4_splat(v));
        }
        if constexpr (TYPEF >= 0) add_col<kE>(a, T + (NKEEP + std::clamp<int>(r[TYPEF], 0, NTYPE - 1)) * kE, wasm_f32x4_splat(1.0f));
#pragma clang loop unroll(full)
        for (int k = 0; k < kE / 4; ++k) wasm_v128_store(emb[e] + 4 * k, wasm_f32x4_pmax(a[k], zero));
    }
}
// the camp block from this turn's features, per group: only inputs that changed since this group was last encoded
inline void live_camps(const std::int16_t* f, Live& lv, std::size_t n_groups) {
    using namespace nnw;
    if (lv.cache.size() != n_groups) lv.cache.assign(n_groups, CampCache{});
    const v128_t zero = wasm_f32x4_splat(0.0f);
    for (int e = 0; e < kNC; ++e) {
        const std::int16_t* r = f + kc_off + e * kc_w;
        lv.pc[e] = r[0] != 0;
        if (!lv.pc[e]) continue;
        auto& c = lv.cache[static_cast<std::size_t>(r[1])];
        v128_t a[kE / 4];
        if (!c.ok) {
#pragma clang loop unroll(full)
            for (int k = 0; k < kE / 4; ++k) a[k] = wasm_v128_load(kc_b0 + 4 * k);
            std::fill(c.x, c.x + kc_nkeep, 0.0f);
            std::fill(c.raw, c.raw + kc_nkeep, static_cast<std::int16_t>(-32768));
            c.ok = true;
        } else {
#pragma clang loop unroll(full)
            for (int k = 0; k < kE / 4; ++k) a[k] = c.acc[k];
        }
        for (int i = 0; i < kc_nkeep; ++i) {
            const std::int16_t v = r[kc_keep[i]];
            if (v == c.raw[i]) continue;
            const float nx = (slogi(v) - kc_mu[i]) / kc_sd[i], dx = nx - c.x[i];
            if (dx < A2_NN_EPS && dx > -A2_NN_EPS) continue;
            add_col<kE>(a, kc_W0_T + i * kE, wasm_f32x4_splat(dx));
            c.raw[i] = v, c.x[i] = nx;
        }
#pragma clang loop unroll(full)
        for (int k = 0; k < kE / 4; ++k) {
            c.acc[k] = a[k];
            wasm_v128_store(lv.ec[e] + 4 * k, wasm_f32x4_pmax(a[k], zero));
        }
    }
}
inline float dot_t(const float* a, const float* b) {
    v128_t s = wasm_f32x4_splat(0.0f);
#pragma clang loop unroll(full)
    for (int k = 0; k < kE / 4; ++k) s = wasm_f32x4_add(s, wasm_f32x4_mul(wasm_v128_load(a + 4 * k), wasm_v128_load(b + 4 * k)));
    return wasm_f32x4_extract_lane(s, 0) + wasm_f32x4_extract_lane(s, 1) + wasm_f32x4_extract_lane(s, 2) + wasm_f32x4_extract_lane(s, 3);
}
// target logits from the kept pointer vector and the camp embeddings in lv
inline void live_target(const Live& lv, Out& o) {
    const float sc = 1.0f / std::sqrt(static_cast<float>(kE));
    for (int i = 0; i < kNC; ++i) o.target[i] = lv.pc[i] ? (lv.c0 + dot_t(lv.ec[i], lv.r)) * sc : -1e9f;
    o.target[kNC] = (lv.c0 + dot_t(nnw::kP_target_E, lv.r)) * sc;
}
// The slow part of the network, in stages that may run on different turns, on the fuel v92 leaves at the end of its turn:
// 0 global + self + allies, 1 enemies + altars, 2 pooling + the first third of trunk layer 0's inputs, 3 the second third, 4 the rest,
// 5 trunk layer 1 and the bank head, 6 the pointer vector (bank gate and pointer vector published together, in the last stage).
// f: the features taken when this refresh started. Larger students (E123) take more stages' worth of fuel: the cuts keep each stage small enough to fit a turn.
inline constexpr int kLiveStages = 7;
#ifdef A2_NN_NNUE
// E123, NNUE-like: trunk layer 0 is W x + b; x has one part per block (global, self, allies mean + max, enemies, camps, altars) and W x + b is kept, so a block that changes costs only its own
// columns. Self and camps change every turn; the other blocks as the fuel allows (nnrec.cpp). live_top runs the rest of the network in full. The result is the plain network on the features as last refreshed.
inline void live_in(Live& lv, int d, int n, const float* nx) {
    using namespace nnw;
    v128_t a[kTrunk / 4];
#pragma clang loop unroll(full)
    for (int k = 0; k < kTrunk / 4; ++k) a[k] = wasm_v128_load(lv.acc0 + 4 * k);
    const float* T = kT_W0_T + d * kTrunk;
    for (int i = 0; i < n; ++i, T += kTrunk) {
        const float dv = nx[i] - lv.x[d + i];
        if (dv <= A2_NN_EPS && dv >= -A2_NN_EPS) continue;
        add_col<kTrunk>(a, T, wasm_f32x4_splat(dv));
        lv.x[d + i] = nx[i];
    }
#pragma clang loop unroll(full)
    for (int k = 0; k < kTrunk / 4; ++k) wasm_v128_store(lv.acc0 + 4 * k, a[k]);
}
// block b: 0 global, 1 self, 2 allies, 3 enemies, 4 camps (their embeddings come from live_camps), 5 altars
inline void live_block(const std::int16_t* f, Live& lv, int b) {
    using namespace nnw;
    if (!lv.x_ok) {
        std::fill(lv.x, lv.x + kTrunkIn, 0.0f);
        std::copy(kT_b0, kT_b0 + kTrunk, lv.acc0);
        lv.x_ok = true;
    }
    float p[2 * kE];
    if (b == 0) {
        encode_t<kg_n, kg_w, kg_nkeep, kg_type, kg_ntype>(f + kg_off, kg_keep, kg_mu, kg_sd, kg_W0_T, kg_b0, lv.eg, lv.pg, true);
        live_in(lv, 0, kE, lv.eg[0]);
    } else if (b == 1) {
        auto& c = lv.sc;
        const std::int16_t* r = f + ks_off;
        v128_t a[kE / 4];
        if (!c.ok) {
#pragma clang loop unroll(full)
            for (int k = 0; k < kE / 4; ++k) a[k] = wasm_v128_load(ks_b0 + 4 * k);
            std::fill(c.x, c.x + ks_nkeep, 0.0f);
            std::fill(c.raw, c.raw + ks_nkeep, static_cast<std::int16_t>(-32768));
            add_col<kE>(a, ks_W0_T + (ks_nkeep + std::clamp<int>(r[ks_type], 0, ks_ntype - 1)) * kE, wasm_f32x4_splat(1.0f));
            c.ok = true;
        } else {
#pragma clang loop unroll(full)
            for (int k = 0; k < kE / 4; ++k) a[k] = c.acc[k];
        }
        for (int i = 0; i < ks_nkeep; ++i) {
            const std::int16_t v = r[ks_keep[i]];
            if (v == c.raw[i]) continue;
            const float nx = (slogi(v) - ks_mu[i]) / ks_sd[i], dx = nx - c.x[i];
            if (dx < A2_NN_EPS && dx > -A2_NN_EPS) continue;
            add_col<kE>(a, ks_W0_T + i * kE, wasm_f32x4_splat(dx));
            c.raw[i] = v, c.x[i] = nx;
        }
        const v128_t zero = wasm_f32x4_splat(0.0f);
#pragma clang loop unroll(full)
        for (int k = 0; k < kE / 4; ++k) {
            c.acc[k] = a[k];
            wasm_v128_store(lv.es[0] + 4 * k, wasm_f32x4_pmax(a[k], zero));
        }
        lv.ps[0] = true;
        live_in(lv, kE, kE, lv.es[0]);
    } else if (b == 2) {
        encode_t<ka_n, ka_w, ka_nkeep, ka_type, ka_ntype>(f + ka_off, ka_keep, ka_mu, ka_sd, ka_W0_T, ka_b0, lv.ea, lv.pa, false);
        pool(lv.ea, lv.pa, kNA, p, p + kE);
        live_in(lv, 2 * kE, 2 * kE, p);
    } else if (b == 3) {
        encode_t<ke_n, ke_w, ke_nkeep, ke_type, ke_ntype>(f + ke_off, ke_keep, ke_mu, ke_sd, ke_W0_T, ke_b0, lv.ee, lv.pe, false);
        pool(lv.ee, lv.pe, kNE, p, p + kE);
        live_in(lv, 4 * kE, 2 * kE, p);
    } else if (b == 4) {
        pool(lv.ec, lv.pc, kNC, p, p + kE);
        live_in(lv, 6 * kE, 2 * kE, p);
    } else {
        encode_t<kl_n, kl_w, kl_nkeep, kl_type, kl_ntype>(f + kl_off, kl_keep, kl_mu, kl_sd, kl_W0_T, kl_b0, lv.el, lv.pl, false);
        pool(lv.el, lv.pl, kNL, p, p + kE);
        live_in(lv, 8 * kE, 2 * kE, p);
    }
}
inline void live_top(Live& lv) {
    using namespace nnw;
    float q[kE], h0n[kTrunk];
    const v128_t zero = wasm_f32x4_splat(0.0f);
#pragma clang loop unroll(full)
    for (int k = 0; k < kTrunk / 4; ++k) wasm_v128_store(h0n + 4 * k, wasm_f32x4_pmax(wasm_v128_load(lv.acc0 + 4 * k), zero));
    // trunk layer 1 is W1 h0 + b1, kept as well: only the units of layer 0 that changed cost anything
    v128_t a1[kTrunk / 4];
    if (!lv.acc1_ok) {
#pragma clang loop unroll(full)
        for (int k = 0; k < kTrunk / 4; ++k) a1[k] = wasm_v128_load(kT_b1 + 4 * k);
        std::fill(lv.h0, lv.h0 + kTrunk, 0.0f);
        lv.acc1_ok = true;
    } else {
#pragma clang loop unroll(full)
        for (int k = 0; k < kTrunk / 4; ++k) a1[k] = lv.acc1[k];
    }
    const float* T1 = kT_W1_T;
    for (int i = 0; i < kTrunk; ++i, T1 += kTrunk) {
        const float dv = h0n[i] - lv.h0[i];
        if (dv <= A2_NN_EPS && dv >= -A2_NN_EPS) continue;
        add_col<kTrunk>(a1, T1, wasm_f32x4_splat(dv));
        lv.h0[i] = h0n[i];
    }
#pragma clang loop unroll(full)
    for (int k = 0; k < kTrunk / 4; ++k) {
        lv.acc1[k] = a1[k];
        wasm_v128_store(lv.h1 + 4 * k, wasm_f32x4_pmax(a1[k], zero));
    }
    dense_t<kE>(kP_target_qW_T, kP_target_qb, lv.h1, kTrunk, q, false);
    static const float kNoBias[kE] = {};
    dense_t<kE>(kP_target_kW, kNoBias, q, kE, lv.r, false);
    lv.c0 = dot_t(kP_target_kb, q);
    lv.z_ok = true;
}
#endif
template <int OUT>
inline void acc_cols(const float* T, const float* x, int i0, int i1, float* acc) {
    v128_t a[OUT / 4];
#pragma clang loop unroll(full)
    for (int k = 0; k < OUT / 4; ++k) a[k] = wasm_v128_load(acc + 4 * k);
    T += i0 * OUT;
    for (int i = i0; i < i1; ++i, T += OUT) {
        if (x[i] == 0.0f) continue;
        add_col<OUT>(a, T, wasm_f32x4_splat(x[i]));
    }
#pragma clang loop unroll(full)
    for (int k = 0; k < OUT / 4; ++k) wasm_v128_store(acc + 4 * k, a[k]);
}
inline void live_stage(const std::int16_t* f, Live& lv, int s) {
    using namespace nnw;
    if (s == 0) {
        encode_t<kg_n, kg_w, kg_nkeep, kg_type, kg_ntype>(f + kg_off, kg_keep, kg_mu, kg_sd, kg_W0_T, kg_b0, lv.eg, lv.pg, true);
        encode_t<ks_n, ks_w, ks_nkeep, ks_type, ks_ntype>(f + ks_off, ks_keep, ks_mu, ks_sd, ks_W0_T, ks_b0, lv.es, lv.ps, true);
        encode_t<ka_n, ka_w, ka_nkeep, ka_type, ka_ntype>(f + ka_off, ka_keep, ka_mu, ka_sd, ka_W0_T, ka_b0, lv.ea, lv.pa, false);
    } else if (s == 1) {
        encode_t<ke_n, ke_w, ke_nkeep, ke_type, ke_ntype>(f + ke_off, ke_keep, ke_mu, ke_sd, ke_W0_T, ke_b0, lv.ee, lv.pe, false);
        encode_t<kl_n, kl_w, kl_nkeep, kl_type, kl_ntype>(f + kl_off, kl_keep, kl_mu, kl_sd, kl_W0_T, kl_b0, lv.el, lv.pl, false);
    } else if (s == 2) {
        int d = 0;
        std::copy(lv.eg[0], lv.eg[0] + kE, lv.x + d), d += kE;
        std::copy(lv.es[0], lv.es[0] + kE, lv.x + d), d += kE;
        pool(lv.ea, lv.pa, kNA, lv.x + d, lv.x + d + kE), d += 2 * kE;
        pool(lv.ee, lv.pe, kNE, lv.x + d, lv.x + d + kE), d += 2 * kE;
        pool(lv.ec, lv.pc, kNC, lv.x + d, lv.x + d + kE), d += 2 * kE;
        pool(lv.el, lv.pl, kNL, lv.x + d, lv.x + d + kE), d += 2 * kE;
        std::copy(kT_b0, kT_b0 + kTrunk, lv.acc0);
        acc_cols<kTrunk>(kT_W0_T, lv.x, 0, kTrunkIn / 3, lv.acc0);
    } else if (s == 3) {
        acc_cols<kTrunk>(kT_W0_T, lv.x, kTrunkIn / 3, 2 * kTrunkIn / 3, lv.acc0);
    } else if (s == 4) {
        acc_cols<kTrunk>(kT_W0_T, lv.x, 2 * kTrunkIn / 3, kTrunkIn, lv.acc0);
        for (int k = 0; k < kTrunk; ++k) lv.h0[k] = lv.acc0[k] > 0.0f ? lv.acc0[k] : 0.0f;
    } else if (s == 5) {
        float beh[8];
        dense_t<kTrunk>(kT_W1_T, kT_b1, lv.h0, kTrunk, lv.h1, true);
        dense_t<8>(kH_behaviour_W_T, kH_behaviour_b, lv.h1, kTrunk, beh, false);
        lv.beh_next = argmax(beh);
    } else {
        float q[kE];
        dense_t<kE>(kP_target_qW_T, kP_target_qb, lv.h1, kTrunk, q, false);
        // r = Wk^T q: rows of kW are per output of the key layer, which is what dense_t walks; no bias, no ReLU
        static const float kNoBias[kE] = {};
        dense_t<kE>(kP_target_kW, kNoBias, q, kE, lv.r, false);
        lv.c0 = dot_t(kP_target_kb, q);
        lv.beh = lv.beh_next;
        lv.z_ok = true;
    }
}
#endif

#if defined(A2_NN_PIPE) && A2_NN_PIPE
// Pipelined forward (A2_NN_PIPE, E120 fuel fit): forward() cut into stages that may run on different turns (the bot
// runs them at the end of its turns while the fuel left covers a stage plus a reserve); the intermediate buffers live in
// Pipe between turns. Stage 0 global + self + allies, 1 enemies + altars, 2 / 3 camps (first / second half), 4 pooling
// + trunk layer 0, 5 trunk layer 1 + the heads the bot reads (behaviour, option, target).
inline constexpr int kPipeStages = 6;
struct Pipe {
    float eg[1][kE], es[1][kE], ea[kNA][kE], ee[kNE][kE], ec[kNC][kE], el[kNL][kE];
    bool pg[1], ps[1], pa[kNA], pe[kNE], pc[kNC], pl[kNL];
    float x[nnw::kTrunkIn], h0[nnw::kTrunk], h1[nnw::kTrunk];
    Out o;
};
inline void pipe_stage(Pipe& p, const std::int16_t* f, int s) {
    using namespace nnw;
#define LAYER_ARRAYS(X)                                                                                                      const float* X##W[] = {k##X##_W0, k##X##_W1v};                                                                         const float* X##B[] = {k##X##_b0, k##X##_b1v};                                                                         const int X##I[] = {k##X##_in0, kE};
    LAYER_ARRAYS(g) LAYER_ARRAYS(s) LAYER_ARRAYS(a) LAYER_ARRAYS(e) LAYER_ARRAYS(c) LAYER_ARRAYS(l)
#undef LAYER_ARRAYS
    switch (s) {
    case 0:
        encode<kg_n, kg_w, kg_nkeep, kg_type, kg_ntype, kg_layers>(f + kg_off, kg_keep, kg_mu, kg_sd, gW, gB, gI, p.eg, p.pg, true);
        encode<ks_n, ks_w, ks_nkeep, ks_type, ks_ntype, ks_layers>(f + ks_off, ks_keep, ks_mu, ks_sd, sW, sB, sI, p.es, p.ps, true);
        encode<ka_n, ka_w, ka_nkeep, ka_type, ka_ntype, ka_layers>(f + ka_off, ka_keep, ka_mu, ka_sd, aW, aB, aI, p.ea, p.pa, false);
        break;
    case 1:
        encode<ke_n, ke_w, ke_nkeep, ke_type, ke_ntype, ke_layers>(f + ke_off, ke_keep, ke_mu, ke_sd, eW, eB, eI, p.ee, p.pe, false);
        encode<kl_n, kl_w, kl_nkeep, kl_type, kl_ntype, kl_layers>(f + kl_off, kl_keep, kl_mu, kl_sd, lW, lB, lI, p.el, p.pl, false);
        break;
    case 2:
        encode<kc_n, kc_w, kc_nkeep, kc_type, kc_ntype, kc_layers>(f + kc_off, kc_keep, kc_mu, kc_sd, cW, cB, cI, p.ec, p.pc, false, 0,
                                                                   kNC / 2);
        break;
    case 3:
        encode<kc_n, kc_w, kc_nkeep, kc_type, kc_ntype, kc_layers>(f + kc_off, kc_keep, kc_mu, kc_sd, cW, cB, cI, p.ec, p.pc, false,
                                                                   kNC / 2, kNC);
        break;
    case 4: {
        int d = 0;
        std::copy(p.eg[0], p.eg[0] + kE, p.x + d), d += kE;
        std::copy(p.es[0], p.es[0] + kE, p.x + d), d += kE;
        pool(p.ea, p.pa, kNA, p.x + d, p.x + d + kE), d += 2 * kE;
        pool(p.ee, p.pe, kNE, p.x + d, p.x + d + kE), d += 2 * kE;
        pool(p.ec, p.pc, kNC, p.x + d, p.x + d + kE), d += 2 * kE;
        pool(p.el, p.pl, kNL, p.x + d, p.x + d + kE), d += 2 * kE;
        dense(kT_W0, kT_b0, p.x, kTrunkIn, kTrunk, p.h0, true);
        break;
    }
    default: {
        dense(kT_W1, kT_b1, p.h0, kTrunk, kTrunk, p.h1, true);
        const float* z = p.h1;
        dense(kH_behaviour_W, kH_behaviour_b, z, kTrunk, 8, p.o.behaviour, false);
#ifdef NNW_HAS_OPTION
        dense(kH_option_W, kH_option_b, z, kTrunk, 5, p.o.option, false);
#else
        p.o.option[0] = 1e9f, p.o.option[1] = p.o.option[2] = p.o.option[3] = p.o.option[4] = 0.0f;
#endif
        const float* ents[kNC];
        for (int i = 0; i < kNC; ++i) ents[i] = p.ec[i];
        pointer(z, kP_target_qW, kP_target_qb, kP_target_kW, kP_target_kb, ents, p.pc, kNC, kP_target_E, 1, p.o.target);
        break;
    }
    }
}
#endif
} // namespace nn
