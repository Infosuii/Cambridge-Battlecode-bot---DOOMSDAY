// Fable map-feature playstyle (fbstyle): the draft reads the map (gem/gold supply, where the gems are, distances,
// terrain, camp types) into feat[], scores every style for this team size with a linear model fitted on lab games
// (fbstyle_model.h) and takes the best. A style = lineup (pick order) + behaviour (knob deltas). The style id goes to
// the champions through draft-memory byte 6 (0x80 | id); each champion applies the behaviour once at its first turn.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>

#include <cambc.h>

#include "common.h"
#include "lab.h"

namespace fbstyle {
inline constexpr int kF = 32;          // features
inline constexpr int kLineups = 4, kBehaviours = 3, kStyles = kLineups * kBehaviours;
inline float feat[kF] = {};
inline bool feat_ok = false;
inline int chosen = -1;                // the draft's style (written to draft memory)

namespace cd_ = cambc;
using cdr = bc::champion_draft;
// Lineups per team size (index = picks - 3), in pick order. 0 = v216's own lineups.
inline constexpr cdr kLineup[3][kLineups][5] = {
    {{cdr::vendetta, cdr::varg, cdr::ren, cdr::ryth, cdr::marcella},
     {cdr::vendetta, cdr::varg, cdr::marcella, cdr::heart_of_ruin, cdr::ryth},
     {cdr::marcella, cdr::tavi, cdr::ryth, cdr::vendetta, cdr::varg},
     {cdr::varg, cdr::marcella, cdr::heart_of_ruin, cdr::vendetta, cdr::ryth}},
    {{cdr::vendetta, cdr::varg, cdr::cassi_and_issac, cdr::ren, cdr::ryth},
     {cdr::vendetta, cdr::marcella, cdr::heart_of_ruin, cdr::varg, cdr::ryth},
     {cdr::prism, cdr::heart_of_ruin, cdr::marcella, cdr::cassi_and_issac, cdr::ryth},
     {cdr::vesper_vale, cdr::marcella, cdr::ryth, cdr::varg, cdr::vendetta}},
    {{cdr::vendetta, cdr::varg, cdr::cassi_and_issac, cdr::ryth, cdr::ren},
     {cdr::heart_of_ruin, cdr::marcella, cdr::vendetta, cdr::cassi_and_issac, cdr::ryth},
     {cdr::vendetta, cdr::varg, cdr::marcella, cdr::heart_of_ruin, cdr::ryth},
     {cdr::prism, cdr::marcella, cdr::heart_of_ruin, cdr::cassi_and_issac, cdr::ryth}},
};
// Behaviours: knob deltas (lab.h knob meaning, bot.cpp knob block). 0 = none, 1 = gold/scale, 2 = fight.
struct KD { int i; float v; };
inline constexpr KD kGold[] = {{8, 2.0f}, {12, -1.0f}};
inline constexpr KD kFight[] = {{0, 1.3f}, {5, 1.0f}, {43, 1.0f}};

inline int lineup_of(int style) { return std::clamp(style, 0, kStyles - 1) / kBehaviours; }
inline int behaviour_of(int style) { return std::clamp(style, 0, kStyles - 1) % kBehaviours; }

inline void apply_behaviour(int style) {
    if (style < 0) return;
    const int b = behaviour_of(style);
    if (b == 1) for (const auto& k : kGold) lab::knobs[k.i] += k.v;
    if (b == 2) {
        for (const auto& k : kFight) lab::knobs[k.i] += k.v;
        lab::knobs[15] = 2.0f; // hunt on
    }
}

// direct read (fdist, common.h): no host call, and the fast host has no bc_DistanceField_Get
inline std::uint16_t fd(const bc::distance_field& f, cd_::vec2 p) {
    return fdist(f, p);
}

// Map features (once, first draft turn; ~2 distance fields). Index meanings are fixed: the model depends on them.
inline void compute_features() {
    if (feat_ok) return;
    feat_ok = true;
    float* f = feat;
    for (int i = 0; i < kF; ++i) f[i] = 0.0f;
    unsigned picks = 5;
    try { picks = bc::draft::team_size(); } catch (...) {}
    const int W = static_cast<int>(bc::map::width()), H = static_cast<int>(bc::map::height());
    const float area = static_cast<float>(W * H), side = std::sqrt(std::max(area, 1.0f));
    f[0] = static_cast<float>(picks);
    f[1] = std::log2(std::max(area, 1.0f));
    const auto walls = bc::map::walls(), holes = bc::map::holes(), bushes = bc::map::bushes(), altars = bc::map::altars();
    const auto sp_us = bc::map::spawn_region(team::ally), sp_them = bc::map::spawn_region(team::enemy);
    f[18] = static_cast<float>(walls.count()) / area;
    f[19] = static_cast<float>(holes.count()) / area;
    f[20] = static_cast<float>(bushes.count()) / area;
    const auto alt = altars.positions();
    f[17] = static_cast<float>(alt.size());
    bc::distance_field d_us, d_them;
    bc::bitboard visited;
    d_us.compute(walls | holes | altars | sp_them, sp_us, visited);
    d_them.compute(walls | holes | altars | sp_us, sp_them, visited);
    auto centre = [](const bc::bitboard& b) {
        int x0 = 1 << 20, y0 = 1 << 20, x1 = -1, y1 = -1;
        for (auto q : b.positions()) x0 = std::min(x0, q.x), y0 = std::min(y0, q.y), x1 = std::max(x1, q.x), y1 = std::max(y1, q.y);
        return cd_::vec2{(x0 + x1) / 2, (y0 + y1) / 2};
    };
    const cd_::vec2 cu = centre(sp_us), ct = centre(sp_them);
    constexpr std::uint16_t kU = 0xFFFF;
    // rush distance: our spawn to the nearest tile beside the enemy spawn (the region itself is blocked in d_us)
    std::uint16_t rush = kU;
    for (auto q : sp_them.positions())
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy) {
                const cd_::vec2 r{q.x + dx, q.y + dy};
                if (r.x < 0 || r.y < 0 || r.x >= W || r.y >= H) continue;
                rush = std::min(rush, fd(d_us, r));
            }
    (void)ct;
    f[14] = rush == kU ? 4.0f : static_cast<float>(rush) / side;
    // altars: nearest walking distance from each spawn (an altar tile is blocked; use its best neighbour)
    float a_us = 1e9f, a_them = 1e9f;
    for (auto a : alt)
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy) {
                const cd_::vec2 q{a.x + dx, a.y + dy};
                if (q.x < 0 || q.y < 0 || q.x >= W || q.y >= H) continue;
                const auto u = fd(d_us, q), t = fd(d_them, q);
                if (u != kU) a_us = std::min(a_us, static_cast<float>(u));
                if (t != kU) a_them = std::min(a_them, static_cast<float>(t));
            }
    f[15] = a_us > 1e8f ? 4.0f : a_us / side;
    f[16] = a_them > 1e8f ? 4.0f : a_them / side;
    // camp groups
    std::uint32_t n = 0;
    if (bc::detail::sdk_map_num_camp_groups(&n) != 0 || n > 400) return;
    std::vector<std::uint32_t> handles(std::max<std::uint32_t>(n, 1));
    if (n && bc::detail::sdk_map_camp_groups(handles.data(), n, &n) != 0) return;
    float gems = 0, gold = 0, maxg = 0, gem_groups = 0, mine = 0, middle = 0, cut = 0, dsum = 0, maze = 0, mazew = 0, gold_only = 0;
    float types[6] = {}, ncamps = 0;
    for (std::uint32_t k = 0; k < n; ++k) {
        bc::detail::camp_group_info info{};
        if (bc::detail::sdk_map_camp_group(handles[k], &info) != 0) continue;
        const float g = static_cast<float>(info.gems), go = static_cast<float>(info.gold);
        gems += g, gold += go, maxg = std::max(maxg, g);
        if (g > 0) gem_groups += 1; else gold_only += go;
        std::uint32_t m = 0;
        bc::detail::sdk_map_camp_group_num_camps(handles[k], &m);
        std::vector<std::uint32_t> mem(std::max<std::uint32_t>(m, 1));
        if (m) bc::detail::sdk_map_camp_group_camps(handles[k], mem.data(), m, &m);
        float du = 1e9f, dt = 1e9f;
        cd_::vec2 cp{0, 0};
        bool any = false;
        for (std::uint32_t q = 0; q < m; ++q) {
            bc::detail::camp_info spec{};
            if (bc::detail::sdk_map_camp_info(mem[q], &spec) != 0) continue;
            if (spec.type >= 0 && spec.type < 6) types[spec.type] += 1;
            ncamps += 1;
            const cd_::vec2 p{spec.x, spec.y};
            // a camp tile itself may be unreachable (blocked by the camp); take the best neighbour
            for (int dx = -1; dx <= 1; ++dx)
                for (int dy = -1; dy <= 1; ++dy) {
                    const cd_::vec2 r{p.x + dx, p.y + dy};
                    if (r.x < 0 || r.y < 0 || r.x >= W || r.y >= H) continue;
                    const auto u = fd(d_us, r), t = fd(d_them, r);
                    if (u != kU) du = std::min(du, static_cast<float>(u));
                    if (t != kU) dt = std::min(dt, static_cast<float>(t));
                }
            if (!any) cp = p, any = true;
        }
        if (g <= 0 || !any) continue;
        if (du > 1e8f) { cut += g; continue; }
        if (dt > 1e8f) dt = du * 3.0f;
        if (du < 0.85f * dt) mine += g;
        else if (du <= 1.15f * dt) middle += g;
        dsum += g * du;
        const float cheb = static_cast<float>(std::max(std::abs(cp.x - cu.x), std::abs(cp.y - cu.y)));
        if (cheb > 3.0f) maze += g * (du / cheb), mazew += g;
    }
    f[3] = static_cast<float>(n);
    f[4] = gems;
    f[5] = gold;
    f[6] = gems / static_cast<float>(std::max(picks, 1u));
    f[7] = gold / std::max(gems, 1.0f);
    f[8] = gem_groups;
    f[9] = gems > 0 ? maxg / gems : 0.0f;
    f[10] = gems > 0 ? mine / gems : 0.0f;
    f[11] = gems > 0 ? middle / gems : 0.0f;
    f[12] = gems > 0 ? cut / gems : 0.0f;
    f[13] = gems > cut ? dsum / (gems - cut) / side : 0.0f;
    f[21] = mazew > 0 ? maze / mazew : 1.0f;
    for (int t = 0; t < 6; ++t) f[22 + t] = ncamps > 0 ? types[t] / ncamps : 0.0f;
    f[28] = gold > 0 ? gold_only / gold : 0.0f;
    f[29] = gems / std::max(area, 1.0f) * 100.0f;     // gem density (per 100 tiles)
    f[30] = gold / std::max(area, 1.0f) * 100.0f;     // gold density
    f[31] = 1.0f;                                     // bias
}

int choose(int picks);  // fbstyle_model.h
} // namespace fbstyle

#include "fbstyle_model.h"
