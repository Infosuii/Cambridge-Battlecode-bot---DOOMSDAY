// jd_mem.h (JD_MEM, FEAT-002): pure codec for the team's 8-byte shared word and owner/merge rules for the 1,024-byte
// draft buffer. No cambc.h dependency, so host fixtures (tools/jd_g5070-1104/tests/mem_test.cpp) test exactly the
// code the bot runs. Schema: research/jd-g5070-1104/MEMORY_SCHEMA.md. This header encodes the CURRENT (v92) schema;
// it adds no new fields.
#pragma once

#include <cstddef>
#include <cstdint>

namespace jdmem {

// ------------------------------------------------------------------------------------------------- shared word
// bits 0-41 six 7-bit claim slots (slot = index in bc::champions(ally)); sighting form (bit 63 clear): x 42-48,
// y 49-55, round mod 64 56-61, distress 62; event form (bit 63 set): group 42-48, respawn-ready round mod 256 49-56.
inline constexpr int kClaimBits = 7, kClaimSlots = 6;
inline constexpr int kSightX = 42, kSightY = 49, kSightRound = 56, kDistressBit = 62, kEventBit = 63;
inline constexpr std::uint64_t kClaimMask = 127, kSightRoundMask = 63;
inline constexpr std::uint64_t kCodeDead = 126, kCodeIdle = 127;
inline constexpr int kOnsiteBase = 64, kOnsiteGroups = 48; // V54_ONSITE: 64 + g = "claims g and is on site", g < 48
inline constexpr int kOrderBase = 112, kOrderLast = 118;   // fight orders: 112 + k engage enemy k (k < 6), 118 retreat
inline constexpr int kOrderMaxGroups = 112;                // orders are written and read only with < 112 groups
inline constexpr std::uint64_t kClaimField = (std::uint64_t{1} << (kClaimBits * kClaimSlots)) - 1; // bits 0-41
inline constexpr std::uint64_t kTopField = ~kClaimField;                                          // bits 42-63
inline constexpr int kSightAgeLimit = 10; // read_sighting ignores older sightings

// The word a first writer starts from (write_claim on an all-zero word): every slot idle, no sighting.
constexpr std::uint64_t all_idle() { return kClaimField; }

constexpr std::uint64_t get_code(std::uint64_t w, int slot) {
    return slot < 0 || slot >= kClaimSlots ? kCodeIdle : (w >> (slot * kClaimBits)) & kClaimMask;
}

// Replace one slot's code; every other bit (other slots, sighting/event, distress) is preserved.
constexpr std::uint64_t set_code(std::uint64_t w, int slot, std::uint64_t code) {
    if (slot < 0 || slot >= kClaimSlots) return w;
    w &= ~(kClaimMask << (slot * kClaimBits));
    return w | ((code & kClaimMask) << (slot * kClaimBits));
}

// write_claim's encoding. group: >= 0 a camp group, -1 none, -2 dead (bot.h kClaimDead). A group that has no code
// (>= 126) is published as idle: dropped, never aliased to another group's code.
constexpr std::uint64_t claim_code(int group, bool onsite, bool onsite_ok) {
    if (group == -2) return kCodeDead;
    if (group < 0 || group >= static_cast<int>(kCodeDead)) return kCodeIdle;
    if (onsite && onsite_ok && group < kOnsiteGroups) return static_cast<std::uint64_t>(kOnsiteBase + group);
    return static_cast<std::uint64_t>(group);
}

enum class Kind : std::uint8_t { idle, dead, group, order };
struct Claim {
    Kind kind;
    int group;   // camp group for Kind::group, enemy index (0-5) or 6 = retreat for Kind::order, else -1
    bool onsite; // V54_ONSITE mark
};

// decode_claims' reading, plus the order codes that tactics reads in the same slots (only with < 112 groups).
constexpr Claim decode_code(std::uint64_t code, bool onsite_ok, int ngroups) {
    const int c = static_cast<int>(code & kClaimMask);
    if (c == static_cast<int>(kCodeIdle)) return {Kind::idle, -1, false};
    if (c == static_cast<int>(kCodeDead)) return {Kind::dead, -1, false};
    if (onsite_ok && c >= kOnsiteBase && c < kOnsiteBase + kOnsiteGroups) return {Kind::group, c - kOnsiteBase, true};
    if (ngroups < kOrderMaxGroups && c >= kOrderBase && c <= kOrderLast) return {Kind::order, c - kOrderBase, false};
    return {Kind::group, c, false};
}

// True when `group` survives encode/decode as itself on a map with `ngroups` groups (onsite_ok = ngroups <= 48).
constexpr bool representable(int group, int ngroups) {
    if (group < 0 || group >= ngroups || group >= static_cast<int>(kCodeDead)) return false;
    const bool onsite_ok = ngroups <= kOnsiteGroups;
    const Claim c = decode_code(claim_code(group, false, onsite_ok), onsite_ok, ngroups);
    return c.kind == Kind::group && c.group == group && !c.onsite;
}

// --- sighting form
constexpr bool is_event(std::uint64_t w) { return (w >> kEventBit) & 1; }

constexpr std::uint64_t set_sighting(std::uint64_t w, int x, int y, int round, bool distress) {
    w &= kClaimField;
    w |= static_cast<std::uint64_t>(x & 127) << kSightX;
    w |= static_cast<std::uint64_t>(y & 127) << kSightY;
    w |= static_cast<std::uint64_t>(round & static_cast<int>(kSightRoundMask)) << kSightRound;
    if (distress) w |= std::uint64_t{1} << kDistressBit;
    return w;
}

// Age by the current rule: (round - published round) mod 64. Wraps after 64 rounds.
constexpr int sighting_age_mod64(std::uint64_t w, int round) {
    int age = (round & static_cast<int>(kSightRoundMask)) - static_cast<int>((w >> kSightRound) & kSightRoundMask);
    if (age < 0) age += static_cast<int>(kSightRoundMask) + 1;
    return age;
}

struct Sighting {
    bool present;
    int x, y, age;
    bool distress;
};
// read_sighting's rule (bot.cpp), event words excluded: nothing published = all of bits 42-63 zero.
constexpr Sighting read_sighting(std::uint64_t w, int round) {
    if (is_event(w) || (w >> kSightX) == 0) return {false, 0, 0, 0, false};
    const int age = sighting_age_mod64(w, round);
    return {age <= kSightAgeLimit, static_cast<int>((w >> kSightX) & 127), static_cast<int>((w >> kSightY) & 127), age,
        ((w >> kDistressBit) & 1) != 0};
}

// JD_SIGHTAGE: a reader that remembers the sighting field it last saw and when; an unchanged field keeps ageing
// with the reader's own clock instead of reading fresh again 64 rounds later. Readers read every live turn.
struct SightClock {
    std::uint64_t field = 0;
    int first_round = -1, first_age = 0;
    constexpr int age(std::uint64_t w, int round) {
        const std::uint64_t f = (w & kTopField) & ~(std::uint64_t{1} << kEventBit);
        if (first_round >= 0 && f == field) return first_age + (round - first_round);
        field = f, first_round = round, first_age = sighting_age_mod64(w, round);
        return first_age;
    }
};

// --- event form (APEX_EVENTS): a teammate learned group g's respawn-ready round.
constexpr std::uint64_t set_event(std::uint64_t w, int group, int ready_round) {
    w &= kClaimField;
    w |= static_cast<std::uint64_t>(group & 127) << kSightX;
    w |= static_cast<std::uint64_t>(ready_round & 255) << kSightY;
    w |= std::uint64_t{1} << kEventBit;
    return w;
}
constexpr int event_group(std::uint64_t w) { return static_cast<int>((w >> kSightX) & 127); }
// read_sighting's decode: the ready round in [round - 64, round + 192).
constexpr int event_ready(std::uint64_t w, int round) {
    const int mod = static_cast<int>((w >> kSightY) & 255);
    const int base = round - 64;
    return base + ((mod - base) % 256 + 256) % 256;
}

// JD_EVTONCE: apply each distinct event word once per reader (the publisher's teammates all read it within a
// round); a later re-read of the same unchanged word is stale and is what decodes as a phantom future respawn.
// A decoded ready round more than `horizon` rounds ahead (no camp respawns later) is also rejected.
struct EventOnce {
    std::uint64_t last = 0;
    bool have = false;
    constexpr bool accept(std::uint64_t w, int round, int horizon) {
        const std::uint64_t ev = w & kTopField;
        if (have && ev == last) return false;
        last = ev, have = true;
        return event_ready(w, round) <= round + horizon;
    }
};

// ------------------------------------------------------------------------------------------------ draft buffer
// Regions of the 1,024-byte team draft buffer (strategy.h, draft.cpp, economy.cpp). Byte 6 is unused.
inline constexpr std::size_t kDraftBytes = 1024;
enum Region : int { kBrain, kMlPlan, kDPlan, kRoster, kRegions };
struct RegionSpec {
    std::size_t off, len;
};
inline constexpr RegionSpec kRegion[kRegions] = {{0, 6}, {7, 1}, {8, 1000}, {1008, 8}};
inline constexpr std::uint8_t kBrainMagic = 0xA5, kRosterMagic = 0x58, kMlFlag = 0x80;

// Owner/merge: `host` holds the CURRENT host bytes (read with sdk_read_draft_memory, not the startup snapshot) and
// `host_len` of them are valid. Writes `n` bytes into `region` only and returns the prefix length to submit (the
// region's end), so the prefix submit carries the other regions' current bytes unchanged and leaves bytes past the
// prefix untouched on the host. Returns 0 (submit nothing) when the payload does not fit its region or the host buffer.
constexpr std::size_t merge(std::uint8_t* host, std::size_t host_len, Region r, const std::uint8_t* bytes, std::size_t n) {
    if (r < 0 || r >= kRegions) return 0;
    const RegionSpec s = kRegion[r];
    if (n > s.len || s.off + n > host_len || s.off + n > kDraftBytes) return 0;
    for (std::size_t i = 0; i < n; ++i) host[s.off + i] = bytes[i];
    return s.off + n;
}

struct Brain {
    bool valid;
    int team_size, enemy_casters, cls, max_group;
    bool race, mono;
};
// strategy.h brain::load's reading (magic + at least 4 bytes; bytes 4-5 optional), plus range checks it lacks.
constexpr Brain read_brain(const std::uint8_t* b, std::size_t len) {
    Brain r{false, 0, 0, -1, 0, false, false};
    if (len < 4 || b[0] != kBrainMagic) return r;
    r.team_size = b[1], r.enemy_casters = b[2], r.cls = b[3];
    if (len >= 5) r.max_group = b[4];
    if (len >= 6) r.race = (b[5] & 1) != 0, r.mono = (b[5] & 2) != 0;
    r.valid = r.team_size >= 1 && r.team_size <= 6 && r.cls >= 0 && r.cls <= 5;
    return r;
}
// strategy.h map_class: the class a header for this map and team size must carry.
constexpr int map_class(int w, int h, int team_size) {
    const int t = team_size < 3 ? 3 : (team_size > 5 ? 5 : team_size);
    return (t - 3) * 2 + (w * h > 2000 ? 1 : 0);
}

// Economy roster (V58_DIRECTOR): public draft picks expanded to physical bodies. Draft ids follow
// bc::champion_draft; body types follow bc::champion_type, where the Cassi+Issac pick (draft id 3) becomes the two
// bodies Cassi (3) and Issac (4) and draft ids above 3 shift by one. At most 6 bodies are recorded.
inline constexpr int kDraftCassiIssac = 3, kTypeCassi = 3, kTypeIssac = 4, kMaxBodies = 6;
constexpr int encode_roster(const int* picks, int npicks, std::uint8_t out[8]) {
    for (int i = 0; i < 8; ++i) out[i] = 0;
    out[0] = kRosterMagic;
    int n = 0;
    for (int i = 0; i < npicks; ++i) {
        if (picks[i] == kDraftCassiIssac) {
            if (n < kMaxBodies) out[2 + n++] = kTypeCassi;
            if (n < kMaxBodies) out[2 + n++] = kTypeIssac;
        } else if (n < kMaxBodies) {
            out[2 + n++] = static_cast<std::uint8_t>(picks[i] > kDraftCassiIssac ? picks[i] + 1 : picks[i]);
        }
    }
    out[1] = static_cast<std::uint8_t>(n);
    return n;
}
// bot.cpp init's reading: needs 1016 bytes, the magic and a body count equal to this game's body count.
constexpr int read_roster(const std::uint8_t* b, std::size_t len, int bodies, int types[kMaxBodies]) {
    if (len < 1016 || b[1008] != kRosterMagic || static_cast<int>(b[1009]) != bodies || bodies > kMaxBodies) return 0;
    for (int s = 0; s < bodies; ++s) types[s] = b[1010 + s];
    return bodies;
}

// ML plan byte (A2_MLPLAN): 0x80 | plan (0-7) or absent.
constexpr int read_ml_plan(const std::uint8_t* b, std::size_t len) {
    return len >= 8 && (b[7] & kMlFlag) ? (b[7] & 7) : -1;
}

} // namespace jdmem
