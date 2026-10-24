// rt_kernels.cpp (agent B) - self-checking native tests of bot/src/nn_rt.h and nn_log.h (synthetic data only).
// Built by tools/run_cpp_tests.py: g++ -std=c++20 -O2 -ffp-contract=off. Prints "PASS <name>" / "FAIL <name> ...".
#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "nn_log.h"
#include "nn_rt.h"

static int g_fail = 0, g_pass = 0;
#define CHECK(cond, name, ...)                                                                                       \
    do {                                                                                                             \
        if (cond) {                                                                                                  \
            ++g_pass;                                                                                                \
            std::printf("PASS %s\n", name);                                                                          \
        } else {                                                                                                     \
            ++g_fail;                                                                                                \
            std::printf("FAIL %s ", name);                                                                           \
            std::printf(__VA_ARGS__);                                                                                \
            std::printf("\n");                                                                                       \
        }                                                                                                            \
    } while (0)

static std::uint32_t bits(float f) {
    std::uint32_t u;
    std::memcpy(&u, &f, 4);
    return u;
}

static void test_act() {
    CHECK(nnrt::act(0.0f) == 0.0f && nnrt::act(3.0f) == 1.0f && nnrt::act(-3.0f) == -1.0f &&
              nnrt::act(50.0f) == 1.0f && nnrt::act(-1e30f) == -1.0f,
          "act_fixed_points", "act(3)=%g", nnrt::act(3.0f));
    double maxerr = 0;
    bool mono = true, odd = true;
    float prev = -2.0f;
    for (int i = -40000; i <= 40000; ++i) {
        const float x = i * 1e-4f;
        const float y = nnrt::act(x);
        maxerr = std::fmax(maxerr, std::fabs(double(y) - std::tanh(double(x))));
        if (y < prev - 3e-7f) mono = false; // f32 rounding: <= 4 ulp wiggle where act' ~ 0 (|x| -> 3)
        prev = y;
        if (bits(nnrt::act(-x)) != (bits(y) ^ 0x80000000u) && !(x == 0.0f)) odd = false;
    }
    CHECK(maxerr < 0.0236, "act_tanh_error", "max |act - tanh| = %g", maxerr);
    CHECK(mono, "act_monotone_4ulp", "not monotone");
    CHECK(odd, "act_odd_exact", "act(-x) != -act(x)");
    CHECK(std::isnan(nnrt::act(std::nanf(""))), "act_nan_propagates", "NaN swallowed");
    float v[23];
    for (int i = 0; i < 23; ++i) v[i] = (i - 11) * 0.37f;
    float w[23];
    std::memcpy(w, v, sizeof v);
    nnrt::act_n(w, 23);
    bool same = true;
    for (int i = 0; i < 23; ++i) same = same && bits(w[i]) == bits(nnrt::act(v[i]));
    CHECK(same, "act_n_matches_scalar", "vector path differs");
    CHECK(nnrt::bounded(0.0f, 2.0f) == 0.0f && nnrt::bounded(100.0f, 2.0f) == 2.0f &&
              nnrt::bounded(-100.0f, 2.0f) == -2.0f,
          "bounded_residual", "bounded wrong");
}

static void test_dense() {
    nnrt::SplitMix64 r{7};
    const int in = 37, out = 22;
    std::vector<float> x(in), W(in * out), b(out), y(out);
    for (auto& v : x) v = r.uniform() * 2 - 1;
    for (int i = 0; i < in; i += 5) x[i] = 0.0f; // sparse inputs exercise the zero-skip
    for (auto& v : W) v = r.uniform() * 2 - 1;
    for (auto& v : b) v = r.uniform() - 0.5f;
    nnrt::dense(x.data(), in, W.data(), b.data(), out, y.data());
    double err = 0;
    bool seq = true;
    for (int o = 0; o < out; ++o) {
        double s = b[o];
        float fs = b[o];
        for (int i = 0; i < in; ++i) s += double(x[i]) * W[i * out + o], fs = fs + x[i] * W[i * out + o];
        err = std::fmax(err, std::fabs(s - y[o]));
        // zero-skip is exact: identical to the full sequential sum except possibly the sign of an exact zero
        seq = seq && (y[o] == fs);
    }
    CHECK(err < 1e-5, "dense_vs_double", "err %g", err);
    CHECK(seq, "dense_sequential_order_exact", "skip-zero changed a value");
    CHECK(std::fabs(nnrt::dot(x.data(), W.data(), in, 0.5f) - 0.5f -
                    [&] { double s = 0; for (int i = 0; i < in; ++i) s += double(x[i]) * W[i]; return s; }()) < 1e-5,
          "dot", "dot wrong");
}

static void test_pool() {
    const int R = 6, E = 5;
    float rows[R * E];
    std::uint8_t mask[R] = {1, 0, 1, 1, 0, 0};
    for (int i = 0; i < R * E; ++i) rows[i] = std::sin(i * 0.7f);
    float mean[E], mx[E];
    nnrt::pool_mean_max(rows, mask, R, E, mean, mx);
    // padding invariance: garbage in masked rows changes nothing
    float rows2[R * E];
    std::memcpy(rows2, rows, sizeof rows);
    for (int e = 0; e < E; ++e) rows2[1 * E + e] = 1e9f, rows2[5 * E + e] = std::nanf("");
    float mean2[E], mx2[E];
    nnrt::pool_mean_max(rows2, mask, R, E, mean2, mx2);
    CHECK(std::memcmp(mean, mean2, sizeof mean) == 0 && std::memcmp(mx, mx2, sizeof mx) == 0, "pool_padding_invariant",
          "masked rows leaked");
    // permutation of valid rows: max exact, mean within 1 ulp-ish
    float rows3[R * E];
    std::memcpy(rows3, rows, sizeof rows);
    for (int e = 0; e < E; ++e) std::swap(rows3[0 * E + e], rows3[3 * E + e]);
    float mean3[E], mx3[E];
    nnrt::pool_mean_max(rows3, mask, R, E, mean3, mx3);
    double d = 0;
    for (int e = 0; e < E; ++e) d = std::fmax(d, std::fabs(mean3[e] - mean[e]));
    CHECK(std::memcmp(mx, mx3, sizeof mx) == 0 && d < 1e-6, "pool_permutation_invariant", "d=%g", d);
    std::uint8_t none[R] = {};
    nnrt::pool_mean_max(rows, none, R, E, mean, mx);
    bool zero = true;
    for (int e = 0; e < E; ++e) zero = zero && mean[e] == 0 && mx[e] == 0;
    CHECK(zero, "pool_empty_is_zero", "empty pool not zero");
}

static void test_argmax_softmax() {
    const float l[6] = {1.0f, 2.0f, 2.0f, 5.0f, 2.0f, 5.0f};
    std::uint8_t legal[6] = {1, 1, 1, 0, 1, 0};
    CHECK(nnrt::masked_argmax(l, legal, 6) == 1, "argmax_lowest_index_tie", "got %d", nnrt::masked_argmax(l, legal, 6));
    const float t[4] = {0.5f, 0.5f, 0.5f, 0.5f};
    std::uint8_t all[4] = {1, 1, 1, 1};
    CHECK(nnrt::masked_argmax(t, all, 4) == 0, "argmax_all_tied_teacher", "tie not to 0");
    std::uint8_t none[6] = {};
    CHECK(nnrt::masked_argmax(l, none, 6) == -1, "argmax_empty", "expected -1");
    float lp[6];
    nnrt::masked_log_softmax(l, legal, 6, lp);
    double s = 0;
    for (int k = 0; k < 6; ++k)
        if (legal[k]) s += std::exp(double(lp[k]));
    CHECK(std::fabs(s - 1.0) < 1e-6 && std::isinf(lp[3]) && lp[3] < 0, "log_softmax_normalised", "sum %g", s);
    CHECK(nnrt::masked_log_prob(l, legal, 6, 3) == nnrt::kNegInf && nnrt::masked_log_prob(l, legal, 6, 1) == lp[1],
          "log_prob_masked", "log_prob wrong");
}

static void test_finite() {
    bool ok = true;
    for (int n = 1; n <= 21; ++n) {
        std::vector<float> v(n, 0.25f);
        if (!nnrt::all_finite(v.data(), n)) ok = false;
        for (int pos = 0; pos < n; ++pos) {
            for (float bad : {std::nanf(""), INFINITY, -INFINITY}) {
                std::vector<float> w = v;
                w[pos] = bad;
                if (nnrt::all_finite(w.data(), n)) ok = false;
            }
        }
    }
    CHECK(ok, "all_finite_detects_nan_inf", "missed a non-finite value");
    CHECK(!nnrt::is_finite(INFINITY) && !nnrt::is_finite(std::nanf("")) && nnrt::is_finite(-3.0f), "is_finite",
          "is_finite wrong");
}

static void test_prng_hash() {
    nnrt::SplitMix64 r{0};
    CHECK(r.next() == 0xE220A8397B1DCDAFull, "splitmix64_reference_value", "first output wrong");
    float u = 0;
    bool range = true;
    nnrt::SplitMix64 q{12345};
    for (int i = 0; i < 100000; ++i) {
        u = q.uniform();
        range = range && u >= 0.0f && u < 1.0f;
    }
    CHECK(range, "uniform_range", "out of [0,1)");
    CHECK(nnrt::fnv1a64_bytes(nnrt::kFnvOffset, "", 0) == 0xCBF29CE484222325ull &&
              nnrt::fnv1a64_bytes(nnrt::kFnvOffset, "a", 1) == 0xAF63DC4C8601EC8Cull &&
              nnrt::fnv1a64_bytes(nnrt::kFnvOffset, "foobar", 6) == 0x85944171F73967E8ull,
          "fnv1a64_vectors", "fnv vectors");
    const float f[3] = {1.0f, -2.5f, 0.1f};
    bool fin = true;
    CHECK(nnrt::fnv1a64_f32(nnrt::kFnvOffset, f, 3, &fin) == nnrt::fnv1a64_bytes(nnrt::kFnvOffset, f, 12) && fin,
          "fnv1a64_f32_le_bytes", "f32 hash != byte hash");
    const float g[2] = {1.0f, std::nanf("")};
    fin = true;
    nnrt::fnv1a64_f32(nnrt::kFnvOffset, g, 2, &fin);
    CHECK(!fin, "fnv1a64_f32_flags_nan", "NaN not flagged");
}

static void test_sampling() {
    const int K = 6;
    const float l[K] = {0.3f, 1.2f, -0.5f, 0.9f, 2.0f, 0.0f};
    const std::uint8_t legal[K] = {1, 1, 1, 1, 0, 1};
    float lp[K];
    nnrt::masked_log_softmax(l, legal, K, lp);
    long cnt[K] = {};
    nnrt::SplitMix64 r{99};
    const int N = 400000;
    bool logp_ok = true;
    for (int i = 0; i < N; ++i) {
        float logp = 0;
        const int k = nnrt::masked_sample(l, legal, K, r.uniform(), &logp);
        ++cnt[k];
        logp_ok = logp_ok && logp == lp[k];
    }
    double worst = 0;
    for (int k = 0; k < K; ++k) {
        const double p = legal[k] ? std::exp(double(lp[k])) : 0.0;
        worst = std::fmax(worst, std::fabs(double(cnt[k]) / N - p) / std::sqrt(p * (1 - p) / N + 1e-12));
    }
    CHECK(cnt[4] == 0, "sample_never_illegal", "sampled an illegal candidate");
    CHECK(worst < 5.0, "sample_distribution", "max z-score %g", worst);
    CHECK(logp_ok, "sample_logp_matches_log_softmax", "logp mismatch");
    float logp;
    CHECK(nnrt::masked_sample(l, legal, K, 0.0f, &logp) == 0 && nnrt::masked_sample(l, legal, K, 0.99999994f, &logp) == 5,
          "sample_extremes", "extremes wrong");
}

static void test_base64() {
    std::memcpy(nnlog::g_payload, "Man", 3);
    int n = nnlog::encode_line(3);
    bool a = std::string(nnlog::g_text, n) == "NFS1 TWFu\n";
    n = nnlog::encode_line(2);
    bool b = std::string(nnlog::g_text, n) == "NFS1 TWE=\n";
    n = nnlog::encode_line(1);
    bool c = std::string(nnlog::g_text, n) == "NFS1 TQ==\n";
    CHECK(a && b && c, "base64_rfc4648", "base64 wrong");
}

int main() {
    test_act();
    test_dense();
    test_pool();
    test_argmax_softmax();
    test_finite();
    test_prng_hash();
    test_sampling();
    test_base64();
    std::printf("SUMMARY rt_kernels pass=%d fail=%d\n", g_pass, g_fail);
    return g_fail ? 1 : 0;
}
