// Host fixture for the ported network (nn_infer.h + jd_nn_weights.h, FEAT-003): saturation / overflow on extreme
// int16 inputs, absent-entity masking, determinism, and the pipelined forward (JD_NN_EVENT's nn::pipe_stage path)
// equal to the one-shot forward on the heads the bot reads. The torch cross-check is tools/jd_g5070-1104/nn_golden.py.
#define JD_NN_EVENT 1
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>

#include "nn_infer.h"

namespace {
int checks = 0, failures = 0;
void check(bool ok, const char* what, int i) {
    ++checks;
    if (!ok) {
        ++failures;
        if (failures < 20) std::printf("FAIL %s (case %d)\n", what, i);
    }
}
constexpr int kNF = 500, kCOff = 248, kCF = 22, kC = 10;
std::uint64_t rs = 0x1104ull;
std::uint64_t next() {
    rs ^= rs << 13, rs ^= rs >> 7, rs ^= rs << 17;
    return rs;
}
bool finite_or_masked(float v) { return std::isfinite(v); }
template <int N>
bool all_finite(const float (&v)[N]) {
    for (int i = 0; i < N; ++i)
        if (!finite_or_masked(v[i])) return false;
    return true;
}
} // namespace

int main() {
    static_assert(nnw::kc_off == kCOff && nnw::kc_n == kC && nnw::kc_w == kCF, "layout 2 weights");
    std::int16_t f[kNF];
    for (int c = 0; c < 400; ++c) {
        // 0: all zero; 1: all +32767; 2: all -32768; 3: +-32000 (the recorder's clamp); 4+: random full-range int16
        // with random presence flags (0 / 1 / 2) on every entity row
        for (int i = 0; i < kNF; ++i) {
            if (c == 0) f[i] = 0;
            else if (c == 1) f[i] = 32767;
            else if (c == 2) f[i] = -32768;
            else if (c == 3) f[i] = (i & 1) ? 32000 : -32000;
            else f[i] = static_cast<std::int16_t>(static_cast<std::uint16_t>(next() & 0xFFFF));
        }
        if (c >= 4) {
            const int offs[4] = {60, 120, 248, 468}, ns[4] = {5, 8, 10, 4}, ws[4] = {12, 16, 22, 8};
            for (int b = 0; b < 4; ++b)
                for (int e = 0; e < ns[b]; ++e) f[offs[b] + e * ws[b]] = static_cast<std::int16_t>(next() % 3);
        }
        nn::Out o1{}, o2{};
        nn::forward(f, o1, nn::kHBeh | nn::kHTarget | nn::kHOption);
        nn::forward(f, o2, nn::kHBeh | nn::kHTarget | nn::kHOption);
        check(all_finite(o1.behaviour) && all_finite(o1.option), "behaviour / option logits finite on extreme input", c);
        bool tf = true, masked = true;
        for (int t = 0; t < kC; ++t) {
            const bool present = f[kCOff + t * kCF] != 0;
            tf &= std::isfinite(o1.target[t]);
            if (!present) masked &= o1.target[t] == -1e9f;
            else masked &= o1.target[t] > -1e8f;
        }
        tf &= std::isfinite(o1.target[kC]);
        check(tf, "target logits finite on extreme input", c);
        check(masked, "absent camp slots masked at -1e9, present ones not", c);
        check(std::memcmp(&o1, &o2, sizeof o1) == 0, "deterministic forward", c);
        // pipelined forward (JD_NN_EVENT): same sums in the same order -> identical heads
        nn::Pipe p{};
        for (int s = 0; s < nn::kPipeStages; ++s) nn::pipe_stage(p, f, s);
        check(std::memcmp(p.o.behaviour, o1.behaviour, sizeof o1.behaviour) == 0, "pipe behaviour == forward", c);
        check(std::memcmp(p.o.target, o1.target, sizeof o1.target) == 0, "pipe target == forward", c);
        check(std::memcmp(p.o.option, o1.option, sizeof o1.option) == 0, "pipe option == forward", c);
    }
    // slog saturation: symmetric, monotone, finite at the int16 extremes
    check(nn::slog(32767.0f) == -nn::slog(-32767.0f), "slog symmetric", 0);
    check(std::isfinite(nn::slog(-32768.0f)) && nn::slog(-32768.0f) < nn::slog(-32767.0f) + 1e-6f, "slog finite at -32768", 0);
    check(nn::slog(0.0f) == 0.0f, "slog(0) = 0", 0);
    std::printf("nn_infer_test: %d checks, %d failures\n", checks, failures);
    return failures ? 1 : 0;
}
