// Small trained policy; only this file is rebuilt when weights change.
#include "neural_policy.h"
#include "neural_weights.h"
#include <cmath>
#include <cstdio>
#include <cstring>
namespace ngp {
bool training() { return kTraining; }
static float fast_tanh(float x) {
    if (x > 4.97f) return 1.0f;
    if (x < -4.97f) return -1.0f;
    const float x2 = x * x;
    return x * (135135.0f + x2 * (17325.0f + x2 * (378.0f + x2))) /
        (135135.0f + x2 * (62370.0f + x2 * (3150.0f + x2 * 28.0f)));
}
float residual(const float* f) {
    float out = kWeights[320];
    float hidden[16];
    for (int j = 0; j < 16; ++j) hidden[j] = kWeights[288 + j];
    for (int i = 0; i < 18; ++i) {
        const float x = f[i] < -8.0f ? -8.0f : f[i] > 8.0f ? 8.0f : f[i];
        for (int j = 0; j < 16; ++j) hidden[j] += kWeights[i * 16 + j] * x;
    }
    for (int j = 0; j < 16; ++j) out += kWeights[304 + j] * fast_tanh(hidden[j]);
    return 4.0f * fast_tanh(out / 4.0f);
}
float uniform(int slot) {
    static std::uint32_t rng = 0;
    if (!rng) rng = kSeed ^ (2654435761u * static_cast<std::uint32_t>(slot + 1));
    rng = rng * 1664525u + 1013904223u;
    return static_cast<float>(rng >> 8) / 16777216.0f;
}
static void hex_record(const char* tag, const void* bytes, int count) {
    const unsigned char* b = static_cast<const unsigned char*>(bytes);
    const char* digits = "0123456789abcdef";
    char output[1400]; int at = 0;
    while (*tag) output[at++] = *tag++;
    for (int i = 0; i < count; ++i) {
        output[at++] = digits[b[i] >> 4]; output[at++] = digits[b[i] & 15];
    }
    output[at++] = '\n'; std::fwrite(output, 1, at, stdout);
}
void trace(std::uint32_t champion, int round, int n, int pick, float logp, const float* obs) {
    if (!kTraining) return;
    // Fixed little-endian Wasm record: five u32s, old log probability, 8x18 features.
    unsigned char record[600];
    const std::uint32_t header[5] = {1u, champion, static_cast<std::uint32_t>(round),
        static_cast<std::uint32_t>(n), static_cast<std::uint32_t>(pick)};
    std::memcpy(record, header, 20); std::memcpy(record + 20, &logp, 4);
    std::memcpy(record + 24, obs, 576); hex_record("NGP1 ", record, 600);
}
void map_trace(const float* f) {
    if (kTraining) hex_record("NGPMAP ", f, 64);
}
}
