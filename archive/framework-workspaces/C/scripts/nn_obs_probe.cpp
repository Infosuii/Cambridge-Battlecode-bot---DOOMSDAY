// SCRATCH-ONLY probe (agent C): never placed in bot/src. Copied into artifacts/tmp/C/probe/bot/src together with a
// patched bot.cpp that calls nnobs_probe() once per turn (after the world update and sighting exchange on living turns,
// before shopping on dead turns). Prints per-turn fuel of capture and encode plus a fingerprint of the encoded
// vector, and every 10th round the raw RawTurn bytes (base64) so Python can re-encode them and compare fingerprints.
#include <cstdio>

#include "bot.h"
#include "nn_obs.h"

namespace {
nnobs::RawTurn g_raw;
float g_x[nnobs::kObsDim];
char g_b64[(sizeof(nnobs::RawTurn) + 2) / 3 * 4 + 1];
bool g_told = false;

void b64(const unsigned char* p, std::size_t n, char* out) {
    static const char* t = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::size_t o = 0;
    for (std::size_t i = 0; i < n; i += 3) {
        const unsigned v = (unsigned{p[i]} << 16) | (i + 1 < n ? unsigned{p[i + 1]} << 8 : 0u) | (i + 2 < n ? unsigned{p[i + 2]} : 0u);
        out[o++] = t[(v >> 18) & 63];
        out[o++] = t[(v >> 12) & 63];
        out[o++] = i + 1 < n ? t[(v >> 6) & 63] : '=';
        out[o++] = i + 2 < n ? t[v & 63] : '=';
    }
    out[o] = 0;
}
} // namespace

void nnobs_probe(const Bot& bot, int where) {
    if (!g_told) {
        g_told = true;
        const std::uint64_t a = bc::fuel_remaining();
        const std::uint64_t b = bc::fuel_remaining();
        std::printf("NOBSINFO dim %d raw %u hash %08x shared_memory_bytes %u draft_memory_bytes %u meter %llu\n", nnobs::kObsDim,
            static_cast<unsigned>(sizeof(nnobs::RawTurn)), nnobs::kObsSchemaHash, bc::constants::shared_memory_bytes,
            bc::constants::draft_memory_bytes, static_cast<unsigned long long>(a - b));
    }
    const std::uint64_t f0 = bc::fuel_remaining();
    const bool ok = nnobs::capture(bot, g_raw);
    const std::uint64_t f1 = bc::fuel_remaining();
    if (!ok) {
        std::printf("NOBS %u x %d nocapture\n", bc::round_number(), where);
        return;
    }
    nnobs::encode(g_raw, g_x);
    const std::uint64_t f2 = bc::fuel_remaining();
    const std::uint32_t h = nnobs::obs_hash(g_x, nnobs::kObsDim);
    std::printf("NOBS %d %u %d %llu %llu %llu %08x\n", g_raw.round, g_raw.my_handle, where, static_cast<unsigned long long>(f0 - f1),
        static_cast<unsigned long long>(f1 - f2), static_cast<unsigned long long>(f2), h);
    if (g_raw.round <= 3 || g_raw.round % 10 == 0) {
        b64(reinterpret_cast<const unsigned char*>(&g_raw), sizeof(g_raw), g_b64);
        std::printf("NRAW %d %u %08x %s\n", g_raw.round, g_raw.my_handle, h, g_b64);
    }
}
