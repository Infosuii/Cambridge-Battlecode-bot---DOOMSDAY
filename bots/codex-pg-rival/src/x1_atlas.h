// Map atlas features (research/x3/atlas): what the map is like, computed once from the bot's own world model, so
// the same numbers exist on maps we have never seen. Used to print the atlas (X1_ATLAS 2) and to pick a strategy
// profile by map category (X1_PORTFOLIO). Distances are the bot's walking fields from our and the enemy spawn.
#pragma once
#include "world.h"
#include <algorithm>
#include <cstdio>
#include <vector>

namespace x1_atlas {

struct Features {
    int w = 0, h = 0, area = 1, team = 0, groups = 0;
    std::uint32_t gems = 0, gold = 0;
    float blocked = 0;        // walls, holes, altars (static_blocked) per tile
    float jackpot = 0, top3 = 0; // biggest group / top three groups, share of all gems
    float harmless = 0;       // share of gems in groups that do not fight back
    float strong = 0;         // share of gems in groups with a golem or monolith
    float own = 0, contested = 0, theirs = 0; // gem shares by distance margin (> 3 ours, |m| <= 3, < -3 theirs)
    float near15 = 0, near30 = 0;            // gem shares within 15 / 30 steps of our spawn
    float unreachable = 0;    // gem share we cannot walk to
    int s2s = -1;             // walking steps spawn to spawn
    float maze = 0;           // s2s / straight-line (Chebyshev) spawn distance
    int nearest = -1;         // steps to the nearest group
    float mean_dist = 0;      // gem-weighted mean steps to a group
    int altars = 0, altar_dist = -1;
    float hp_per_gem = 0;     // camp health per gem (how hard the gems are to take)
    float gems_per_champ = 0; // all gems per champion on the map
};

inline Features compute(World& w, int team_size) {
    Features f;
    f.w = w.width; f.h = w.height; f.area = std::max(1, w.width * w.height);
    f.team = team_size; f.groups = static_cast<int>(w.groups.size());
    f.blocked = static_cast<float>(w.static_blocked.count()) / static_cast<float>(f.area);
    w.ensure_enemy_field();
    std::vector<std::uint32_t> g;
    float hp = 0, wsum = 0, dsum = 0;
    for (std::size_t gi = 0; gi < w.groups.size(); ++gi) {
        const auto& gr = w.groups[gi];
        f.gems += gr.gems; f.gold += gr.gold; g.push_back(gr.gems);
        bool strong = false;
        int ours = kUnreach;
        for (int ci : gr.camps) {
            const auto& c = w.camps[static_cast<std::size_t>(ci)];
            hp += c.max_hp;
            strong |= c.type == bc::camp_type::golem || c.type == bc::camp_type::monolith;
            ours = std::min<int>(ours, fdist(w.spawn_field, c.pos));
        }
        const float v = static_cast<float>(gr.gems);
        if (gr.harmless) f.harmless += v;
        if (strong) f.strong += v;
        if (ours >= kUnreach) { f.unreachable += v; continue; }
        const int m = gi < w.group_margin.size() ? w.group_margin[gi] : 0;
        if (m > 3) f.own += v; else if (m >= -3) f.contested += v; else f.theirs += v;
        if (ours <= 15) f.near15 += v;
        if (ours <= 30) f.near30 += v;
        if (f.nearest < 0 || ours < f.nearest) f.nearest = ours;
        dsum += v * static_cast<float>(ours); wsum += v;
    }
    const float tot = std::max(1.0f, static_cast<float>(f.gems));
    std::sort(g.begin(), g.end(), [](std::uint32_t a, std::uint32_t b) { return a > b; });
    if (!g.empty()) f.jackpot = static_cast<float>(g[0]) / tot;
    for (std::size_t i = 0; i < g.size() && i < 3; ++i) f.top3 += static_cast<float>(g[i]) / tot;
    f.harmless /= tot; f.strong /= tot; f.own /= tot; f.contested /= tot; f.theirs /= tot;
    f.near15 /= tot; f.near30 /= tot; f.unreachable /= tot;
    f.mean_dist = wsum > 0 ? dsum / wsum : 0;
    f.hp_per_gem = hp / tot;
    f.gems_per_champ = tot / static_cast<float>(std::max(1, 2 * team_size));
    // Spawn to spawn: our walking field at the nearest enemy spawn tile; straight line between spawn centres.
    float ax = 0, ay = 0, bx = 0, by = 0; int na = 0, nb = 0;
    for (vec2 p : w.spawn_tiles) ax += static_cast<float>(p.x), ay += static_cast<float>(p.y), ++na;
    for (vec2 p : w.enemy_spawn.positions()) {
        bx += static_cast<float>(p.x), by += static_cast<float>(p.y), ++nb;
        // The enemy spawn is blocked in our field: step to it from its walkable neighbours.
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy) {
                const vec2 q{p.x + dx, p.y + dy};
                if (q.x < 0 || q.y < 0 || q.x >= w.width || q.y >= w.height) continue;
                const int d = fdist(w.spawn_field, q);
                if (d < kUnreach && (f.s2s < 0 || d + 1 < f.s2s)) f.s2s = d + 1;
            }
    }
    if (na && nb) {
        const float straight = std::max(std::abs(ax / na - bx / nb), std::abs(ay / na - by / nb));
        f.maze = f.s2s > 0 && straight > 0 ? static_cast<float>(f.s2s) / straight : 0;
    }
    f.altars = static_cast<int>(w.altars.size());
    for (vec2 p : w.altar_ring.positions()) {
        const int d = fdist(w.spawn_field, p);
        if (d < kUnreach && (f.altar_dist < 0 || d < f.altar_dist)) f.altar_dist = d;
    }
    return f;
}

// One line, parsed by tools/mapatlas/collect.py; the fingerprint (w h groups gems team) joins it to a map.
inline void print(const Features& f, int team) {
    std::printf("ATLAS fp=%d,%d,%d,%u,%d team_size=%d gold=%u blocked=%.4f jackpot=%.3f top3=%.3f harmless=%.3f strong=%.3f "
                "own=%.3f contested=%.3f theirs=%.3f near15=%.3f near30=%.3f unreachable=%.3f s2s=%d maze=%.3f nearest=%d "
                "mean_dist=%.1f altars=%d altar_dist=%d hp_per_gem=%.1f gems_per_champ=%.1f\n",
                f.w, f.h, f.groups, f.gems, team, f.team, f.gold, f.blocked, f.jackpot, f.top3, f.harmless, f.strong,
                f.own, f.contested, f.theirs, f.near15, f.near30, f.unreachable, f.s2s, f.maze, f.nearest,
                f.mean_dist, f.altars, f.altar_dist, f.hp_per_gem, f.gems_per_champ);
}

} // namespace x1_atlas
