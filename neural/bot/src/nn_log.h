// nn_log.h (agent B) - NFS1 training records on stdout (CONTRACTS 3.5; exact layout: agents/B/RECORD_FORMAT.md,
// decoder: python/nfs/records.py). Only used when nncfg::kTraining.
//
// Fuel design (measured, models/budget.json): building a payload is a few memcpy (cheap) and happens inside the turn
// (enqueue_*); base64 encoding + fwrite costs ~8 fuel/byte and is deferred to nnh::idle() at the END of the turn,
// after the teacher has finished, using only leftover fuel (flush_one / flush_all). So logging never changes the
// teacher's in-turn fuel view. Records that do not fit the bounded queue are dropped and counted (episode markers).
// One record = one line "NFS1 <base64(payload)>\n" written with a single fwrite. Payload little-endian, packed:
//   u32 magic 0x3153464E | u16 version 1 | u16 kind | u32 schema_hash | i32 round | u32 champion | kind-specific.
// Pure (stdio only): compiles natively for the round-trip test.
#pragma once
#include <cstdint>
#include <cstdio>
#include <cstring>

namespace nnlog {

inline constexpr std::uint32_t kMagic = 0x3153464Eu; // bytes "NFS1"
inline constexpr std::uint16_t kVersion = 1;
enum Kind : std::uint16_t { kTurnContext = 0, kDecision = 1, kEpisode = 2 };
enum Event : std::uint16_t { kEpisodeStart = 0, kEpisodeHeartbeat = 1 };

inline constexpr int kMaxPayload = 8192;
inline constexpr int kMaxText = 5 + (kMaxPayload + 2) / 3 * 4 + 2;
inline constexpr int kQueueBytes = 49152;

inline unsigned char g_payload[kMaxPayload];
inline char g_text[kMaxText];
inline unsigned char g_queue[kQueueBytes];
inline int g_qhead = 0, g_qtail = 0;
inline std::uint32_t g_dropped = 0; // records not written (payload overflow or queue full)
inline std::uint32_t g_written = 0; // records written to stdout
inline std::uint32_t g_queued = 0;  // records accepted into the queue

// Base64 via a 4096-entry table of character pairs (12 bits -> 2 chars, little-endian u16).
inline constexpr char kAlpha[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
struct B64Pairs {
    std::uint16_t v[4096];
};
constexpr B64Pairs make_pairs() {
    B64Pairs t{};
    for (int i = 0; i < 4096; ++i)
        t.v[i] = static_cast<std::uint16_t>(static_cast<unsigned char>(kAlpha[i >> 6]) |
                                            (static_cast<unsigned>(static_cast<unsigned char>(kAlpha[i & 63])) << 8));
    return t;
}
inline constexpr B64Pairs kPairs = make_pairs();

struct Writer {
    int n = 0;
    bool overflow = false;
    void raw(const void* p, int len) {
        if (overflow || len < 0 || n + len > kMaxPayload) {
            overflow = true;
            return;
        }
        std::memcpy(g_payload + n, p, static_cast<unsigned>(len)); // wasm32 and x86-64 are little-endian
        n += len;
    }
    void u8(std::uint8_t v) { raw(&v, 1); }
    void u16(std::uint16_t v) { raw(&v, 2); }
    void i16(std::int16_t v) { raw(&v, 2); }
    void u32(std::uint32_t v) { raw(&v, 4); }
    void i32(std::int32_t v) { raw(&v, 4); }
    void u64(std::uint64_t v) { raw(&v, 8); }
    void f32(float v) { raw(&v, 4); }
    void header(Kind kind, std::uint32_t schema_hash, std::int32_t round, std::uint32_t champion) {
        u32(kMagic);
        u16(kVersion);
        u16(kind);
        u32(schema_hash);
        i32(round);
        u32(champion);
    }
};

// Base64 (RFC 4648, '=' padded) of p[0, n) into g_text after the "NFS1 " tag; returns the line length.
inline int encode_line_from(const unsigned char* p, int n) {
    char* o = g_text;
    std::memcpy(o, "NFS1 ", 5);
    o += 5;
    int i = 0;
    for (; i + 3 <= n; i += 3) {
        const std::uint32_t v = (std::uint32_t(p[i]) << 16) | (std::uint32_t(p[i + 1]) << 8) | p[i + 2];
        const std::uint32_t w = kPairs.v[v >> 12] | (std::uint32_t(kPairs.v[v & 4095]) << 16);
        std::memcpy(o, &w, 4);
        o += 4;
    }
    if (n - i == 1) {
        const std::uint32_t v = std::uint32_t(p[i]) << 16;
        *o++ = kAlpha[(v >> 18) & 63], *o++ = kAlpha[(v >> 12) & 63], *o++ = '=', *o++ = '=';
    } else if (n - i == 2) {
        const std::uint32_t v = (std::uint32_t(p[i]) << 16) | (std::uint32_t(p[i + 1]) << 8);
        *o++ = kAlpha[(v >> 18) & 63], *o++ = kAlpha[(v >> 12) & 63], *o++ = kAlpha[(v >> 6) & 63], *o++ = '=';
    }
    *o++ = '\n';
    return static_cast<int>(o - g_text);
}
inline int encode_line(int n) { return encode_line_from(g_payload, n); }

// Append the payload built in g_payload to the queue (u32 length prefix). Compacts when the head has advanced.
inline bool enqueue(const Writer& w) {
    if (w.overflow) {
        ++g_dropped;
        return false;
    }
    const int need = 4 + w.n;
    if (g_qtail + need > kQueueBytes && g_qhead > 0) {
        const int live = g_qtail - g_qhead;
        std::memmove(g_queue, g_queue + g_qhead, static_cast<unsigned>(live));
        g_qhead = 0, g_qtail = live;
    }
    if (g_qtail + need > kQueueBytes) {
        ++g_dropped;
        return false;
    }
    const std::uint32_t len = static_cast<std::uint32_t>(w.n);
    std::memcpy(g_queue + g_qtail, &len, 4);
    std::memcpy(g_queue + g_qtail + 4, g_payload, static_cast<unsigned>(w.n));
    g_qtail += need;
    ++g_queued;
    return true;
}

inline bool queue_empty() { return g_qhead >= g_qtail; }
inline int next_bytes() {
    if (queue_empty()) return 0;
    std::uint32_t len;
    std::memcpy(&len, g_queue + g_qhead, 4);
    return static_cast<int>(len);
}

// Encode and write the oldest queued record. False when the queue is empty.
inline bool flush_one(std::FILE* out = stdout) {
    if (queue_empty()) return false;
    const int len = next_bytes();
    const int line = encode_line_from(g_queue + g_qhead + 4, len);
    std::fwrite(g_text, 1, static_cast<unsigned>(line), out);
    g_qhead += 4 + len;
    if (g_qhead >= g_qtail) g_qhead = g_qtail = 0;
    ++g_written;
    return true;
}
inline int flush_all(std::FILE* out = stdout) {
    int n = 0;
    while (flush_one(out)) ++n;
    return n;
}

struct DecisionRec {
    std::uint32_t schema_hash; // observation schema hash of the shared context
    std::int32_t round;
    std::uint32_t champion;
    std::uint16_t head, K, F;
    std::int16_t chosen;
    std::uint8_t mode, reason, context, sampled;
    float logp;
    const float* prior;        // K
    const std::uint8_t* legal; // K
    const std::uint32_t* id;   // K
    const float* feat;         // K x F
    // v1 trailer (after feat): u32 action_hash, u16 call_index, i16 net, f32 logit[K]
    std::uint32_t action_hash;
    std::uint16_t call;
    std::int16_t net;
    const float* logit; // K (-inf for illegal); may be null -> zeros are written
};

inline int decision_bytes(int K, int F) { return 20 + 18 + K * 9 + K * F * 4 + 8 + K * 4; }

inline bool enqueue_decision(const DecisionRec& r) {
    Writer w;
    w.header(kDecision, r.schema_hash, r.round, r.champion);
    w.u16(r.head), w.u16(r.K), w.u16(r.F), w.i16(0), w.i16(r.chosen);
    w.u8(r.mode), w.u8(r.reason), w.u8(r.context), w.u8(r.sampled);
    w.f32(r.logp);
    w.raw(r.prior, 4 * r.K);
    w.raw(r.legal, r.K);
    w.raw(r.id, 4 * r.K);
    w.raw(r.feat, 4 * r.K * r.F);
    w.u32(r.action_hash), w.u16(r.call), w.i16(r.net);
    if (r.logit)
        w.raw(r.logit, 4 * r.K);
    else
        for (int k = 0; k < r.K; ++k) w.f32(0.0f);
    return enqueue(w);
}

// Turn context: the raw nnobs::RawTurn bytes (schema-hashed by the header).
inline bool enqueue_turn_context(std::uint32_t schema_hash, std::int32_t round, std::uint32_t champion,
                                 const void* raw, std::uint32_t bytes) {
    Writer w;
    w.header(kTurnContext, schema_hash, round, champion);
    w.u32(bytes);
    w.raw(raw, static_cast<int>(bytes));
    return enqueue(w);
}

// Episode marker: u16 event, u16 flags (bit0 training, bit1 fuel credit), u32 seed, u64 model checksum,
// u32 records written so far, u32 records dropped so far, u32 profile hash.
inline bool enqueue_episode(std::uint32_t schema_hash, std::int32_t round, std::uint32_t champion,
                            std::uint16_t event, std::uint16_t flags, std::uint32_t seed, std::uint64_t model_checksum,
                            std::uint32_t profile_hash) {
    Writer w;
    w.header(kEpisode, schema_hash, round, champion);
    w.u16(event), w.u16(flags), w.u32(seed), w.u64(model_checksum), w.u32(g_written), w.u32(g_dropped);
    w.u32(profile_hash);
    return enqueue(w);
}

} // namespace nnlog
