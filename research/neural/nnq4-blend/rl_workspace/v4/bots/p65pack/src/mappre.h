// Map walking analysis shared by the draft (A2_MAPPRE: computed on the first draft turn, ~10M fuel) and the champions
// (A2_PLANSEL: the plan cluster). Distances are the engine's distance field over walls, holes and altars (8-way steps);
// a camp group's distance is that of its nearest camp tile's free neighbour, +1 off the tile (agent2/lab/path_feats.js).
#pragma once
#if A2_PLANSEL || A2_MAPPRE || A2_MACRO
#include <algorithm>
#include <cstdint>
#include <vector>

namespace mappre {
namespace d = cambc::detail;

struct Box {
    int x0 = 1 << 20, y0 = 1 << 20, x1 = -1, y1 = -1; // inclusive
    bool ok() const { return x1 >= 0; }
};
inline Box box_of(const bc::bitboard& b) {
    Box r;
    for (vec2 q : b.positions()) r.x0 = std::min(r.x0, q.x), r.y0 = std::min(r.y0, q.y), r.x1 = std::max(r.x1, q.x), r.y1 = std::max(r.y1, q.y);
    return r;
}
inline int cheb_to(const Box& b, int x, int y) { return std::max(std::max({b.x0 - x, 0, x - b.x1}), std::max({b.y0 - y, 0, y - b.y1})); }

struct Group {
    std::vector<vec2> tiles;
    std::vector<int> types; // camp type per tile (camp designs)
    float gems = 0, gold = 0, hp = 0;
    int respawn = 60;
};
// Every camp group in map order (the champions' World::groups order).
inline bool read_groups(std::vector<Group>& out) {
    constexpr float kHp[6] = {1350, 2400, 120, 120, 20000, 5000};
    std::uint32_t n = 0;
    if (d::sdk_map_num_camp_groups(&n) != 0 || n > 400) return false;
    std::vector<std::uint32_t> handles(n);
    if (n && d::sdk_map_camp_groups(handles.data(), n, &n) != 0) return false;
    out.assign(n, Group{});
    for (std::uint32_t k = 0; k < n; ++k) {
        d::camp_group_info info{};
        d::sdk_map_camp_group(handles[k], &info);
        out[k].gems = static_cast<float>(info.gems), out[k].gold = static_cast<float>(info.gold);
        std::uint32_t m = 0;
        d::sdk_map_camp_group_num_camps(handles[k], &m);
        if (!m) continue;
        std::vector<std::uint32_t> mem(m);
        d::sdk_map_camp_group_camps(handles[k], mem.data(), m, &m);
        for (std::uint32_t q = 0; q < m; ++q) {
            d::camp_info spec{};
            if (d::sdk_map_camp_info(mem[q], &spec) != 0) continue;
            out[k].tiles.push_back(vec2{spec.x, spec.y});
            out[k].types.push_back(spec.type);
            out[k].hp += spec.type >= 0 && spec.type < 6 ? kHp[spec.type] : 5000.0f;
        }
        std::int32_t respawn = 60;
        d::sdk_bc_camp_group_max_respawn(handles[k], &respawn);
        out[k].respawn = std::max(respawn, 10);
    }
    return true;
}
inline constexpr int kUnreach = bc::distance_field::unreachable;
// Walking distance from the field's roots to a group (kUnreach if none of its tiles has a reachable free neighbour).
inline int walk_to(const bc::distance_field& f, const std::vector<vec2>& tiles, int W, int H) {
    int best = kUnreach;
    for (vec2 t : tiles)
        for (int dy = -1; dy <= 1; ++dy)
            for (int dx = -1; dx <= 1; ++dx) {
                const vec2 p{t.x + dx, t.y + dy};
                if (p.x < 0 || p.y < 0 || p.x >= W || p.y >= H) continue;
                const int v = fdist(f, p);
                if (v != kUnreach) best = std::min(best, v + (dx || dy ? 1 : 0));
            }
    return best;
}
inline constexpr float kArea = 4000.0f, kRatio = 1.2f;
// Plan cluster (plan_sel.h, agent2/lab/plan_clusters.py): 2 * large + maze, from a field rooted at our spawn region.
inline int cluster_of(const bc::distance_field& from_spawn, const Box& spawn, const std::vector<Group>& G, int W, int H) {
    float reach = 0, ratio = 0;
    for (const auto& g : G) {
        if (g.tiles.empty()) continue;
        const int w = walk_to(from_spawn, g.tiles, W, H);
        if (w == kUnreach) continue;
        int s = 1 << 20;
        for (vec2 t : g.tiles) s = std::min(s, cheb_to(spawn, t.x, t.y));
        const float gems = std::max(g.gems, 1.0f);
        reach += gems, ratio += gems * std::min(static_cast<float>(w) / static_cast<float>(std::max(s, 1)), 6.0f);
    }
    const bool large = static_cast<float>(W * H) >= kArea, maze = reach > 0 && ratio / reach >= kRatio;
    return 2 * (large ? 1 : 0) + (maze ? 1 : 0);
}
inline bc::bitboard terrain() { return bc::map::walls() | bc::map::holes() | bc::map::altars(); }

#if A2_MAPPRE
// Draft-memory summary at kOff: 'M', version, plan cluster, group count n (0 = groups omitted: more than kMaxGroups),
// rush distance (u16, spawn to enemy spawn, 65535 = none), nearest altar access (u16), then 4 bytes per group:
// distance from our spawn, from the enemy spawn (u8; 254 = 254 or more, 255 = unreachable), value per round of a
// round trip (u8, x10, capped), flags (1 reachable by us, 2 contested: the enemy spawn is nearer, 4 reachable by them).
inline constexpr int kOff = 600, kMaxGroups = 96, kBytes = 8 + 4 * kMaxGroups;
struct Analysis {
    bool ok = false;
    int cluster = -1, rush = kUnreach, altar = kUnreach;
    std::vector<Group> G;
    std::vector<int> dA, dE;
    std::vector<float> vpt;
    std::vector<int> mat; // (n + 1) x n walking distances: row 0 from our spawn, row 1 + a from group a (kUnreach)
    bool have_mat = false;
};
inline const Analysis& analysis() {
    static Analysis A;
    static bool done = false;
    if (done) return A;
    done = true;
    try {
        const int W = static_cast<int>(bc::map::width()), H = static_cast<int>(bc::map::height());
        const bc::bitboard ours = bc::map::spawn_region(team::ally), theirs = bc::map::spawn_region(team::enemy);
        const Box sb = box_of(ours);
        if (!sb.ok() || !read_groups(A.G)) return A;
        const bc::bitboard walls = terrain();
        bc::bitboard visited;
        bc::distance_field fa, fe;
        fa.compute(walls, ours, visited);
        fe.compute(walls, theirs, visited);
        const int n = static_cast<int>(A.G.size());
        A.dA.assign(n, kUnreach), A.dE.assign(n, kUnreach), A.vpt.assign(n, 0.0f);
        for (int i = 0; i < n; ++i) {
            const auto& g = A.G[i];
            if (g.tiles.empty()) continue;
            A.dA[i] = walk_to(fa, g.tiles, W, H), A.dE[i] = walk_to(fe, g.tiles, W, H);
            if (A.dA[i] == kUnreach) continue;
            // DPLAN's farming model: 1.25 rounds a tile, 50 damage a round per champion, crews of 1-3 by health, capture 5.
            const float crew = g.hp <= 1500 ? 1.0f : g.hp <= 3000 ? 2.0f : 3.0f;
            A.vpt[i] = (g.gold + 10.0f * g.gems) / (2.5f * static_cast<float>(A.dA[i]) + g.hp / (50.0f * crew) + 5.0f) / crew;
        }
        for (vec2 p : theirs.positions()) A.rush = std::min<int>(A.rush, fdist(fa, p));
        for (vec2 a : bc::map::altars().positions())
            for (int dy = -1; dy <= 1; ++dy)
                for (int dx = -1; dx <= 1; ++dx) {
                    const vec2 p{a.x + dx, a.y + dy};
                    if (p.x < 0 || p.y < 0 || p.x >= W || p.y >= H || (dx == 0 && dy == 0)) continue;
                    const int v = fdist(fa, p);
                    if (v != kUnreach) A.altar = std::min(A.altar, v);
                }
        A.cluster = cluster_of(fa, sb, A.G, W, H);
        A.ok = true;
        // Group-to-group walking distances for the opening planner, while the first draft turn's fuel lasts.
        if (bc::fuel_remaining() > 4000000) {
            A.mat.assign(static_cast<std::size_t>((n + 1) * n), kUnreach);
            for (int b = 0; b < n; ++b) A.mat[static_cast<std::size_t>(b)] = A.dA[b];
            bool full = true;
            for (int a = 0; a < n && full; ++a) {
                if (bc::fuel_remaining() < 2500000) {
                    full = false;
                    break;
                }
                if (A.G[a].tiles.empty() || A.dA[a] == kUnreach) continue;
                bc::bitboard roots;
                for (vec2 t : A.G[a].tiles) roots.set(t, true);
                bc::distance_field f;
                f.compute(walls, roots, visited);
                for (int b = 0; b < n; ++b)
                    if (!A.G[b].tiles.empty()) A.mat[static_cast<std::size_t>((1 + a) * n + b)] = a == b ? 0 : walk_to(f, A.G[b].tiles, W, H);
            }
            A.have_mat = full;
        }
    } catch (const std::exception& e) {
        A.ok = false;
#ifdef A2_MAPPRE_DEBUG
        std::printf("MAPPRE exception %s%c", e.what(), 10);
#endif
    } catch (...) {
        A.ok = false;
    }
    return A;
}
inline std::vector<std::uint8_t> summary_bytes() {
    const Analysis& A = analysis();
    std::vector<std::uint8_t> b;
    if (!A.ok) return b;
    const int n = static_cast<int>(A.G.size());
    const int m = n <= kMaxGroups ? n : 0;
    const auto u8d = [](int v) { return static_cast<std::uint8_t>(v == kUnreach ? 255 : std::min(v, 254)); };
    b = {'M', 1, static_cast<std::uint8_t>(A.cluster), static_cast<std::uint8_t>(m), static_cast<std::uint8_t>(A.rush & 255),
        static_cast<std::uint8_t>(A.rush >> 8), static_cast<std::uint8_t>(A.altar & 255), static_cast<std::uint8_t>(A.altar >> 8)};
    for (int i = 0; i < m; ++i) {
        const int fl = (A.dA[i] != kUnreach ? 1 : 0) | (A.dE[i] < A.dA[i] ? 2 : 0) | (A.dE[i] != kUnreach ? 4 : 0);
        b.push_back(u8d(A.dA[i]));
        b.push_back(u8d(A.dE[i]));
        b.push_back(static_cast<std::uint8_t>(std::min(255.0f, 10.0f * A.vpt[i])));
        b.push_back(static_cast<std::uint8_t>(fl));
    }
    return b;
}
#endif
} // namespace mappre
#endif
