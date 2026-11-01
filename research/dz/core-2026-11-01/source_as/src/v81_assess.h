#pragma once
// Learned fight-or-run assessment, ported from bots/v81hl/src/bot.cpp (A2_ASSESS) with its weights
// (v81_assess_model.h, engine counterfactuals; the user lifted the no-copy rule for v81hl on 2026-11-01).
// Output: predicted 3-round value of fighting minus running, in gems. Features rebuilt from DZ's observation.
#include "config.h"
#include "observation.h"
#include <algorithm>
#include <cmath>
#if DZ_HAS(ASSESS)
#include "v81_assess_model.h"
namespace dz::v81 {
inline float assess_tanh(float x) {
    if (x > 4.97f) return 1.0f;
    if (x < -4.97f) return -1.0f;
    const float x2 = x * x;
    return x * (135135.0f + x2 * (17325.0f + x2 * (378.0f + x2))) / (135135.0f + x2 * (62370.0f + x2 * (3150.0f + x2 * 28.0f)));
}
inline float assess_fight(const Observation& obs, unsigned round) {
    namespace am = assess_model;
    float f[am::kIn] = {};
    auto& me = cambc::self();
    const int ti = static_cast<int>(me.champion_name());
    if (ti >= 0 && ti < 12) f[ti] = 1.0f;
    f[12] = obs.hp / std::max(1.0f, obs.max_hp);
    f[13] = static_cast<float>(obs.bag) / 100.0f;
    f[14] = obs.strength / 100.0f;
    int spell = 0;
    for (auto ability : me.abilities()) { if (spell < 2) f[15 + spell] = ability.is_ready() ? 1.0f : 0.0f; ++spell; }
    f[17] = static_cast<float>(round) / 1000.0f;
    const int radii[3] = {3, 5, 8};
    const SeenChampion* nb = nullptr;
    int nbd = 99, reach_me = 0, in_mine = 0;
    float ours = obs.hp, theirs = 0.0f, weakest = 1.0f;
    for (const auto& e : obs.enemies) {
        const int d = static_cast<int>(obs.p.chebyshev_distance(e.p));
        for (int k = 0; k < 3; ++k)
            if (d <= radii[k]) f[18 + 5 * k] += 1.0f, f[19 + 5 * k] += e.hp / 1000.0f, f[20 + 5 * k] += e.strength / 100.0f;
        if (d < nbd) nbd = d, nb = &e;
        reach_me += d <= std::max(1, e.range) + 1;
        if (d <= obs.range) ++in_mine, weakest = std::min(weakest, e.hp / std::max(1.0f, e.max_hp));
        if (d <= 4) theirs += e.hp;
    }
    for (const auto& a : obs.allies) {
        const int d = static_cast<int>(obs.p.chebyshev_distance(a.p));
        for (int k = 0; k < 3; ++k)
            if (d <= radii[k]) f[21 + 5 * k] += 1.0f, f[22 + 5 * k] += a.hp / 1000.0f;
        if (d <= 4) ours += a.hp;
    }
    if (nb) {
        f[33] = static_cast<float>(nbd) / 8.0f;
        f[34] = nb->hp / std::max(1.0f, nb->max_hp);
        f[35] = nb->range > 1 ? 1.0f : 0.0f;
    }
    f[36] = static_cast<float>(reach_me);
    f[37] = static_cast<float>(in_mine);
    // log(ours/theirs) without libm: a 3-term atanh series of (r-1)/(r+1), clamped like the original (+-3).
    {
        const float r = (ours + 1.0f) / (theirs + 1.0f), u = (r - 1.0f) / (r + 1.0f), u2 = u * u;
        f[38] = std::clamp(2.0f * u * (1.0f + u2 / 3.0f + u2 * u2 / 5.0f), -3.0f, 3.0f);
    }
    f[39] = weakest;
    for (const auto& c : obs.camps)
        if (c.strength > 0 && std::max(std::abs(c.p.x - obs.p.x), std::abs(c.p.y - obs.p.y)) <= 4) f[40] += 1.0f, f[41] += c.strength / 100.0f;
    float out = am::kB2;
    for (int j = 0; j < am::kHidden; ++j) {
        float v = am::kB1[j];
        for (int i = 0; i < am::kIn; ++i) v += (f[i] - am::kMu[i]) / am::kSd[i] * am::kW1[i][j];
        out += assess_tanh(v) * am::kW2[j];
    }
    return out;
}
}
#endif
