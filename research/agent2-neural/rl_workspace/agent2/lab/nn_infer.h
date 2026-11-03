// Neural bot forward pass (agent2/lab/nn_model.py Net, weights from nn_export.py in nn_weights.h). Input: the int16
// features of nnrec.cpp. Output: logits per head (pointer heads over present entities, absent ones at -1e9).
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
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

inline void dense(const float* W, const float* b, const float* x, int in, int out, float* y, bool relu) {
#if defined(__wasm_simd128__) && defined(A2_NN_FAST) && A2_NN_FAST
    // 4-wide multiply-adds (A2_NN_FAST): ~4x fewer instructions (fuel) than the scalar loop
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

// signed log1p of an int16 feature; A2_NN_FAST reads a table for |v| < 4096 (filled once)
inline float slog(float v) {
#if defined(A2_NN_FAST) && A2_NN_FAST
    static float tab[4096];
    static bool ready = false;
    if (!ready) {
        for (int i = 0; i < 4096; ++i) tab[i] = std::log1p(static_cast<float>(i));
        ready = true;
    }
    const int a = static_cast<int>(v < 0 ? -v : v);
    const float l = a < 4096 ? tab[a] : std::log1p(static_cast<float>(a));
    return v < 0 ? -l : l;
#else
    return v < 0 ? -std::log1p(-v) : std::log1p(v);
#endif
}

// one entity block: prep (signed log, standardise, one-hot category: champion type, or the ladder map id) + encoder
// layers -> emb [n][kE]
template <int N, int W, int NKEEP, int TYPEF, int NTYPE, int LAYERS>
inline void encode(const std::int16_t* f, const int* keep, const float* mu, const float* sd, const float* const* Ws,
                   const float* const* bs, const int* ins, float emb[][kE], bool* present, bool always) {
    for (int e = 0; e < N; ++e) {
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

template <class Tag = void>
inline void forward(const std::int16_t* f, Out& o, unsigned heads = kHAll) {
    using namespace nnw;
    float eg[1][kE], es[1][kE], ea[kNA][kE], ee[kNE][kE], ec[kNC][kE], el[kNL][kE];
    bool pg[1], ps[1], pa[kNA], pe[kNE], pc[kNC], pl[kNL];
#define LAYER_ARRAYS(X)                                                                                                      const float* X##W[] = {k##X##_W0, k##X##_W1v};                                                                         const float* X##B[] = {k##X##_b0, k##X##_b1v};                                                                         const int X##I[] = {k##X##_in0, kE};
    LAYER_ARRAYS(g) LAYER_ARRAYS(s) LAYER_ARRAYS(a) LAYER_ARRAYS(e) LAYER_ARRAYS(c) LAYER_ARRAYS(l)
#undef LAYER_ARRAYS
    encode<kg_n, kg_w, kg_nkeep, kg_type, kg_ntype, kg_layers>(f + kg_off, kg_keep, kg_mu, kg_sd, gW, gB, gI, eg, pg, true);
    encode<ks_n, ks_w, ks_nkeep, ks_type, ks_ntype, ks_layers>(f + ks_off, ks_keep, ks_mu, ks_sd, sW, sB, sI, es, ps, true);
    encode<ka_n, ka_w, ka_nkeep, ka_type, ka_ntype, ka_layers>(f + ka_off, ka_keep, ka_mu, ka_sd, aW, aB, aI, ea, pa, false);
    encode<ke_n, ke_w, ke_nkeep, ke_type, ke_ntype, ke_layers>(f + ke_off, ke_keep, ke_mu, ke_sd, eW, eB, eI, ee, pe, false);
    encode<kc_n, kc_w, kc_nkeep, kc_type, kc_ntype, kc_layers>(f + kc_off, kc_keep, kc_mu, kc_sd, cW, cB, cI, ec, pc, false);
    encode<kl_n, kl_w, kl_nkeep, kl_type, kl_ntype, kl_layers>(f + kl_off, kl_keep, kl_mu, kl_sd, lW, lB, lI, el, pl, false);
    float x[kTrunkIn];
    int d = 0;
    std::copy(eg[0], eg[0] + kE, x + d), d += kE;
    std::copy(es[0], es[0] + kE, x + d), d += kE;
    pool(ea, pa, kNA, x + d, x + d + kE), d += 2 * kE;
    pool(ee, pe, kNE, x + d, x + d + kE), d += 2 * kE;
    pool(ec, pc, kNC, x + d, x + d + kE), d += 2 * kE;
    pool(el, pl, kNL, x + d, x + d + kE), d += 2 * kE;
    float h0[kTrunk], h1[kTrunk];
    dense(kT_W0, kT_b0, x, kTrunkIn, kTrunk, h0, true);
    dense(kT_W1, kT_b1, h0, kTrunk, kTrunk, h1, true);
    const float* z = h1;
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
    if (heads & kHTarget) {
        const float* ents[kNC];
        for (int i = 0; i < kNC; ++i) ents[i] = ec[i];
        pointer(z, kP_target_qW, kP_target_qb, kP_target_kW, kP_target_kb, ents, pc, kNC, kP_target_E, 1, o.target);
    }
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
} // namespace nn
