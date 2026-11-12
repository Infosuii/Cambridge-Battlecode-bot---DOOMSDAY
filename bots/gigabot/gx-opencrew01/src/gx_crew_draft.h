#pragma once
#include "gx_opencrew.h"

#if GX_OPEN_CREW
namespace gx_crew {
namespace d = bc::detail;

struct Job {
    bc::bitboard tiles;
    float hp = 0, soak = 0, value = 0;
    int home = kUnreach, enemy = kUnreach, altar = kUnreach;
    int group = -1, need = 0;
};

struct Result {
    Step plan[kBody][kSteps]{};
    float value = -1.0f;
};

inline int dist_to(const bc::distance_field& field, const bc::bitboard& tiles) {
    int best = kUnreach;
    for (vec2 p : tiles.positions()) best = std::min(best, static_cast<int>(fdist(field,p)));
    return best;
}

inline std::uint32_t next(std::uint32_t& seed) {
    seed = seed * 1664525u + 1013904223u;
    return seed >> 16;
}

inline Result schedule(const std::vector<Job>& jobs, const int edges[48][48],
                       int bodies, bool frontier, unsigned seed) {
    int where[kBody], free[kBody]{}, depth[kBody]{};
    bool used[48]{};
    std::fill_n(where,bodies,-1);
    Result out;
    out.value = 0;
    for (int it = 0; it < bodies * kSteps; ++it) {
        if (bc::fuel_remaining() < 600000) break;
        int root = -1;
        for (int s = 0; s < bodies; ++s)
            if (depth[s] < kSteps && (root < 0 || free[s] < free[root])) root = s;
        if (root < 0) break;
        float best = 0;
        int best_job = -1, best_crew = 0, best_arrive = 0, best_done = 0;
        for (int j = 0; j < static_cast<int>(jobs.size()); ++j) {
            const auto& g = jobs[j];
            if (used[j] || g.need == 0 || g.need > bodies) continue;
            if (g.enemy + 4 < g.home) continue;
            int arrival[kBody];
            for (int s = 0; s < bodies; ++s) {
                const int travel = where[s] < 0 ? g.home : edges[where[s]][j];
                arrival[s] = free[s] + (travel == kUnreach ? 300 : std::max(0,travel - 1));
                if (depth[s] >= kSteps) arrival[s] = 300;
            }
            if (arrival[root] > 85) continue;
            int crew = 1 << root, arrive = arrival[root];
            for (int c = 1; c < g.need; ++c) {
                int next_s = -1;
                for (int s = 0; s < bodies; ++s)
                    if (!(crew & (1 << s)) && (next_s < 0 || arrival[s] < arrival[next_s])) next_s = s;
                crew |= 1 << next_s;
                arrive = std::max(arrive,arrival[next_s]);
            }
            if (arrive > 85) continue;
            const int done = arrive + static_cast<int>(std::ceil(g.hp / (48.0f * g.need))) + 8;
            if (done > 115) continue;
            float occupied = 0.0f;
            for (int s = 0; s < bodies; ++s) if (crew & (1 << s)) occupied += done - free[s];
            float reward = g.value;
            if (frontier && g.enemy <= g.home + 12 && depth[root] == 0 && g.need <= 2) reward *= 1.35f;
            const float health_turns = std::min(18.0f, g.soak / (48.0f * g.need * 32.0f));
            const float noise = seed ? 0.72f + next(seed) * (0.56f / 65535.0f) : 1.0f;
            const float score = noise * reward / (12.0f + occupied + health_turns);
            if (score > best) {
                best = score;
                best_job = j;
                best_crew = crew;
                best_arrive = arrive;
                best_done = done;
            }
        }
        if (best_job < 0) {
            depth[root] = kSteps;
            continue;
        }
        const auto& g = jobs[best_job];
        for (int s = 0; s < bodies; ++s) if (best_crew & (1 << s)) {
            const int expires = std::min(kUntil,best_done + (g.need > 1 ? 24 : 14));
            out.plan[s][depth[s]++] = {g.group, std::max(0, free[s] - 3), expires, g.need};
            where[s] = best_job;
            free[s] = best_done + 1;
        }
        used[best_job] = true;
        const float contention = frontier && g.enemy <= g.home + 12 && g.need <= 2 && best_arrive <= 28 ? 1.16f : 1.0f;
        out.value += contention * g.value * (130.0f - best_done) / 130.0f;
    }
    return out;
}

inline std::vector<std::uint8_t> make(unsigned picks) {
    if (picks < 3 || picks > 5 || bc::constants::draft_memory_bytes < kBytes) return {};
    std::uint32_t n = 0;
    if (d::sdk_map_num_camp_groups(&n) != 0 || n < 5 || n > 48) return {};
    std::vector<std::uint32_t> handles(n);
    if (d::sdk_map_camp_groups(handles.data(),n,&n) != 0 || n > 48) return {};
    const auto ally = bc::map::spawn_region(team::ally), foe = bc::map::spawn_region(team::enemy);
    const auto hard = bc::map::walls() | bc::map::holes() | bc::map::altars();
    const auto blocked = hard | foe;
    bc::bitboard visited, altar_ring;
    altar_ring.clear();
    for (vec2 p : bc::map::altars().positions())
        altar_ring.draw_chebyshev(p,static_cast<float>(bc::constants::submit_gems_range));
    altar_ring &= ~blocked;
    bc::distance_field home, enemy, altar;
    home.compute(blocked, ally, visited);
    enemy.compute(hard | ally, foe, visited);
    if (!altar_ring.is_empty()) altar.compute(blocked,altar_ring,visited);
    d::camp_design designs[16]{};
    bool have[16]{};
    std::vector<Job> jobs;
    for (std::uint32_t i = 0; i < n; ++i) {
        if (bc::fuel_remaining() < 1600000) return {};
        d::camp_group_info info{};
        std::uint32_t m = 0, members[16];
        if (d::sdk_map_camp_group(handles[i],&info) != 0 || (!info.gems && !info.gold) ||
            d::sdk_map_camp_group_num_camps(handles[i],&m) != 0 || m == 0 || m > 16 ||
            d::sdk_map_camp_group_camps(handles[i],members,m,&m) != 0) continue;
        Job g;
        g.group = static_cast<int>(i);
        g.tiles.clear();
        float total_strength = 0;
        std::pair<float,float> units[16];
        int count = 0;
        for (std::uint32_t k = 0; k < m; ++k) {
            d::camp_info c{};
            if (d::sdk_map_camp_info(members[k],&c) != 0 || c.type < 0 || c.type >= 16) break;
            if (!have[c.type]) {
                if (d::sdk_camp_design(c.type,&designs[c.type]) != 0) break;
                have[c.type] = true;
            }
            const auto& stats = designs[c.type].base_stats;
            const float health = stats.base_health, strength = std::max(0.0f,stats.base_strength);
            g.tiles.set({c.x,c.y},true);
            g.hp += health;
            total_strength += strength;
            units[count++] = {health,strength};
        }
        if (count != static_cast<int>(m) || g.hp > 6700.0f) continue;
        std::sort(units,units+count);
        for (int k = 0; k < count; ++k) {
            g.soak += units[k].first * total_strength;
            total_strength -= units[k].second;
        }
        g.home = dist_to(home,g.tiles);
        g.enemy = dist_to(enemy,g.tiles);
        if (g.home > 65) continue;
        if (!altar_ring.is_empty()) g.altar = dist_to(altar,g.tiles);
        for (int c = 1; c <= 3; ++c) {
            if (g.soak / (48.0f * c) <= 420.0f * c && g.hp <= 2300.0f * c) {
                g.need = c; break;
            }
        }
        if (g.need == 0) continue;
        const float delivery = 1.0f + 0.012f * std::min(40,g.altar);
        g.value = (static_cast<float>(info.gems) / delivery + 0.095f * info.gold);
        if (g.value > 0.0f) jobs.push_back(std::move(g));
    }
    if (jobs.size() < 4) return {};
    int edges[48][48];
    for (std::size_t i = 0; i < jobs.size(); ++i) {
        if (bc::fuel_remaining() < 1400000) return {};
        bc::distance_field d;
        d.compute(blocked,jobs[i].tiles,visited);
        for (std::size_t j = 0; j < jobs.size(); ++j) edges[i][j] = dist_to(d,jobs[j].tiles);
    }
    const bool frontier = action == 1003u;
    std::vector<std::uint8_t> bytes(kBytes,0);
    for (int bodies : {static_cast<int>(picks), static_cast<int>(picks)+1}) {
        auto best = schedule(jobs,edges,bodies,frontier,0);
        for (unsigned seed = 1; seed <= 12 && bc::fuel_remaining() >= 950000; ++seed) {
            const auto rival = schedule(jobs,edges,bodies,frontier,2654435761u * seed);
            if (rival.value > best.value) best = rival;
        }
        const int off = kOffset + (bodies - 3) * (2 + kBody * kSteps * kStride);
        bytes[off] = 0x93;
        bytes[off+1] = static_cast<std::uint8_t>(bodies);
        int at = off + 2;
        for (int s = 0; s < kBody; ++s) for (int k = 0; k < kSteps; ++k) {
            const auto& v = best.plan[s][k];
            bytes[at++] = v.group < 0 ? 255 : static_cast<std::uint8_t>(v.group);
            bytes[at++] = static_cast<std::uint8_t>(v.ready);
            bytes[at++] = static_cast<std::uint8_t>(v.expires);
            bytes[at++] = static_cast<std::uint8_t>(v.need);
        }
    }
    return bytes;
}
}  // namespace gx_crew
#endif
