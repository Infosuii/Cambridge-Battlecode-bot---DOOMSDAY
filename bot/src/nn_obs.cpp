// Pure observation encoder (agent C). No cambc.h: compiled natively by tests/cpp/obs_*.cpp with -DNNOBS_NATIVE.
// In the bot it exists only when some head is compiled in (NN_ANY_HEAD); otherwise this translation unit is empty
// and the Wasm is unchanged. python/nfs/obs.py mirrors every line (float32, same operation order).
#include "nn_config.h"

#if NN_ANY_HEAD || defined(NNOBS_NATIVE)
#include "nn_obs.h"

#include <cmath>
#include <cstring>

namespace nnobs {
namespace {

constexpr float kBig = 10000.0f; // "unknown/unreachable" distances and ages: saturate at the clip bound

inline float f(std::int64_t v) { return static_cast<float>(v); }
inline std::int64_t iabs(std::int64_t v) { return v < 0 ? -v : v; }
inline std::int64_t cheb(std::int64_t dx, std::int64_t dy) {
    const std::int64_t a = iabs(dx), b = iabs(dy);
    return a > b ? a : b;
}

inline float norm1(float v, float inv, float lo, float hi) {
    float y = v * inv;
    if (!std::isfinite(y)) return 0.0f;
    y = y < lo ? lo : (y > hi ? hi : y);
    return y + 0.0f; // -0 -> +0
}

inline void onehot(float* s, int base, int n, std::int64_t k) {
    if (k >= 0 && k < n) s[base + static_cast<int>(k)] = 1.0f;
}

// Row order: visible first, then position known, then nearer, then lower handle; then the original index so the
// order is total even for duplicate handles (which capture never produces).
struct Key {
    int vis, known;
    std::int64_t dist;
    std::uint32_t handle;
    int idx;
};
inline bool before(const Key& a, const Key& b) {
    if (a.vis != b.vis) return a.vis > b.vis;
    if (a.known != b.known) return a.known > b.known;
    if (a.dist != b.dist) return a.dist < b.dist;
    if (a.handle != b.handle) return a.handle < b.handle;
    return a.idx < b.idx;
}
template <int N> int sort_rows(Key (&k)[N], int n) {
    for (int i = 1; i < n; ++i) { // insertion sort, n <= 6
        const Key v = k[i];
        int j = i - 1;
        while (j >= 0 && before(v, k[j])) {
            k[j + 1] = k[j];
            --j;
        }
        k[j + 1] = v;
    }
    return n;
}

} // namespace

std::uint32_t obs_hash(const float* x, int n) {
    std::uint32_t h = 0x811C9DC5u;
    for (int i = 0; i < n; ++i) {
        std::uint32_t b;
        std::memcpy(&b, &x[i], 4);
        for (int k = 0; k < 4; ++k) {
            h ^= (b >> (8 * k)) & 0xFFu;
            h *= 0x01000193u;
        }
    }
    return h;
}

void encode(const RawTurn& r, float* x) {
    for (int i = 0; i < kObsDim; ++i) x[i] = 0.0f;
    const Frame F = frame_of(r);
    const std::int64_t px = r.pos_x, py = r.pos_y;
    const bool alive = r.alive != 0;
    float* s = x;

    // ---- self
    s[fsg::self_alive] = alive ? 1.0f : 0.0f;
    s[fsg::self_hp_frac] = alive ? r.hp / r.max_hp : 0.0f;
    s[fsg::self_max_hp] = r.max_hp;
    s[fsg::self_strength] = r.strength;
    s[fsg::self_focus] = r.focus;
    s[fsg::self_gems] = f(r.gems);
    s[fsg::self_gems_vs_carry] = f(r.gems) / f(r.tribute_carry);
    s[fsg::self_gold] = f(r.gold);
    s[fsg::self_attack_range] = f(r.attack_range);
    s[fsg::self_melee] = r.attack_range <= 1 ? 1.0f : 0.0f;
    onehot(s, fsg::self_type__base, fsg::self_type__n, r.type);
    {
        constexpr int base[2] = {fsg::self_spell0_present, fsg::self_spell1_present};
        constexpr int kind[2] = {fsg::self_spell0_kind__base, fsg::self_spell1_kind__base};
        static_assert(fsg::self_spell0_ready == fsg::self_spell0_present + 1 && fsg::self_spell0_cooldown == fsg::self_spell0_present + 2 &&
            fsg::self_spell0_range == fsg::self_spell0_present + 3);
        static_assert(fsg::self_spell1_ready == fsg::self_spell1_present + 1 && fsg::self_spell1_cooldown == fsg::self_spell1_present + 2 &&
            fsg::self_spell1_range == fsg::self_spell1_present + 3);
        for (int k = 0; k < 2; ++k) {
            if (!r.spell_present[k]) continue;
            s[base[k]] = 1.0f;
            s[base[k] + 1] = r.spell_cooldown[k] == 0 && !r.cast_done ? 1.0f : 0.0f;
            s[base[k] + 2] = f(r.spell_cooldown[k]);
            s[base[k] + 3] = r.spell_range[k];
            onehot(s, kind[k], fsg::self_spell0_kind__n, std::int64_t{r.spell_kind[k]} - 1);
        }
    }
    s[fsg::self_cast_done] = r.cast_done ? 1.0f : 0.0f;
    {
        const std::uint32_t b = static_cast<std::uint32_t>(r.state_bits);
        s[fsg::self_state_recalling] = (b >> 1) & 1u ? 1.0f : 0.0f;
        s[fsg::self_state_submitting_gems] = (b >> 2) & 1u ? 1.0f : 0.0f;
        s[fsg::self_state_teleporting] = (b >> 12) & 1u ? 1.0f : 0.0f;
        s[fsg::self_state_can_move] = (b >> 3) & 1u ? 1.0f : 0.0f;
        s[fsg::self_state_can_attack] = (b >> 4) & 1u ? 1.0f : 0.0f;
        s[fsg::self_state_can_cast] = (b >> 11) & 1u ? 1.0f : 0.0f;
    }
    s[fsg::self_items] = r.items;
    s[fsg::self_camp_taken_mult] = r.camp_taken_mult;
    s[fsg::self_camp_dealt_mult] = r.camp_dealt_mult;
    s[fsg::self_ward_charges] = f(r.ward_charges);
    s[fsg::self_ward_cooldown] = f(r.ward_cooldown);
    s[fsg::self_pos_x] = f(canon_x(F, px)) / f(F.w - 1);
    s[fsg::self_pos_y] = f(canon_y(F, py)) / f(F.h - 1);
    auto tiles = [](std::int32_t d) { return d >= 0 ? f(d) : d == -2 ? kBig : 0.0f; };
    s[fsg::self_spawn_dist] = tiles(r.spawn_dist);
    s[fsg::self_altar_known] = r.altar_ready && r.altar_dist != -1 ? 1.0f : 0.0f;
    s[fsg::self_altar_dist] = r.altar_ready ? tiles(r.altar_dist) : 0.0f;
    s[fsg::self_enemy_spawn_cheb] =
        f(cheb(2 * px - (std::int64_t{r.enemy_spawn_x0} + r.enemy_spawn_x1), 2 * py - (std::int64_t{r.enemy_spawn_y0} + r.enemy_spawn_y1))) * 0.5f;
    s[fsg::self_enemy_spawn_walk_known] = r.enemy_ready && r.enemy_spawn_walk != -1 ? 1.0f : 0.0f;
    s[fsg::self_enemy_spawn_walk] = r.enemy_ready ? tiles(r.enemy_spawn_walk) : 0.0f;
    s[fsg::self_in_bush] = r.in_bush ? 1.0f : 0.0f;
    s[fsg::self_on_own_spawn] = r.on_own_spawn ? 1.0f : 0.0f;
    s[fsg::self_in_hot_zone] = r.in_hot_zone ? 1.0f : 0.0f;
    s[fsg::self_in_enemy_zone] = r.in_enemy_zone ? 1.0f : 0.0f;
    s[fsg::self_heading_home] = r.heading_home ? 1.0f : 0.0f;
    s[fsg::self_has_target] = r.target_group >= 0 ? 1.0f : 0.0f;
    s[fsg::self_hp_delta_turn] = alive ? (r.hp - r.prev_hp) / r.max_hp : 0.0f;
    if (r.hist10_age >= 10) {
        s[fsg::self_hist10_valid] = 1.0f;
        s[fsg::self_hp_delta_10] = (r.hp - r.hist10_hp) / r.max_hp;
        s[fsg::self_gems_delta_10] = f(std::int64_t{r.gems} - r.hist10_gems);
        s[fsg::self_hist10_age] = f(r.hist10_age);
    }

    // ---- global
    const float win = f(r.winning_gems);
    s[fsg::glob_round_frac] = f(r.round) / f(r.max_rounds);
    s[fsg::glob_ally_score] = f(r.ally_score) / win;
    s[fsg::glob_enemy_score] = f(r.enemy_score) / win;
    s[fsg::glob_score_diff] = f(std::int64_t{r.ally_score} - r.enemy_score) / win;
    s[fsg::glob_gems_to_win] = f(std::int64_t{r.winning_gems} - r.ally_score - r.gems) / win;
    s[fsg::glob_win_now] = r.winning_gems > 0 && std::int64_t{r.ally_score} + r.gems >= r.winning_gems ? 1.0f : 0.0f;
    if (r.hist50_age >= 50) {
        s[fsg::glob_rate50_valid] = 1.0f;
        s[fsg::glob_ally_rate50] = f(std::int64_t{r.ally_score} - r.hist50_ally) / f(r.hist50_age);
        s[fsg::glob_enemy_rate50] = f(std::int64_t{r.enemy_score} - r.hist50_enemy) / f(r.hist50_age);
    }
    if (r.hist200_age >= 200) {
        s[fsg::glob_rate200_valid] = 1.0f;
        s[fsg::glob_ally_rate200] = f(std::int64_t{r.ally_score} - r.hist200_ally) / f(r.hist200_age);
        s[fsg::glob_enemy_rate200] = f(std::int64_t{r.enemy_score} - r.hist200_enemy) / f(r.hist200_age);
    }
    s[fsg::glob_alive_us] = f(r.alive_us) / f(r.team_size);
    s[fsg::glob_alive_them] = f(r.alive_them) / f(r.enemy_count);
    s[fsg::glob_team_size] = f(r.team_size);
    s[fsg::glob_enemy_count] = f(r.enemy_count);
    s[fsg::glob_ally_deaths_50] = f(r.ally_deaths_50);
    s[fsg::glob_enemy_deaths_50] = f(r.enemy_deaths_50);
    s[fsg::glob_ally_deaths_total] = f(r.ally_deaths_total);
    s[fsg::glob_enemy_deaths_total] = f(r.enemy_deaths_total);
    s[fsg::glob_map_w] = f(r.width);
    s[fsg::glob_map_h] = f(r.height);
    {
        const std::int64_t area = std::int64_t{r.width} * r.height;
        s[area <= kSmallMaxArea ? fsg::glob_size_class_small : area <= kMediumMaxArea ? fsg::glob_size_class_medium : fsg::glob_size_class_large] = 1.0f;
    }
    onehot(s, fsg::glob_symmetry__base, fsg::glob_symmetry__n, r.symmetry);
    // No "flipped" feature: it would be the only difference between the two teams' views of a mirrored state.
    s[fsg::glob_n_groups] = f(r.n_groups);
    s[fsg::glob_fields_frac] = f(r.fields_built) / f(r.n_groups);
    s[fsg::glob_vis_enemies] = f(r.vis_enemies);
    s[fsg::glob_vis_allies] = f(r.vis_allies);
    s[fsg::glob_sight_n5] = f(r.sight_n5);
    s[fsg::glob_sight_n20] = f(r.sight_n20);
    if (r.sight_age >= 0) {
        const std::int64_t dx = std::int64_t{r.sight_x} - px, dy = std::int64_t{r.sight_y} - py;
        s[fsg::glob_sight_valid] = 1.0f;
        s[fsg::glob_sight_dx] = f(canon_dx(F, dx));
        s[fsg::glob_sight_dy] = f(canon_dy(F, dy));
        s[fsg::glob_sight_dist] = f(cheb(dx, dy));
        s[fsg::glob_sight_age] = f(r.sight_age);
    }
    if (r.distress_age >= 0) {
        s[fsg::glob_distress_valid] = 1.0f;
        s[fsg::glob_distress_dx] = f(canon_dx(F, std::int64_t{r.distress_x} - px));
        s[fsg::glob_distress_dy] = f(canon_dy(F, std::int64_t{r.distress_y} - py));
        s[fsg::glob_distress_age] = f(r.distress_age);
    }
    s[fsg::glob_enemy_wards] = f(r.enemy_wards);

    // ---- objective slots
    for (int k = 0; k < kObjSlots; ++k) {
        const ObjRaw& o = r.obj[k];
        if (!o.valid) continue;
        float* q = s + kObjBase + k * kObjDim;
        const std::int64_t dx = std::int64_t{o.anchor_x} - px, dy = std::int64_t{o.anchor_y} - py;
        q[fobj::valid] = 1.0f;
        q[fobj::dx] = f(canon_dx(F, dx));
        q[fobj::dy] = f(canon_dy(F, dy));
        q[fobj::dist] = o.dist_walk >= 0 ? f(o.dist_walk) : f(o.dist_cheb);
        q[fobj::dist_is_walk] = o.dist_walk >= 0 ? 1.0f : 0.0f;
        q[fobj::unreachable] = o.dist_walk == -2 ? 1.0f : 0.0f;
        q[fobj::gems] = f(o.gems);
        q[fobj::gold] = f(o.gold);
        onehot(q, fobj::state__base, fobj::state__n, o.state);
        q[fobj::respawn_in] = f(o.respawn_in);
        q[fobj::hp_left_frac] = o.hp_left / o.max_hp;
        q[fobj::max_hp] = o.max_hp;
        q[fobj::harmless] = o.harmless ? 1.0f : 0.0f;
        q[fobj::ally_claims] = f(o.ally_claims);
        q[fobj::enemy_seen] = o.enemy_age >= 0 ? 1.0f : 0.0f;
        q[fobj::enemy_age] = o.enemy_age >= 0 ? f(o.enemy_age) : kBig;
    }
    for (int i = 0; i < kSelfGlobalDim; ++i) s[i] = norm1(s[i], kSGInvScale[i], kSGLo[i], kSGHi[i]);

    // ---- ally rows
    {
        Key key[kAllyRows];
        int n = 0;
        for (int i = 0; i < kAllyRows; ++i) {
            const AllyRaw& a = r.ally[i];
            if (!a.present) continue;
            const bool known = a.known != 0;
            key[n++] = Key{a.visible && known ? 1 : 0, known ? 1 : 0,
                known ? cheb(std::int64_t{a.x} - px, std::int64_t{a.y} - py) : INT64_MAX, a.handle, i};
        }
        sort_rows(key, n);
        for (int j = 0; j < n; ++j) {
            const AllyRaw& a = r.ally[key[j].idx];
            float* q = x + kAllyRowsOff + j * kAllyDim;
            const bool known = a.known != 0;
            q[fa::alive] = a.alive ? 1.0f : 0.0f;
            q[fa::visible] = a.visible && known ? 1.0f : 0.0f;
            q[fa::known] = known ? 1.0f : 0.0f;
            q[fa::age] = known ? (a.visible ? 0.0f : f(a.age)) : kBig;
            if (known) {
                const std::int64_t dx = std::int64_t{a.x} - px, dy = std::int64_t{a.y} - py;
                q[fa::dx] = f(canon_dx(F, dx));
                q[fa::dy] = f(canon_dy(F, dy));
                q[fa::dist] = f(cheb(dx, dy));
                q[fa::hp_frac] = a.hp / a.max_hp;
                q[fa::max_hp] = a.max_hp;
                q[fa::strength] = a.strength;
                q[fa::focus] = a.focus;
                q[fa::range] = f(a.range);
                if (a.gems >= 0) {
                    q[fa::gems_known] = 1.0f;
                    q[fa::gems] = f(a.gems);
                }
            } else {
                q[fa::dist] = kBig;
            }
            onehot(q, fa::type__base, fa::type__n, a.type);
            const std::int32_t c = a.claim_code;
            const bool is_group = c >= 0 && c < r.n_groups && c < 126;
            if (c == 127) q[fa::claim_idle] = 1.0f;
            else if (c == 126) q[fa::claim_dead] = 1.0f;
            else if (is_group) q[fa::claim_group] = 1.0f;
            else if (c >= 0) q[fa::claim_other] = 1.0f;
            if (is_group) {
                q[fa::claim_is_my_target] = c == r.target_group ? 1.0f : 0.0f;
                if (a.claim_dist >= 0 && known) {
                    q[fa::claim_dist_known] = 1.0f;
                    q[fa::claim_dist] = f(a.claim_dist);
                }
                q[fa::claim_gems] = f(a.claim_gems);
            }
            q[fa::acts_before_me] = a.slot < r.slot ? 1.0f : 0.0f;
            for (int i = 0; i < kAllyDim; ++i) q[i] = norm1(q[i], kAllyInvScale[i], kAllyLo[i], kAllyHi[i]);
            x[kAllyMaskOff + j] = 1.0f;
        }
    }

    // ---- enemy rows
    {
        Key key[kEnemyRows];
        int n = 0;
        for (int i = 0; i < kEnemyRows; ++i) {
            const EnemyRaw& e = r.enemy[i];
            if (!e.present) continue;
            const bool known = e.known != 0;
            key[n++] = Key{e.visible && known ? 1 : 0, known ? 1 : 0,
                known ? cheb(std::int64_t{e.x} - px, std::int64_t{e.y} - py) : INT64_MAX, e.handle, i};
        }
        sort_rows(key, n);
        for (int j = 0; j < n; ++j) {
            const EnemyRaw& e = r.enemy[key[j].idx];
            float* q = x + kEnemyRowsOff + j * kEnemyDim;
            const bool known = e.known != 0, vis = known && e.visible;
            q[fe::alive] = e.alive ? 1.0f : 0.0f;
            q[fe::visible] = vis ? 1.0f : 0.0f;
            q[fe::known] = known ? 1.0f : 0.0f;
            q[fe::age] = known ? (vis ? 0.0f : f(e.age)) : kBig;
            if (known) {
                const std::int64_t dx = std::int64_t{e.x} - px, dy = std::int64_t{e.y} - py, d = cheb(dx, dy);
                q[fe::dx] = f(canon_dx(F, dx));
                q[fe::dy] = f(canon_dy(F, dy));
                q[fe::dist] = f(d);
                q[fe::hp_frac] = e.hp / e.max_hp;
                q[fe::max_hp] = e.max_hp;
                q[fe::strength] = e.strength;
                q[fe::focus] = e.focus;
                q[fe::range] = f(e.range);
                q[fe::gems] = f(e.gems);
                const std::uint32_t b = static_cast<std::uint32_t>(e.state_bits);
                q[fe::recalling] = (b >> 1) & 1u ? 1.0f : 0.0f;
                q[fe::tributing] = (b >> 2) & 1u ? 1.0f : 0.0f;
                if (vis && alive) {
                    q[fe::in_my_range] = d <= r.attack_range ? 1.0f : 0.0f;
                    q[fe::threatens_me] = d <= std::int64_t{e.range} + 1 ? 1.0f : 0.0f;
                }
            } else {
                q[fe::dist] = kBig;
            }
            onehot(q, fe::type__base, fe::type__n, e.type);
            for (int i = 0; i < kEnemyDim; ++i) q[i] = norm1(q[i], kEnemyInvScale[i], kEnemyLo[i], kEnemyHi[i]);
            x[kEnemyMaskOff + j] = 1.0f;
        }
    }
}

} // namespace nnobs
#endif
