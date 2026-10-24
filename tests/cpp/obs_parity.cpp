// Native tests for the pure observation encoder (agent C). Build (tools/run_obs_tests.py does this):
//   g++ -std=c++20 -O2 -DNNOBS_NATIVE -I bot/src tests/cpp/obs_parity.cpp bot/src/nn_obs.cpp -o obs_parity
// Modes:
//   obs_parity selftest            C++-only invariants (padding, permutation, mirror, NaN/Inf, transforms)
//   obs_parity encode IN OUT       IN = concatenated RawTurn bytes, OUT = concatenated float32[kObsDim] (Python parity)
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#include "nn_obs.h"

using namespace nnobs;

namespace {
int g_fail = 0, g_checks = 0;
#define CHECK(cond, ...)                                                    \
    do {                                                                    \
        ++g_checks;                                                         \
        if (!(cond)) {                                                      \
            ++g_fail;                                                       \
            std::printf("FAIL %s:%d: %s | ", __FILE__, __LINE__, #cond);    \
            std::printf(__VA_ARGS__);                                       \
            std::printf("\n");                                              \
        }                                                                   \
    } while (0)

struct Rng {
    std::uint64_t s;
    std::uint32_t next() {
        s ^= s << 13;
        s ^= s >> 7;
        s ^= s << 17;
        return static_cast<std::uint32_t>(s >> 11);
    }
    int range(int lo, int hi) { return lo + static_cast<int>(next() % static_cast<std::uint32_t>(hi - lo + 1)); }
    float unit() { return static_cast<float>(next() & 0xFFFFFF) / 16777216.0f; }
    bool coin(int pct) { return range(0, 99) < pct; }
};

// A plausible state on a symmetric map (W x H, symmetry sym) for team A with its spawn on the low side.
RawTurn plausible(Rng& g, int sym) {
    RawTurn r;
    std::memset(&r, 0, sizeof(r));
    r.magic = kRawMagic, r.version = kRawVersion, r.schema_hash = kObsSchemaHash, r.size = sizeof(RawTurn);
    r.width = g.range(20, 100), r.height = g.range(20, 100), r.symmetry = sym;
    r.abs_team = 0;
    r.round = g.range(1, 1999), r.max_rounds = 2000, r.winning_gems = 1000;
    r.slot = g.range(0, 4), r.team_size = g.range(3, 6), r.enemy_count = g.range(3, 6);
    r.n_groups = g.range(4, 120), r.fields_built = g.range(0, r.n_groups), r.altar_ready = g.coin(70), r.enemy_ready = g.coin(20);
    r.own_spawn_x0 = 1, r.own_spawn_y0 = 1, r.own_spawn_x1 = 3, r.own_spawn_y1 = 3;
    r.enemy_spawn_x0 = r.width - 4, r.enemy_spawn_x1 = r.width - 2, r.enemy_spawn_y0 = r.height - 4, r.enemy_spawn_y1 = r.height - 2;
    if (sym == 0) r.enemy_spawn_y0 = 1, r.enemy_spawn_y1 = 3;
    if (sym == 1) r.enemy_spawn_x0 = 1, r.enemy_spawn_x1 = 3;
    r.alive = g.coin(90), r.pos_x = g.range(0, r.width - 1), r.pos_y = g.range(0, r.height - 1);
    r.gems = g.range(0, 120), r.gold = g.range(0, 900), r.attack_range = g.range(1, 6), r.type = g.range(0, 12);
    r.state_bits = static_cast<std::int32_t>(g.next() & 0x1FFF), r.cast_done = g.coin(20), r.heading_home = g.coin(20);
    r.target_group = g.range(-1, r.n_groups - 1), r.tribute_carry = g.range(8, 80);
    r.ward_charges = g.range(0, 2), r.ward_cooldown = g.range(0, 120);
    r.spawn_dist = g.range(-2, 150), r.altar_dist = g.range(-2, 150), r.enemy_spawn_walk = g.range(-2, 150);
    r.in_bush = g.coin(20), r.on_own_spawn = g.coin(10), r.in_hot_zone = g.coin(10), r.in_enemy_zone = g.coin(5);
    for (int k = 0; k < 2; ++k) {
        r.spell_present[k] = g.coin(85), r.spell_kind[k] = g.range(1, 7), r.spell_cooldown[k] = g.range(0, 30);
        r.spell_range[k] = static_cast<float>(g.range(0, 8));
    }
    r.max_hp = 500.0f + 2000.0f * g.unit(), r.hp = r.alive ? r.max_hp * g.unit() : 0.0f, r.prev_hp = r.max_hp * g.unit();
    r.strength = 200.0f * g.unit(), r.focus = 200.0f * g.unit(), r.items = 40.0f * g.unit();
    r.camp_taken_mult = g.coin(50) ? 1.0f : 0.7f, r.camp_dealt_mult = g.coin(50) ? 1.0f : 1.1f;
    r.hist10_age = g.coin(80) ? g.range(10, 14) : -1, r.hist10_hp = r.max_hp * g.unit(), r.hist10_gems = g.range(0, 100);
    r.ally_score = g.range(0, 990), r.enemy_score = g.range(0, 990);
    r.hist50_age = g.coin(80) ? g.range(50, 59) : -1, r.hist50_ally = r.ally_score - g.range(0, 50), r.hist50_enemy = r.enemy_score - g.range(0, 50);
    r.hist200_age = g.coin(60) ? g.range(200, 209) : -1, r.hist200_ally = r.ally_score - g.range(0, 200), r.hist200_enemy = r.enemy_score - g.range(0, 200);
    r.alive_us = g.range(0, r.team_size), r.alive_them = g.range(0, r.enemy_count);
    r.ally_deaths_50 = g.range(0, 3), r.enemy_deaths_50 = g.range(0, 3), r.ally_deaths_total = g.range(0, 30), r.enemy_deaths_total = g.range(0, 30);
    r.vis_enemies = g.range(0, 6), r.vis_allies = g.range(0, 5), r.sight_n5 = g.range(0, 5), r.sight_n20 = g.range(0, 9);
    r.sight_age = g.range(-1, 20), r.sight_x = g.range(0, r.width - 1), r.sight_y = g.range(0, r.height - 1);
    r.distress_age = g.range(-1, 10), r.distress_x = g.range(0, r.width - 1), r.distress_y = g.range(0, r.height - 1);
    r.enemy_wards = g.range(0, 3);
    for (auto& o : r.obj) {
        o.valid = g.coin(80), o.group = g.range(0, r.n_groups - 1), o.anchor_x = g.range(0, r.width - 1), o.anchor_y = g.range(0, r.height - 1);
        o.dist_walk = g.range(-2, 200), o.dist_cheb = g.range(0, 100), o.gems = g.range(0, 400), o.gold = g.range(0, 400);
        o.state = g.range(0, 2), o.respawn_in = g.range(0, 300), o.harmless = g.coin(30), o.ally_claims = g.range(0, 3);
        o.enemy_age = g.range(-1, 300), o.max_hp = 100.0f + 20000.0f * g.unit(), o.hp_left = o.max_hp * g.unit();
    }
    for (int i = 0; i < kAllyRows; ++i) {
        auto& a = r.ally[i];
        a.present = i < r.team_size - 1, a.handle = 100u + 7u * static_cast<std::uint32_t>(i), a.slot = i, a.type = g.range(0, 12);
        a.alive = g.coin(85), a.visible = g.coin(50), a.known = g.coin(80), a.age = g.range(0, 60);
        a.x = g.range(0, r.width - 1), a.y = g.range(0, r.height - 1), a.range = g.range(1, 6), a.gems = g.range(-1, 100);
        a.claim_code = g.coin(10) ? -1 : g.range(0, 127), a.claim_dist = g.range(-1, 150), a.claim_gems = g.range(0, 300);
        a.max_hp = 500.0f + 2000.0f * g.unit(), a.hp = a.max_hp * g.unit(), a.strength = 150.0f * g.unit(), a.focus = 150.0f * g.unit();
    }
    for (int i = 0; i < kEnemyRows; ++i) {
        auto& e = r.enemy[i];
        e.present = i < r.enemy_count, e.handle = 200u + 11u * static_cast<std::uint32_t>(i), e.type = g.range(0, 12);
        e.alive = g.coin(85), e.visible = g.coin(40), e.known = g.coin(70), e.age = g.range(0, 60);
        e.x = g.range(0, r.width - 1), e.y = g.range(0, r.height - 1), e.range = g.range(1, 6), e.gems = g.range(0, 100);
        e.state_bits = static_cast<std::int32_t>(g.next() & 0x1FFF);
        e.max_hp = 500.0f + 2000.0f * g.unit(), e.hp = e.max_hp * g.unit(), e.strength = 150.0f * g.unit(), e.focus = 150.0f * g.unit();
    }
    return r;
}

void reflect(const RawTurn& r, std::int32_t& x, std::int32_t& y) {
    if (r.symmetry == 0 || r.symmetry == 2) x = r.width - 1 - x;
    if (r.symmetry == 1 || r.symmetry == 2) y = r.height - 1 - y;
}
// The same state seen by the other team (python/nfs/transforms.py mirror_raw).
RawTurn mirror(const RawTurn& in) {
    RawTurn r = in;
    reflect(r, r.pos_x, r.pos_y);
    reflect(r, r.sight_x, r.sight_y);
    reflect(r, r.distress_x, r.distress_y);
    auto box = [&](std::int32_t& x0, std::int32_t& y0, std::int32_t& x1, std::int32_t& y1) {
        std::int32_t ax = x0, ay = y0, bx = x1, by = y1;
        reflect(r, ax, ay), reflect(r, bx, by);
        x0 = ax < bx ? ax : bx, x1 = ax < bx ? bx : ax, y0 = ay < by ? ay : by, y1 = ay < by ? by : ay;
    };
    box(r.own_spawn_x0, r.own_spawn_y0, r.own_spawn_x1, r.own_spawn_y1);
    box(r.enemy_spawn_x0, r.enemy_spawn_y0, r.enemy_spawn_x1, r.enemy_spawn_y1);
    for (auto& o : r.obj) reflect(r, o.anchor_x, o.anchor_y);
    for (auto& a : r.ally) reflect(r, a.x, a.y);
    for (auto& e : r.enemy) reflect(r, e.x, e.y);
    r.abs_team = 1 - r.abs_team;
    return r;
}

bool same(const float* a, const float* b, int n, int* where = nullptr) {
    for (int i = 0; i < n; ++i)
        if (std::memcmp(&a[i], &b[i], 4) != 0) {
            if (where) *where = i;
            return false;
        }
    return true;
}

int selftest() {
    static float a[kObsDim], b[kObsDim];
    Rng g{0x9E3779B97F4A7C15ull};
    // Transforms: canon_dir is an involution and matches the vector map.
    constexpr int kd[8][2] = {{0, 1}, {1, 1}, {1, 0}, {1, -1}, {0, -1}, {-1, -1}, {-1, 0}, {-1, 1}};
    for (int sym = 0; sym < 3; ++sym) {
        const Frame F = make_frame(30, 40, sym, 100, 100, 0); // spawn far on the high side: flipped
        CHECK(F.flip, "sym %d", sym);
        for (int d = 0; d < 8; ++d) {
            const int e = canon_dir(F, d);
            CHECK(canon_dir(F, e) == d, "dir involution sym %d d %d", sym, d);
            CHECK(kd[e][0] == canon_dx(F, kd[d][0]) && kd[e][1] == canon_dy(F, kd[d][1]), "dir vs vec sym %d d %d", sym, d);
        }
        for (int x = 0; x < 30; ++x) CHECK(canon_x(F, canon_x(F, x)) == x, "pos involution");
    }
    int bad = 0;
    for (int it = 0; it < 3000; ++it) {
        const int sym = it % 3;
        RawTurn r = plausible(g, sym);
        encode(r, a);
        for (int i = 0; i < kObsDim; ++i) bad += !std::isfinite(a[i]);
        // Padding invariance: garbage in non-present rows changes nothing.
        RawTurn p = r;
        for (auto& al : p.ally)
            if (!al.present) {
                std::uint32_t junk = g.next();
                std::memcpy(reinterpret_cast<char*>(&al) + 4, &junk, 4);
                al.x = static_cast<std::int32_t>(g.next()), al.hp = std::nanf(""), al.known = 1, al.visible = 1;
            }
        for (auto& en : p.enemy)
            if (!en.present) en.x = static_cast<std::int32_t>(g.next()), en.max_hp = INFINITY, en.known = 1, en.type = 3;
        encode(p, b);
        int w = -1;
        CHECK(same(a, b, kObsDim, &w), "padding it %d idx %d", it, w);
        // Padded rows are zero with mask 0, present rows have mask 1 and come first.
        int na = 0, ne = 0;
        for (const auto& al : r.ally) na += al.present != 0;
        for (const auto& en : r.enemy) ne += en.present != 0;
        for (int j = 0; j < kAllyRows; ++j) {
            CHECK(a[kAllyMaskOff + j] == (j < na ? 1.0f : 0.0f), "ally mask");
            if (j >= na)
                for (int i = 0; i < kAllyDim; ++i) CHECK(a[kAllyRowsOff + j * kAllyDim + i] == 0.0f, "ally pad zero");
        }
        for (int j = 0; j < kEnemyRows; ++j) {
            CHECK(a[kEnemyMaskOff + j] == (j < ne ? 1.0f : 0.0f), "enemy mask");
            if (j >= ne)
                for (int i = 0; i < kEnemyDim; ++i) CHECK(a[kEnemyRowsOff + j * kEnemyDim + i] == 0.0f, "enemy pad zero");
        }
        // Row permutation: shuffling RawTurn rows does not change the encoding.
        RawTurn q = r;
        for (int i = kAllyRows - 1; i > 0; --i) {
            const int j = g.range(0, i);
            const AllyRaw t = q.ally[i];
            q.ally[i] = q.ally[j], q.ally[j] = t;
        }
        for (int i = kEnemyRows - 1; i > 0; --i) {
            const int j = g.range(0, i);
            const EnemyRaw t = q.enemy[i];
            q.enemy[i] = q.enemy[j], q.enemy[j] = t;
        }
        encode(q, b);
        CHECK(same(a, b, kObsDim, &w), "permutation it %d idx %d", it, w);
        // Team A/B equivalence on the mirrored state.
        const RawTurn m = mirror(r);
        encode(m, b);
        CHECK(same(a, b, kObsDim, &w), "mirror sym %d it %d idx %d", sym, it, w);
        CHECK(!frame_of(r).flip && frame_of(m).flip, "frames: team A unflipped, mirrored state flipped");
    }
    CHECK(bad == 0, "non-finite outputs %d", bad);
    // Hostile inputs: NaN/Inf/extremes everywhere -> finite, clipped output.
    for (int it = 0; it < 2000; ++it) {
        RawTurn r;
        auto* w32 = reinterpret_cast<std::uint32_t*>(&r);
        for (std::size_t i = 0; i < sizeof(r) / 4; ++i) w32[i] = g.next() ^ (g.next() << 16);
        if (it % 3 == 0) {
            const float specials[] = {NAN, INFINITY, -INFINITY, 3.4e38f, -3.4e38f, 0.0f, -0.0f, 1e-38f};
            float* fp = reinterpret_cast<float*>(&r);
            for (std::size_t i = 0; i < sizeof(r) / 4; ++i)
                if (g.coin(30)) fp[i] = specials[g.range(0, 7)];
        }
        encode(r, a);
        for (int i = 0; i < kObsDim; ++i) {
            CHECK(std::isfinite(a[i]), "hostile finite idx %d", i);
            CHECK(!std::signbit(a[i]) || a[i] < 0.0f, "negative zero idx %d", i);
        }
    }
    // Zero entities and a dead self.
    {
        Rng h{7};
        RawTurn r = plausible(h, 2);
        for (auto& al : r.ally) al.present = 0;
        for (auto& en : r.enemy) en.present = 0;
        r.alive = 0, r.hp = 0.0f;
        encode(r, a);
        for (int i = kAllyRowsOff; i < kObsDim; ++i) CHECK(a[i] == 0.0f, "empty rows idx %d", i);
        CHECK(a[fsg::self_alive] == 0.0f && a[fsg::self_hp_frac] == 0.0f && a[fsg::self_hp_delta_turn] == 0.0f, "dead self");
    }
    std::printf("obs_parity selftest: %d checks, %d failures (kObsDim %d, RawTurn %zu bytes, hash 0x%08X)\n", g_checks, g_fail,
        kObsDim, sizeof(RawTurn), kObsSchemaHash);
    return g_fail ? 1 : 0;
}

int encode_file(const char* in, const char* out) {
    std::FILE* fi = std::fopen(in, "rb");
    std::FILE* fo = std::fopen(out, "wb");
    if (!fi || !fo) {
        std::printf("cannot open files\n");
        return 2;
    }
    RawTurn r;
    static float x[kObsDim];
    int n = 0;
    while (std::fread(&r, sizeof(r), 1, fi) == 1) {
        encode(r, x);
        std::fwrite(x, sizeof(float), kObsDim, fo);
        ++n;
    }
    std::fclose(fi);
    std::fclose(fo);
    std::printf("encoded %d\n", n);
    return 0;
}
} // namespace

int main(int argc, char** argv) {
    if (argc >= 2 && std::strcmp(argv[1], "selftest") == 0) return selftest();
    if (argc >= 4 && std::strcmp(argv[1], "encode") == 0) return encode_file(argv[2], argv[3]);
    if (argc >= 2 && std::strcmp(argv[1], "info") == 0) {
        std::printf("{\"obs_dim\": %d, \"raw_size\": %zu, \"hash\": %u}\n", kObsDim, sizeof(RawTurn), kObsSchemaHash);
        return 0;
    }
    std::printf("usage: obs_parity selftest | encode IN OUT | info\n");
    return 2;
}
