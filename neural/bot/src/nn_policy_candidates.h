// Direct-policy v2: SDK-independent candidate data, deterministic normalization and canonical IDs.
// No teacher preference, prior, or index-zero convention. Features are described by schemas/policy_v2.json.
#pragma once
#include <cstdint>
#include "nn_config.h"

namespace nnpc {
inline constexpr int kF = 12, kMaxK = 16;
inline constexpr unsigned kInterpretationVersion = 2;
struct Candidate { std::uint32_t id; std::uint8_t legal; float raw[kF]; };
struct Decision {
    nncfg::H head;
    int K = 0, F = kF;
    std::uint8_t context = 0;
    float feat[kMaxK * kF];
    std::uint8_t legal[kMaxK];
    std::uint32_t id[kMaxK];
};
enum class Error : std::uint8_t {
    ok = 0, unsupported_head = 1, bad_count = 2, bad_context = 3, duplicate_id = 4,
    bad_mask = 5, non_finite = 6, empty = 7, no_legal = 8
};
struct FeatureSpec { float inv_scale, lo, hi; };
// BEGIN GENERATED
// GENERATED from schemas/policy_v2.json by agents/v2_candidates/generate_schema.py.
inline constexpr std::uint32_t kActionSchemaHash = 0x16DF3B9Eu;
inline constexpr std::uint32_t kHeadActionHash[13] = {0u,0x30DEC85Fu,0xD07E6450u,0x19389322u,0x221371AAu,0x15BEC187u,0x5BD56300u,0xD08E531Bu,0xE6375C5Fu,0u,0u,0u,0u};
inline constexpr FeatureSpec kFeatureSpec[9][kF] = {
    {}, // no direct draft head; inherited draft remains separate
    {{1.0f/6.0f,0.0f,1.0f},{1.0f/1.0f,0.0f,1.0f},{1.0f/100.0f,0.0f,8.0f},{1.0f/1000.0f,0.0f,8.0f},{1.0f/2000.0f,0.0f,1.0f},{1.0f/50.0f,0.0f,4.0f},{1.0f/6.0f,0.0f,1.0f},{1.0f/6.0f,0.0f,1.0f},{1.0f/100.0f,-4.0f,4.0f},{1.0f/1000.0f,-4.0f,4.0f},{1.0f/100.0f,0.0f,8.0f},{1.0f/1000.0f,0.0f,4.0f}}, // strategy
    {{1.0f/16.0f,-4.0f,4.0f},{1.0f/16.0f,-4.0f,4.0f},{1.0f/50.0f,0.0f,4.0f},{1.0f/100.0f,0.0f,8.0f},{1.0f/1000.0f,0.0f,8.0f},{1.0f/5000.0f,0.0f,4.0f},{1.0f/100.0f,0.0f,8.0f},{1.0f/100.0f,0.0f,4.0f},{1.0f/200.0f,0.0f,4.0f},{1.0f/6.0f,0.0f,1.0f},{1.0f/6.0f,0.0f,1.0f},{1.0f/100.0f,0.0f,4.0f}}, // objective
    {{1.0f/4.0f,0.0f,1.0f},{1.0f/5.0f,0.0f,1.0f},{1.0f/1.0f,0.0f,1.0f},{1.0f/100.0f,0.0f,8.0f},{1.0f/1000.0f,0.0f,8.0f},{1.0f/10.0f,0.0f,2.0f},{1.0f/6.0f,0.0f,1.0f},{1.0f/6.0f,0.0f,1.0f},{1.0f/50.0f,0.0f,4.0f},{1.0f/6.0f,0.0f,1.0f},{1.0f/1000.0f,-4.0f,4.0f},{1.0f/2000.0f,0.0f,1.0f}}, // role
    {{1.0f/2.0f,0.0f,1.0f},{1.0f/16.0f,-4.0f,4.0f},{1.0f/16.0f,-4.0f,4.0f},{1.0f/50.0f,0.0f,4.0f},{1.0f/100.0f,0.0f,8.0f},{1.0f/1000.0f,-4.0f,4.0f},{1.0f/2000.0f,0.0f,1.0f},{1.0f/1.0f,0.0f,1.0f},{1.0f/6.0f,0.0f,1.0f},{1.0f/1000.0f,0.0f,4.0f},{1.0f/20.0f,0.0f,4.0f},{1.0f/1.0f,-1.0f,1.0f}}, // bank
    {{1.0f/2.0f,0.0f,1.0f},{1.0f/42.0f,0.0f,4.0f},{1.0f/1000.0f,0.0f,8.0f},{1.0f/1000.0f,0.0f,8.0f},{1.0f/5.0f,0.0f,4.0f},{1.0f/1000.0f,0.0f,4.0f},{1.0f/100.0f,0.0f,4.0f},{1.0f/100.0f,0.0f,4.0f},{1.0f/1000.0f,0.0f,4.0f},{1.0f/100.0f,0.0f,4.0f},{1.0f/2000.0f,0.0f,1.0f},{1.0f/5.0f,0.0f,4.0f}}, // shop
    {{1.0f/8.0f,-4.0f,4.0f},{1.0f/8.0f,-4.0f,4.0f},{1.0f/50.0f,0.0f,4.0f},{1.0f/50.0f,0.0f,4.0f},{1.0f/6.0f,0.0f,1.0f},{1.0f/6.0f,0.0f,1.0f},{1.0f/1.0f,0.0f,1.0f},{1.0f/16.0f,0.0f,4.0f},{1.0f/16.0f,0.0f,4.0f},{1.0f/3.0f,0.0f,1.0f},{1.0f/20.0f,0.0f,4.0f},{1.0f/100.0f,0.0f,8.0f}}, // move
    {{1.0f/3.0f,0.0f,1.0f},{1.0f/1000.0f,0.0f,4.0f},{1.0f/1000.0f,0.0f,4.0f},{1.0f/100.0f,0.0f,8.0f},{1.0f/16.0f,0.0f,4.0f},{1.0f/1.0f,0.0f,1.0f},{1.0f/100.0f,0.0f,8.0f},{1.0f/100.0f,0.0f,8.0f},{1.0f/1000.0f,0.0f,4.0f},{1.0f/20.0f,0.0f,4.0f},{1.0f/20.0f,0.0f,4.0f},{1.0f/6.0f,0.0f,1.0f}}, // combat
    {{1.0f/2.0f,0.0f,1.0f},{1.0f/1.0f,0.0f,1.0f},{1.0f/1.0f,0.0f,1.0f},{1.0f/1000.0f,0.0f,8.0f},{1.0f/1000.0f,0.0f,8.0f},{1.0f/100.0f,0.0f,8.0f},{1.0f/100.0f,0.0f,8.0f},{1.0f/16.0f,0.0f,4.0f},{1.0f/50.0f,0.0f,4.0f},{1.0f/100.0f,0.0f,8.0f},{1.0f/2.0f,0.0f,1.0f},{1.0f/1000.0f,0.0f,4.0f}}, // engage
};
// END GENERATED
constexpr bool supported(nncfg::H head) { const int h = static_cast<int>(head); return h >= 1 && h <= 8; }
constexpr std::uint32_t action_hash(nncfg::H head) { return supported(head) ? kHeadActionHash[static_cast<int>(head)] : 0; }

// Caller must admit complete candidate construction+normalization+inference BEFORE filling raw rows.
// count>16 and duplicates reject, never truncate/reorder around a teacher. Error leaves K=0.
Error build(nncfg::H head, const Candidate* rows, int count, std::uint8_t context, Decision& out);
// Collection-only annotation. -1 means absent, missing, masked or unrepresentable. No influence on build().
int teacher_index(const Decision& decision, std::int64_t stable_action_id = -1);
// Stable composite IDs. Positions must already use the canonical team frame. No lossy bit masking.
bool move_id(unsigned kind, int canonical_x, int canonical_y, std::uint32_t& out);
bool combat_id(unsigned kind, std::uint32_t target_handle, std::uint32_t& out);
} // namespace nnpc
