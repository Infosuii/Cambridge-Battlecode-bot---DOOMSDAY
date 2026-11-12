#pragma once
// Learned draft, ported from bots/v81hl/src/draft.cpp ml_draft_pick (v81_home_ladder_hybrid; the user lifted the
// no-copy rule for v81hl on 2026-11-01). A 53 -> 64 -> 1 tanh net scores every free champion by P(win | 16 map
// features, our picks with it, their picks, team size, picking first, draft progress); DZ takes the best.
// The map part is computed once, on the first draft turn (100x fuel); later picks add a few weight rows each.
#include "config.h"
#include <cambc.h>
#include <algorithm>
#include <cmath>
#include <vector>
#if DZ_DRAFT_NET
#include "v81_draft_net.h"
namespace dz::v81 {
// Lambert continued fraction (error < 1e-6 for |x| < 5); std::tanh is a libm call (~150 fuel in wasm).
inline float fast_tanh(float x) {
    if (x > 4.97f) return 1.0f;
    if (x < -4.97f) return -1.0f;
    const float x2 = x * x;
    return x * (135135.0f + x2 * (17325.0f + x2 * (378.0f + x2))) / (135135.0f + x2 * (62370.0f + x2 * (3150.0f + x2 * 28.0f)));
}
// Champion index (0..11, cambc::champion_draft order) the net prefers, or -1 when the map read fails.
inline int draft_choice(std::uint32_t size) {
    namespace dn = draft_net;
    namespace api = cambc::detail;
    static float h_map[dn::kHid] = {};
    static bool have_feat = false;
    if (!have_feat) {
        const float W = static_cast<float>(cambc::map::width()), Hh = static_cast<float>(cambc::map::height());
        float sp[2][2] = {};
        const cambc::team sides[2] = {cambc::team::ally, cambc::team::enemy};
        for (int t = 0; t < 2; ++t) {
            int x0 = 1 << 20, y0 = 1 << 20, x1 = -1, y1 = -1;
            for (auto q : cambc::map::spawn_region(sides[t]).positions())
                x0 = std::min(x0, q.x), y0 = std::min(y0, q.y), x1 = std::max(x1, q.x), y1 = std::max(y1, q.y);
            sp[t][0] = static_cast<float>(x0 + x1) / 2.0f, sp[t][1] = static_cast<float>(y0 + y1) / 2.0f;
        }
        std::uint32_t n = 0;
        if (api::sdk_map_num_camp_groups(&n) != 0 || n > 400) return -1;
        std::vector<std::uint32_t> handles(n);
        if (n && api::sdk_map_camp_groups(handles.data(), n, &n) != 0) return -1;
        float gems = 0, gold = 0, maxg = 0, near = 0, dsum = 0, cnt[6] = {};
        for (std::uint32_t k = 0; k < n; ++k) {
            api::camp_group_info info{};
            api::sdk_map_camp_group(handles[k], &info);
            const float g = static_cast<float>(info.gems);
            gems += g, gold += static_cast<float>(info.gold), maxg = std::max(maxg, g);
            std::uint32_t m = 0;
            api::sdk_map_camp_group_num_camps(handles[k], &m);
            std::vector<std::uint32_t> mem(std::max<std::uint32_t>(m, 1));
            if (m) api::sdk_map_camp_group_camps(handles[k], mem.data(), m, &m);
            float x = 0, y = 0, c = 0;
            for (std::uint32_t q = 0; q < m; ++q) {
                api::camp_info spec{};
                if (api::sdk_map_camp_info(mem[q], &spec) != 0) continue;
                if (spec.type >= 0 && spec.type < 6) cnt[spec.type] += 1;
                x += static_cast<float>(spec.x), y += static_cast<float>(spec.y), c += 1;
            }
            if (c > 0) {
                const float d = std::max(std::fabs(x / c - sp[0][0]), std::fabs(y / c - sp[0][1]));
                dsum += d;
                if (d <= 20) near += g;
            }
        }
        const float sd = std::max(std::fabs(sp[0][0] - sp[1][0]), std::fabs(sp[0][1] - sp[1][1]));
        const float nn = static_cast<float>(n);
        const float f[16] = {W / 100, Hh / 100, W * Hh / 10000, nn / 30, gems / 500, gold / 3000, cnt[0] / 20, cnt[1] / 20, cnt[2] / 20,
            cnt[3] / 20, cnt[5] / 4, cnt[4] / 2, sd / 100, n ? dsum / nn / 100 : 0, gems > 0 ? near / gems : 0, maxg / 60};
        for (int h = 0; h < dn::kHid; ++h) {
            float a = dn::b1[h];
            for (int i = 0; i < 16; ++i) a += dn::W1[i * dn::kHid + h] * f[i];
            h_map[h] = a;
        }
        have_feat = true;
    }
    const auto ours = cambc::draft::current_draft(cambc::team::ally), theirs = cambc::draft::current_draft(cambc::team::enemy);
    bool taken[12] = {};
    for (auto c : ours) if (static_cast<int>(c) >= 0 && static_cast<int>(c) < 12) taken[static_cast<int>(c)] = true;
    const int sz = static_cast<int>(std::max<std::uint32_t>(size, 1));
    const int j = static_cast<int>(ours.size()) + 1;
    const bool first = theirs.size() == ours.size();
    int rows[32]; float rw[32]; int nr = 0;
    for (auto o : ours) if (nr < 28) rows[nr] = 16 + static_cast<int>(o), rw[nr++] = 1.0f;
    for (auto o : theirs) if (nr < 28) rows[nr] = 28 + static_cast<int>(o), rw[nr++] = 1.0f;
    rows[nr] = 40 + std::min(std::max(sz, 3), 5) - 3, rw[nr++] = 1.0f;
    if (first) rows[nr] = 43, rw[nr++] = 1.0f;
    rows[nr] = 44, rw[nr++] = static_cast<float>(j) / static_cast<float>(sz);
    float h_base[dn::kHid];
    for (int h = 0; h < dn::kHid; ++h) {
        float a = h_map[h];
        for (int r = 0; r < nr; ++r) a += dn::W1[rows[r] * dn::kHid + h] * rw[r];
        h_base[h] = a;
    }
    int best = -1; float best_z = -1e30f;
    for (int c = 0; c < 12; ++c) {
        if (taken[c]) continue;
        float z = dn::b2;
        const float* wc = dn::W1 + (16 + c) * dn::kHid;
        for (int h = 0; h < dn::kHid; ++h) z += dn::w2[h] * fast_tanh(h_base[h] + wc[h]);
        if (z > best_z) best_z = z, best = c;
    }
    return best;
}
}
#endif
