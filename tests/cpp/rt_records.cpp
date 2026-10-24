// rt_records.cpp (agent B) - writes NFS1 records with known synthetic content for the C++ -> Python decoder round
// trip (tests/python/test_rt_records.py checks every field against the same generator).
#include <cstdio>

#include "nn_log.h"
#include "nn_rt.h"

int main() {
    nnrt::SplitMix64 r{424242};
    // Episode start.
    nnlog::enqueue_episode(0xA1B2C3D4u, 1, 7, nnlog::kEpisodeStart, 1, 2026102401u, 0x0123456789ABCDEFull, 0xFEEDu);
    nnlog::flush_all();
    // Turn context with 37 raw bytes (odd length exercises base64 padding).
    unsigned char raw[37];
    for (int i = 0; i < 37; ++i) raw[i] = static_cast<unsigned char>(i * 7 + 3);
    nnlog::enqueue_turn_context(0xA1B2C3D4u, 2, 7, raw, 37);
    nnlog::flush_all();
    // Decisions for K = 1..16 with F = 1 + K % 24.
    for (int K = 1; K <= 16; ++K) {
        const int F = 1 + (K * 5) % 24;
        float prior[16], feat[16 * 24], logit[16];
        std::uint8_t legal[16];
        std::uint32_t id[16];
        for (int k = 0; k < K; ++k) {
            prior[k] = -0.25f * k;
            legal[k] = k == 0 || (k % 3) != 1;
            id[k] = 1000u * K + k;
            logit[k] = legal[k] ? r.uniform() : nnrt::kNegInf;
        }
        for (int i = 0; i < K * F; ++i) feat[i] = r.uniform() * 2.0f - 1.0f;
        int chosen = K - 1;
        while (!legal[chosen]) --chosen;
        nnlog::DecisionRec rec{0xA1B2C3D4u, -5 + K, 7, static_cast<std::uint16_t>(K % 13), static_cast<std::uint16_t>(K),
                               static_cast<std::uint16_t>(F), static_cast<std::int16_t>(chosen), 2, 0, static_cast<std::uint8_t>(K % 4),
                               1, -0.5f * K, prior, legal, id, feat, 0xBEEF0000u + K, static_cast<std::uint16_t>(K * 3),
                               static_cast<std::int16_t>(K / 2), logit};
        nnlog::enqueue_decision(rec);
        nnlog::flush_all();
    }
    // Oversized payload is dropped, not truncated.
    static unsigned char big[nnlog::kMaxPayload];
    const bool ok = nnlog::enqueue_turn_context(0, 0, 0, big, sizeof big);
    std::printf("dropped=%u written=%u oversize_ok=%d\n", nnlog::g_dropped, nnlog::g_written, ok ? 1 : 0);
    return 0;
}
