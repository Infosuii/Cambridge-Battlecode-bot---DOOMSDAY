// nn_rt.h (agent B) - pure inference kernels. No SDK, no heap, no exceptions, every loop bounded by its arguments.
//
// Numeric specification (reproduced bit-for-bit by python/nfs/models/reference.py, within float tolerance by the
// PyTorch PolicyNet; see agents/B/REPORT.md "Numerics"):
//   * f32 everywhere, IEEE round-to-nearest, no fused multiply-add (wasm32 has none; native tests use
//     -ffp-contract=off).
//   * dense:  y[o] = b[o]; then for i = 0..in-1 in order, skipping x[i] == 0: y[o] = y[o] + x[i] * W[i*out + o].
//     Weights are stored row-major [in][out] (PyTorch weight.T), so the update vectorises over o without
//     reassociation: SIMD and scalar paths give identical bits.
//   * act (rational tanh, "rtanh"): x' = clamp(x, -3, 3); t = x'*x'; y = (x' * (27 + t)) / (27 + 9*t);
//     y = clamp(y, -1, 1). Monotone, odd, C1 (derivative 9(x^2-9)^2/(27+9x^2)^2 vanishes exactly at |x| = 3),
//     max |rtanh - tanh| = 0.0235. NaN propagates (clamps are written as x < lo ? lo : x).
//   * bounded residual: R * act(r / R).
//   * masked mean: sum of valid rows in row order, divided by float(n); masked max starts at the first valid row;
//     both are 0 when no row is valid.
//   * argmax: strict '>' scan from index 0, so ties go to the lowest legal index (candidate 0 = teacher).
//   * log-softmax: m = max legal logit; s = sum_k exp(l_k - m) in index order; logp_k = (l_k - m) - log(s).
//   * PRNG: splitmix64 (Steele/Lea/Flood); uniform = (next >> 40) * 2^-24 in [0, 1).
#pragma once

#include <cmath>
#include <cstdint>
#include <cstring>

#if defined(__wasm_simd128__) && !defined(NN_RT_NO_SIMD)
#include <wasm_simd128.h>
#define NN_RT_SIMD 1
#else
#define NN_RT_SIMD 0
#endif

namespace nnrt {

inline constexpr float kNegInf = -__builtin_huge_valf();

// ---------------------------------------------------------------- activation
inline float act(float x) {
    x = x < -3.0f ? -3.0f : x;
    x = x > 3.0f ? 3.0f : x;
    const float t = x * x;
    float y = (x * (27.0f + t)) / (27.0f + 9.0f * t);
    y = y < -1.0f ? -1.0f : y;
    y = y > 1.0f ? 1.0f : y;
    return y;
}

// In-place activation of n values.
inline void act_n(float* v, int n) {
    int i = 0;
#if NN_RT_SIMD
    const v128_t lo = wasm_f32x4_splat(-3.0f), hi = wasm_f32x4_splat(3.0f);
    const v128_t c27 = wasm_f32x4_splat(27.0f), c9 = wasm_f32x4_splat(9.0f);
    const v128_t m1 = wasm_f32x4_splat(-1.0f), p1 = wasm_f32x4_splat(1.0f);
    for (; i + 4 <= n; i += 4) {
        v128_t x = wasm_v128_load(v + i);
        x = wasm_f32x4_pmax(x, lo); // x < lo ? lo : x
        x = wasm_f32x4_pmin(x, hi); // hi < x ? hi : x
        const v128_t t = wasm_f32x4_mul(x, x);
        v128_t y = wasm_f32x4_div(wasm_f32x4_mul(x, wasm_f32x4_add(c27, t)), wasm_f32x4_add(c27, wasm_f32x4_mul(c9, t)));
        y = wasm_f32x4_pmax(y, m1);
        y = wasm_f32x4_pmin(y, p1);
        wasm_v128_store(v + i, y);
    }
#endif
    for (; i < n; ++i) v[i] = act(v[i]);
}

// Hard tanh: measured alternative (cheaper, zero gradient outside [-1, 1]); not used by the model.
inline float hard_tanh(float x) {
    x = x < -1.0f ? -1.0f : x;
    return x > 1.0f ? 1.0f : x;
}

inline float bounded(float r, float R) { return R * act(r / R); }

// ---------------------------------------------------------------- dense layers
// Register-blocked y += x @ W for a compile-time output width: accumulators stay in Wasm locals and input rows are
// taken in pairs (one accumulator get/set per pair). The per-lane operation sequence is exactly the sequential one
// (acc = (acc + x0*w0) + x1*w1, zero rows skipped individually), so results are bit-identical to the generic and
// scalar paths and to the numpy reference. Measured: ~45% less fuel than one row at a time.
template <int OUT> inline void dense_acc_fixed(const float* __restrict x, int in, const float* __restrict W,
                                               float* __restrict y) {
#if NN_RT_SIMD
    static_assert(OUT % 4 == 0, "fixed kernels need OUT % 4 == 0");
    constexpr int V = OUT / 4;
    v128_t acc[V];
    for (int j = 0; j < V; ++j) acc[j] = wasm_v128_load(y + 4 * j);
    int i = 0;
    for (; i + 2 <= in; i += 2) {
        const float x0 = x[i], x1 = x[i + 1];
        const float* __restrict w0 = W + i * OUT;
        const float* __restrict w1 = w0 + OUT;
        if (x0 != 0.0f) {
            const v128_t s0 = wasm_f32x4_splat(x0);
            if (x1 != 0.0f) {
                const v128_t s1 = wasm_f32x4_splat(x1);
                for (int j = 0; j < V; ++j)
                    acc[j] = wasm_f32x4_add(wasm_f32x4_add(acc[j], wasm_f32x4_mul(s0, wasm_v128_load(w0 + 4 * j))),
                                            wasm_f32x4_mul(s1, wasm_v128_load(w1 + 4 * j)));
            } else {
                for (int j = 0; j < V; ++j) acc[j] = wasm_f32x4_add(acc[j], wasm_f32x4_mul(s0, wasm_v128_load(w0 + 4 * j)));
            }
        } else if (x1 != 0.0f) {
            const v128_t s1 = wasm_f32x4_splat(x1);
            for (int j = 0; j < V; ++j) acc[j] = wasm_f32x4_add(acc[j], wasm_f32x4_mul(s1, wasm_v128_load(w1 + 4 * j)));
        }
    }
    if (i < in && x[i] != 0.0f) {
        const v128_t s0 = wasm_f32x4_splat(x[i]);
        const float* __restrict w0 = W + i * OUT;
        for (int j = 0; j < V; ++j) acc[j] = wasm_f32x4_add(acc[j], wasm_f32x4_mul(s0, wasm_v128_load(w0 + 4 * j)));
    }
    for (int j = 0; j < V; ++j) wasm_v128_store(y + 4 * j, acc[j]);
#else
    float acc[OUT];
    for (int o = 0; o < OUT; ++o) acc[o] = y[o];
    for (int i = 0; i < in; ++i) {
        const float xi = x[i];
        if (xi == 0.0f) continue;
        const float* __restrict w = W + i * OUT;
        for (int o = 0; o < OUT; ++o) acc[o] = acc[o] + xi * w[o];
    }
    for (int o = 0; o < OUT; ++o) y[o] = acc[o];
#endif
}

// Generic y += x @ W (any width).
inline void dense_acc_generic(const float* __restrict x, int in, const float* __restrict W, int out,
                              float* __restrict y) {
    for (int i = 0; i < in; ++i) {
        const float xi = x[i];
        if (xi == 0.0f) continue;
        const float* __restrict w = W + i * out;
        int o = 0;
#if NN_RT_SIMD
        const v128_t xs = wasm_f32x4_splat(xi);
        for (; o + 4 <= out; o += 4)
            wasm_v128_store(y + o, wasm_f32x4_add(wasm_v128_load(y + o), wasm_f32x4_mul(xs, wasm_v128_load(w + o))));
#endif
        for (; o < out; ++o) y[o] = y[o] + xi * w[o];
    }
}

// y += x @ W (W row-major [in][out]); x[i] == 0 rows are skipped (exact: adding +-0 never changes a non-zero sum,
// and the reference twin skips identically). Widths 8/16/32/64 use the register-blocked kernel.
inline void dense_acc(const float* __restrict x, int in, const float* __restrict W, int out, float* __restrict y) {
    switch (out) {
    case 8: dense_acc_fixed<8>(x, in, W, y); return;
    case 16: dense_acc_fixed<16>(x, in, W, y); return;
    case 32: dense_acc_fixed<32>(x, in, W, y); return;
    case 64: dense_acc_fixed<64>(x, in, W, y); return;
    default: dense_acc_generic(x, in, W, out, y); return;
    }
}

// y = b + x @ W (b may be null = zero bias).
inline void dense(const float* __restrict x, int in, const float* __restrict W, const float* __restrict b, int out,
                  float* __restrict y) {
    if (b)
        std::memcpy(y, b, sizeof(float) * static_cast<unsigned>(out));
    else
        for (int o = 0; o < out; ++o) y[o] = 0.0f;
    dense_acc(x, in, W, out, y);
}

// Dot product in index order (single-output layers): s = b; s = s + x[i] * w[i].
inline float dot(const float* __restrict x, const float* __restrict w, int n, float b) {
    float s = b;
    for (int i = 0; i < n; ++i) s = s + x[i] * w[i];
    return s;
}

// ---------------------------------------------------------------- pooling
// Masked mean and max over R rows of width E (rows already embedded). mask[r] != 0 means valid.
// mean = (sum of valid rows in order) / float(n); max starts at the first valid row; both 0 when n == 0.
inline void pool_mean_max(const float* rows, const std::uint8_t* mask, int R, int E, float* mean, float* mx) {
    int n = 0;
    for (int e = 0; e < E; ++e) mean[e] = 0.0f, mx[e] = 0.0f;
    for (int r = 0; r < R; ++r) {
        if (!mask[r]) continue;
        const float* row = rows + r * E;
        if (n == 0) {
            for (int e = 0; e < E; ++e) mean[e] = row[e], mx[e] = row[e];
        } else {
            for (int e = 0; e < E; ++e) {
                mean[e] = mean[e] + row[e];
                mx[e] = row[e] > mx[e] ? row[e] : mx[e];
            }
        }
        ++n;
    }
    if (n > 1) {
        const float fn = static_cast<float>(n);
        for (int e = 0; e < E; ++e) mean[e] = mean[e] / fn;
    }
}

// ---------------------------------------------------------------- finiteness
// True when every value is finite. x - x is 0 for finite x and NaN for +-Inf/NaN; the running sum stays 0 exactly
// unless a non-finite value occurred (cheap, branch-free, vectorisable without fast-math).
inline bool all_finite(const float* x, int n) {
    float acc = 0.0f;
    int i = 0;
#if NN_RT_SIMD
    v128_t a = wasm_f32x4_splat(0.0f);
    for (; i + 4 <= n; i += 4) {
        const v128_t v = wasm_v128_load(x + i);
        a = wasm_f32x4_add(a, wasm_f32x4_sub(v, v));
    }
    acc = (wasm_f32x4_extract_lane(a, 0) + wasm_f32x4_extract_lane(a, 1)) +
          (wasm_f32x4_extract_lane(a, 2) + wasm_f32x4_extract_lane(a, 3));
#endif
    for (; i < n; ++i) acc = acc + (x[i] - x[i]);
    return acc == 0.0f;
}

inline bool is_finite(float v) { return (v - v) == 0.0f; }

// ---------------------------------------------------------------- candidate scoring
// logit[k] = prior[k] + R * act(r[k] / R) for legal k, -inf otherwise.
inline void logits_from_residual(const float* prior, const float* r, const std::uint8_t* legal, int K, float R,
                                 float* logit) {
    for (int k = 0; k < K; ++k) logit[k] = legal[k] ? prior[k] + bounded(r[k], R) : kNegInf;
}

// Lowest-index argmax over legal entries; -1 when nothing is legal.
inline int masked_argmax(const float* v, const std::uint8_t* legal, int K) {
    int best = -1;
    float bv = 0.0f;
    for (int k = 0; k < K; ++k) {
        if (!legal[k]) continue;
        if (best < 0 || v[k] > bv) best = k, bv = v[k];
    }
    return best;
}

// Masked log-softmax. Returns log(sum exp(l - m)) and m via out params; illegal entries get -inf.
// e[k] (optional) receives exp(l_k - m) for legal k, 0 otherwise. Returns false when nothing is legal.
inline bool masked_log_softmax(const float* l, const std::uint8_t* legal, int K, float* logp, float* e = nullptr) {
    const int a = masked_argmax(l, legal, K);
    if (a < 0) return false;
    const float m = l[a];
    float s = 0.0f;
    for (int k = 0; k < K; ++k) {
        const float ek = legal[k] ? std::exp(l[k] - m) : 0.0f;
        if (e) e[k] = ek;
        s = s + ek;
    }
    const float ls = std::log(s);
    for (int k = 0; k < K; ++k) logp[k] = legal[k] ? (l[k] - m) - ls : kNegInf;
    return true;
}

inline float masked_log_prob(const float* l, const std::uint8_t* legal, int K, int choice) {
    float lp[64];
    if (K > 64 || choice < 0 || choice >= K || !legal[choice]) return kNegInf;
    if (!masked_log_softmax(l, legal, K, lp)) return kNegInf;
    return lp[choice];
}

// ---------------------------------------------------------------- PRNG (training-time sampling only)
struct SplitMix64 {
    std::uint64_t s;
    std::uint64_t next() {
        std::uint64_t z = (s += 0x9E3779B97F4A7C15ull);
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
        return z ^ (z >> 31);
    }
    // Uniform in [0, 1) with 24 random bits (exactly representable in f32).
    float uniform() { return static_cast<float>(next() >> 40) * (1.0f / 16777216.0f); }
};

// Stateless splitmix finaliser used to derive per-decision streams.
inline std::uint64_t mix64(std::uint64_t z) {
    z += 0x9E3779B97F4A7C15ull;
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
    return z ^ (z >> 31);
}

// Stream for one decision: deterministic in (seed, round, champion, head, per-turn call index).
inline SplitMix64 decision_stream(std::uint32_t seed, std::uint32_t round, std::uint32_t champion, std::uint32_t head,
                                  std::uint32_t call) {
    std::uint64_t s = mix64(seed);
    s = mix64(s ^ round);
    s = mix64(s ^ champion);
    s = mix64(s ^ head);
    s = mix64(s ^ call);
    return SplitMix64{s};
}

// Inverse-CDF sample from the masked softmax of l with uniform u in [0, 1). Uses unnormalised weights
// e_k = exp(l_k - m): first legal k with u * s < cumsum_k; falls back to the last legal index (rounding).
// Writes log p(choice) to *logp. Returns -1 when nothing is legal.
inline int masked_sample(const float* l, const std::uint8_t* legal, int K, float u, float* logp) {
    float e[64], lp[64];
    if (K > 64 || !masked_log_softmax(l, legal, K, lp, e)) return -1;
    float s = 0.0f;
    for (int k = 0; k < K; ++k) s = s + e[k];
    const float target = u * s;
    float c = 0.0f;
    int last = -1, pick = -1;
    for (int k = 0; k < K; ++k) {
        if (!legal[k]) continue;
        last = k;
        c = c + e[k];
        if (target < c) {
            pick = k;
            break;
        }
    }
    if (pick < 0) pick = last;
    *logp = lp[pick];
    return pick;
}

// ---------------------------------------------------------------- checksum
// FNV-1a 64 over the little-endian bytes of f32 values; resumable (pass the running hash back in).
inline constexpr std::uint64_t kFnvOffset = 0xCBF29CE484222325ull, kFnvPrime = 0x00000100000001B3ull;

inline std::uint64_t fnv1a64_f32(std::uint64_t h, const float* v, int n, bool* finite) {
    bool ok = true;
    for (int i = 0; i < n; ++i) {
        std::uint32_t u;
        std::memcpy(&u, v + i, 4);
        ok = ok && ((u & 0x7F800000u) != 0x7F800000u);
        h = (h ^ (u & 0xFFu)) * kFnvPrime;
        h = (h ^ ((u >> 8) & 0xFFu)) * kFnvPrime;
        h = (h ^ ((u >> 16) & 0xFFu)) * kFnvPrime;
        h = (h ^ (u >> 24)) * kFnvPrime;
    }
    if (finite) *finite = *finite && ok;
    return h;
}

inline std::uint64_t fnv1a64_bytes(std::uint64_t h, const void* p, int n) {
    const unsigned char* b = static_cast<const unsigned char*>(p);
    for (int i = 0; i < n; ++i) h = (h ^ b[i]) * kFnvPrime;
    return h;
}

} // namespace nnrt
