// Canonical observation (agent C): the raw per-turn snapshot, the pure encoder and the canonical team frame.
// Pure part (this header, nn_obs.cpp): no cambc.h, compiles natively for parity tests (tests/cpp/obs_*.cpp).
// SDK part: nn_obs_glue.cpp (capture/observe). Layout constants come from the generated nn_schema.h.
//
// Contract (CONTRACTS.md 3.3): capture() fills RawTurn once per (champion, round) from already-computed Bot/World
// state; encode() is a pure function RawTurn -> float[kObsDim]:
//   [self_global | ally rows | ally mask | enemy rows | enemy mask]
// Padded rows are all zero with mask 0. Rows are sorted inside encode (visible, known, distance, handle), so the
// RawTurn row order never changes the output. Every value is clip(raw * inv_scale) with non-finite -> 0.
#pragma once
#include <cstddef>
#include <cstdint>
#include <type_traits>

#include "nn_schema.h"

class Bot;

namespace nnobs {

// One objective slot: slot 0 = the teacher's target group, 1..3 = nearest other groups (World::groups memory).
struct ObjRaw {
    std::int32_t valid, group, anchor_x, anchor_y;
    std::int32_t dist_walk; // walking tiles from self via World::group_dist; -1 no field, -2 unreachable
    std::int32_t dist_cheb; // Chebyshev tiles from self to the anchor camp
    std::int32_t gems, gold, state /*0 alive 1 reward 2 respawning*/, respawn_in, harmless, ally_claims;
    std::int32_t enemy_age; // rounds since an enemy was seen near it; -1 never
    float hp_left, max_hp;
};

// One teammate (never self). Last-seen fields are valid when known != 0.
struct AllyRaw {
    std::int32_t present;
    std::uint32_t handle;
    std::int32_t slot, type, alive, visible, known, age, x, y, range;
    std::int32_t gems;       // -1 unknown
    std::int32_t claim_code; // shared-memory claim slot code (0..127), -1 none (slot >= kClaimSlots)
    std::int32_t claim_dist; // walking tiles from the ally's last position to its claimed group; -1 unknown
    std::int32_t claim_gems;
    float hp, max_hp, strength, focus;
};

// One enemy body. Last-seen fields are valid when known != 0 (own observation; never another team's state).
struct EnemyRaw {
    std::int32_t present;
    std::uint32_t handle;
    std::int32_t type, alive, visible, known, age, x, y, range, gems, state_bits;
    float hp, max_hp, strength, focus;
};

// Everything the encoder needs, POD, fixed size, little-endian 4-byte fields (training records carry it raw).
struct RawTurn {
    std::uint32_t magic, version, schema_hash, size;
    std::int32_t round, max_rounds, winning_gems, abs_team;
    std::uint32_t my_handle;
    std::int32_t slot, team_size, enemy_count;
    std::int32_t width, height, symmetry, n_groups, fields_built, altar_ready, enemy_ready;
    std::int32_t own_spawn_x0, own_spawn_y0, own_spawn_x1, own_spawn_y1; // inclusive bounding boxes
    std::int32_t enemy_spawn_x0, enemy_spawn_y0, enemy_spawn_x1, enemy_spawn_y1;
    // self
    std::int32_t alive, pos_x, pos_y, gems, gold, attack_range, type, state_bits, cast_done, heading_home, target_group;
    std::int32_t tribute_carry, ward_charges, ward_cooldown;
    std::int32_t spawn_dist, altar_dist, enemy_spawn_walk; // tiles; -1 unknown, -2 unreachable
    std::int32_t in_bush, on_own_spawn, in_hot_zone, in_enemy_zone;
    std::int32_t spell_present[2], spell_kind[2], spell_cooldown[2];
    float spell_range[2];
    float hp, max_hp, prev_hp, strength, focus, items, camp_taken_mult, camp_dealt_mult;
    // bounded history (glue ring buffers; ages are explicit, -1 = no sample old enough)
    std::int32_t hist10_age;
    float hist10_hp;
    std::int32_t hist10_gems;
    std::int32_t hist50_age, hist50_ally, hist50_enemy, hist200_age, hist200_ally, hist200_enemy;
    // global
    std::int32_t ally_score, enemy_score, alive_us, alive_them;
    std::int32_t ally_deaths_50, enemy_deaths_50, ally_deaths_total, enemy_deaths_total;
    std::int32_t vis_enemies, vis_allies, sight_n5, sight_n20, sight_x, sight_y, sight_age /*-1 none*/;
    std::int32_t distress_x, distress_y, distress_age /*-1 none*/, enemy_wards;
    ObjRaw obj[kObjSlots];
    AllyRaw ally[kAllyRows];
    EnemyRaw enemy[kEnemyRows];
};

NNOBS_RAW_LAYOUT_CHECK(RawTurn, ObjRaw, AllyRaw, EnemyRaw)
static_assert(std::is_trivially_copyable_v<RawTurn> && std::is_standard_layout_v<RawTurn>);

// ---------------------------------------------------------------- canonical frame (pure, inline)
// Symmetry values follow cambc::symmetry: 0 horizontal (x reversed), 1 vertical (y reversed), 2 rotational180.
struct Frame {
    std::int64_t w = 0, h = 0;
    int sym = -1;
    bool flip = false, fx = false, fy = false; // fx: x is mirrored, fy: y is mirrored
};

constexpr Frame make_frame(std::int64_t w, std::int64_t h, int sym, std::int64_t s2x, std::int64_t s2y, int abs_team) {
    // s2x/s2y = twice our spawn centre (x0 + x1 of the inclusive bounding box). See observation.json coordinate_frame.
    Frame f;
    f.w = w;
    f.h = h;
    f.sym = sym;
    const bool team_b = abs_team == 1;
    if (sym == 0) f.flip = s2x != w - 1 ? s2x > w - 1 : team_b;
    else if (sym == 1) f.flip = s2y != h - 1 ? s2y > h - 1 : team_b;
    else if (sym == 2) f.flip = s2x != w - 1 ? s2x > w - 1 : (s2y != h - 1 ? s2y > h - 1 : team_b);
    else f.flip = false;
    f.fx = f.flip && (sym == 0 || sym == 2);
    f.fy = f.flip && (sym == 1 || sym == 2);
    return f;
}
inline Frame frame_of(const RawTurn& r) {
    return make_frame(r.width, r.height, r.symmetry, std::int64_t{r.own_spawn_x0} + r.own_spawn_x1,
        std::int64_t{r.own_spawn_y0} + r.own_spawn_y1, r.abs_team);
}
constexpr std::int64_t canon_x(const Frame& f, std::int64_t x) { return f.fx ? f.w - 1 - x : x; }
constexpr std::int64_t canon_y(const Frame& f, std::int64_t y) { return f.fy ? f.h - 1 - y : y; }
constexpr std::int64_t canon_dx(const Frame& f, std::int64_t dx) { return f.fx ? -dx : dx; }
constexpr std::int64_t canon_dy(const Frame& f, std::int64_t dy) { return f.fy ? -dy : dy; }
// 8 compass directions in common.h kDirs order (0 N=+y, 1 NE, 2 E, 3 SE, 4 S, 5 SW, 6 W, 7 NW).
constexpr int canon_dir(const Frame& f, int d) {
    d &= 7;
    if (f.fx) d = (8 - d) & 7;   // x mirror: E<->W, NE<->NW
    if (f.fy) d = (12 - d) & 7;  // y mirror: N<->S, NE<->SE  ((4 - d) mod 8)
    return d;
}

// ---------------------------------------------------------------- API
// Pure: writes exactly kObsDim floats. Never reads uninitialised padding of non-present rows.
void encode(const RawTurn& raw, float* x);
// FNV-1a-32 over the float bit patterns (probe/fixture fingerprint).
std::uint32_t obs_hash(const float* x, int n);

// SDK glue (nn_obs_glue.cpp, only when NN_ANY_HEAD): fill `out` from already-computed state. false = unavailable
// (not initialised / draft). Idempotent within a round; also advances the bounded memory (observe).
bool capture(const Bot& bot, RawTurn& out);
// Memory tick without building a RawTurn: last-seen tables, alive transitions, score/hp history. Cheap; meant for a
// per-turn hook so memory does not depend on which turns admitted a head (see agents/C/patches).
void observe(const Bot& bot);

} // namespace nnobs
