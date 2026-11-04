// cl1 camp-pointer actor inference (format jd-cl1-pointer-f32-v1, preprocessing jd-cl1-af91-v1), float32.
// Implements JOHNDOE tools/rl_learner_1104/rl_learner_1104/cl1.py (CampPointer.forward + preprocess) exactly:
// entity encoders Linear+ReLU (8), masked mean + max pooling in order ally, altar, camp, enemy, globals 58 ->
// context Linear+ReLU (32) -> GRUCell 16 (gate order r, z, n; reset zeroes the incoming hidden state) -> per-camp
// score tanh(Linear[24->16]) -> Linear[16->1], none head Linear[16->1]. Absent camps are illegal; none always legal.
// No SDK calls: input is one cl1 int16[448] row, so the same code runs on the host, in tests and in the bot.
#pragma once
#include <cmath>
#include <cstdint>
#include <limits>

#include "clrl_actor_weights.h"

namespace clrl_actor {
constexpr int kH = 16, kG = 58, kCtxIn = 122, kNA = 13;
constexpr int kWAlly = 20, kWEnemy = 23, kWCamp = 19, kWAltar = 4;

struct Out {
    float logits[kNA];  // -inf where illegal
    bool legal[kNA];
    float h[kH];
};

inline float onehot_at(float x, int n, int i) { return (x >= 0 && x < n && static_cast<int>(x) == i) ? 1.0f : 0.0f; }

// y[o] = b[o] + sum_i W[o][i] * x[i]  (W row-major [out][in], PyTorch Linear layout)
inline void linear(const float* W, const float* b, const float* x, int in, int out, float* y) {
    for (int o = 0; o < out; ++o) {
        float s = 0.0f;
        for (int i = 0; i < in; ++i) s += W[o * in + i] * x[i];
        y[o] = s + b[o];
    }
}

inline float sigmoid(float v) { return 1.0f / (1.0f + std::exp(-v)); }

struct Pre {
    float glob[kG];
    float ally[5][kWAlly], enemy[6][kWEnemy], camp[12][kWCamp], altar[4][kWAltar];
    bool pa[5], pe[6], pc[12], pl[4];
};

inline void preprocess(const std::int16_t* raw, Pre& p) {
    float x[448];
    for (int i = 0; i < 448; ++i) x[i] = static_cast<float>(raw[i]);
    const float* g = x;
    const float* s = x + 16;
    int k = 0;
    const float gdiv[7] = { 2000, 1000, 1000, 1000, 6, 256, 256 };
    for (int i = 0; i < 7; ++i) p.glob[k++] = g[i] / gdiv[i];
    for (int i = 0; i < 3; ++i) p.glob[k++] = onehot_at(g[7], 3, i);
    for (int i = 0; i < 6; ++i) p.glob[k++] = onehot_at(g[8], 6, i);
    for (int i = 9; i < 12; ++i) p.glob[k++] = g[i] / 6.0f;
    for (int i = 12; i < 14; ++i) p.glob[k++] = (g[i] < 0 ? 0.0f : g[i]) / 256.0f;
    for (int i = 12; i < 14; ++i) p.glob[k++] = g[i] >= 0 ? 1.0f : 0.0f;
    for (int i = 0; i < 13; ++i) p.glob[k++] = onehot_at(s[0], 13, i);
    const float sdiv[8] = { 256, 256, 1000, 1000, 100, 100, 1000, 1000 };
    for (int i = 0; i < 8; ++i) p.glob[k++] = s[1 + i] / sdiv[i];
    const long bits = static_cast<long>(s[9]);
    for (int i = 0; i < 9; ++i) p.glob[k++] = static_cast<float>((bits >> i) & 1);
    const float sdiv2[5] = { 100, 100, 32, 1, 4 };
    for (int i = 0; i < 5; ++i) p.glob[k++] = s[10 + i] / sdiv2[i];

    const float adiv[6] = { 256, 256, 1000, 256, 100, 32 };
    for (int r = 0; r < 5; ++r) {
        const float* a = x + 48 + r * 16;
        p.pa[r] = a[0] > 0;
        const float vis = a[2] > 0 ? 1.0f : 0.0f;
        int j = 0;
        for (int i = 0; i < 13; ++i) p.ally[r][j++] = onehot_at(a[1], 13, i);
        p.ally[r][j++] = vis;
        for (int i = 0; i < 6; ++i) p.ally[r][j++] = (a[3 + i] / adiv[i]) * vis;
        if (!p.pa[r]) for (int i = 0; i < kWAlly; ++i) p.ally[r][i] = 0.0f;
    }
    const float ediv[7] = { 256, 256, 1000, 1000, 256, 32, 1 };
    for (int r = 0; r < 6; ++r) {
        const float* e = x + 128 + r * 16;
        p.pe[r] = e[0] > 0;
        int j = 0;
        for (int i = 0; i < 13; ++i) p.enemy[r][j++] = onehot_at(e[1], 13, i);
        p.enemy[r][j++] = e[2];
        p.enemy[r][j++] = (e[3] < 0 ? 0.0f : e[3]) / 2000.0f;
        p.enemy[r][j++] = e[3] >= 0 ? 1.0f : 0.0f;
        for (int i = 0; i < 7; ++i) p.enemy[r][j++] = e[4 + i] / ediv[i];
        if (!p.pe[r]) for (int i = 0; i < kWEnemy; ++i) p.enemy[r][i] = 0.0f;
    }
    const float cdiv[9] = { 256, 256, 16, 16, 16, 16, 16, 16, 16 };
    const float cdiv2[3] = { 16, 1000, 256 };
    for (int r = 0; r < 12; ++r) {
        const float* c = x + 224 + r * 16;
        p.pc[r] = c[0] > 0;
        int j = 0;
        for (int i = 0; i < 9; ++i) p.camp[r][j++] = c[1 + i] / cdiv[i];
        for (int i = 0; i < 3; ++i) p.camp[r][j++] = onehot_at(c[10], 3, i);
        p.camp[r][j++] = c[10] >= 0 ? 1.0f : 0.0f;
        for (int i = 0; i < 3; ++i) p.camp[r][j++] = c[11 + i] / cdiv2[i];
        p.camp[r][j++] = (c[14] < 0 ? 0.0f : c[14]) / 2000.0f;
        p.camp[r][j++] = c[14] >= 0 ? 1.0f : 0.0f;
        p.camp[r][j++] = c[15] / 1000.0f;
        if (!p.pc[r]) for (int i = 0; i < kWCamp; ++i) p.camp[r][i] = 0.0f;
    }
    const int lidx[4] = { 1, 2, 3, 7 };
    const float ldiv[4] = { 256, 256, 256, 1 };
    for (int r = 0; r < 4; ++r) {
        const float* l = x + 416 + r * 8;
        p.pl[r] = l[0] > 0;
        for (int i = 0; i < 4; ++i) p.altar[r][i] = p.pl[r] ? l[lidx[i]] / ldiv[i] : 0.0f;
    }
}

// Encode a block of entity rows with Linear+ReLU(8); write masked mean then max (zeros when no row is present).
template <int N, int W>
inline void pool(const float (&rows)[N][W], const bool (&present)[N], const float* w, const float* b, float* mean,
                 float* mx, float (*enc)[8] = nullptr) {
    float z[N][8];
    int n = 0;
    for (int r = 0; r < N; ++r) {
        linear(w, b, rows[r], W, 8, z[r]);
        for (int o = 0; o < 8; ++o) z[r][o] = z[r][o] > 0.0f ? z[r][o] : 0.0f;
        if (enc) for (int o = 0; o < 8; ++o) enc[r][o] = z[r][o];
        n += present[r] ? 1 : 0;
    }
    for (int o = 0; o < 8; ++o) {
        float s = 0.0f, m = -std::numeric_limits<float>::infinity();
        for (int r = 0; r < N; ++r)
            if (present[r]) {
                s += z[r][o];
                m = z[r][o] > m ? z[r][o] : m;
            }
        mean[o] = s / static_cast<float>(n > 1 ? n : 1);
        mx[o] = n > 0 ? m : 0.0f;
    }
}

inline void forward(const std::int16_t* raw, const float* h_in, bool reset, Out& out) {
    using namespace clrl_w;
    Pre p;
    preprocess(raw, p);
    float ctx_in[kCtxIn];
    float camp_enc[12][8];
    pool<5, kWAlly>(p.ally, p.pa, enc_ally_w, enc_ally_b, ctx_in + 0, ctx_in + 8);
    pool<4, kWAltar>(p.altar, p.pl, enc_altar_w, enc_altar_b, ctx_in + 16, ctx_in + 24);
    pool<12, kWCamp>(p.camp, p.pc, enc_camp_w, enc_camp_b, ctx_in + 32, ctx_in + 40, camp_enc);
    pool<6, kWEnemy>(p.enemy, p.pe, enc_enemy_w, enc_enemy_b, ctx_in + 48, ctx_in + 56);
    for (int i = 0; i < kG; ++i) ctx_in[64 + i] = p.glob[i];
    float ctx[32];
    linear(ctx_w, ctx_b, ctx_in, kCtxIn, 32, ctx);
    for (int i = 0; i < 32; ++i) ctx[i] = ctx[i] > 0.0f ? ctx[i] : 0.0f;

    float hp[kH], gi[48], gh[48];
    for (int i = 0; i < kH; ++i) hp[i] = reset ? 0.0f : h_in[i];
    linear(gru_wih, gru_bih, ctx, 32, 48, gi);
    linear(gru_whh, gru_bhh, hp, kH, 48, gh);
    for (int i = 0; i < kH; ++i) {
        const float r = sigmoid(gi[i] + gh[i]);
        const float z = sigmoid(gi[kH + i] + gh[kH + i]);
        const float n = std::tanh(gi[2 * kH + i] + r * gh[2 * kH + i]);
        out.h[i] = (1.0f - z) * n + z * hp[i];
    }
    for (int c = 0; c < 12; ++c) {
        float pin[24], t[16], sc;
        for (int i = 0; i < 8; ++i) pin[i] = camp_enc[c][i];
        for (int i = 0; i < kH; ++i) pin[8 + i] = out.h[i];
        linear(ptr_w, ptr_b, pin, 24, 16, t);
        for (int i = 0; i < 16; ++i) t[i] = std::tanh(t[i]);
        linear(score_w, score_b, t, 16, 1, &sc);
        out.legal[c] = p.pc[c];
        out.logits[c] = p.pc[c] ? sc : -std::numeric_limits<float>::infinity();
    }
    linear(none_w, none_b, out.h, kH, 1, &out.logits[12]);
    out.legal[12] = true;
}
}  // namespace clrl_actor
