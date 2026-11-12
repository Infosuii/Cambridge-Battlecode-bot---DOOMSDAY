// CLRL_ACT: the cl1 camp-pointer actor chooses v92's farm target (task rl-env-collector-1104).
// Hybrid macro milestone: at farm()'s target point (after v92's own choice `best`) the actor encodes this body's cl1
// observation and runs the network, both CHARGED (outside debug_block, as in deployment), samples a c-row at
// temperature 1 and returns the World group to farm (action 12 = no farm target this turn). Only logging is inside
// debug_block. Rows (one per actor decision):
//   CLA1 <round> <slot> <body_id> <sampled> <logp> <reset> <mask_bits> <v92_row> <b64 int16[448]>
// and at the end of the same turn (main.cpp), the target that was actually executed after v92's later code:
//   CLX1 <round> <slot> <body_id> <executed_row>   (12 = no target or a group outside the 12 rows)
// The collector joins them; a decision whose executed row differs from the sampled one is a replacement and makes
// the episode PPO-ineligible (PPO_HANDOFF: replacements are rejected in the first schema).
#pragma once
#if CLRL_ACT
#include <cmath>
#include <cstdint>
#include <cstdio>

#include "clrl_actor.h"
#include "clrl_rec.h"

#ifndef CLRL_SEED
#define CLRL_SEED 1104
#endif

namespace clrl {
struct ActState {
    float h[clrl_actor::kH] = {};
    bool have = false;
    std::uint64_t rng = 0;
    int dec_round = -1;  // round of this turn's decision (-1: none this turn)
};
inline ActState act;

inline double uniform01(std::uint64_t& s) {  // splitmix64
    s += 0x9E3779B97F4A7C15ull;
    std::uint64_t z = s;
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
    z ^= z >> 31;
    return static_cast<double>(z >> 11) * (1.0 / 9007199254740992.0);
}
} // namespace clrl

struct ClrlAct {
    // Called at farm()'s target point with v92's own choice; returns the World group index to farm (-1 none).
    template <class BotT>
    static int decide(const BotT& b, int v92_best, int claim_dead) {
        using namespace clrl;
        if (!act.rng) act.rng = static_cast<std::uint64_t>(CLRL_SEED) * 0x100000001B3ull ^ (static_cast<std::uint64_t>(b.my_id) << 17);
        const bool reset = !act.have || b.target_group == claim_dead;  // first decision, or respawned since the last
        const std::uint64_t f0 = bc::fuel_remaining();
        ClrlFriend::encode(b);                                          // charged: deployment encoder
        const std::uint64_t f1 = bc::fuel_remaining();
        clrl_actor::Out o;
        clrl_actor::forward(st.f, act.h, reset, o);                     // charged: deployment inference
        const std::uint64_t f2 = bc::fuel_remaining();
        double mx = -1e30;
        for (int i = 0; i < clrl_actor::kNA; ++i)
            if (o.legal[i] && o.logits[i] > mx) mx = o.logits[i];
        double p[clrl_actor::kNA], z = 0;
        for (int i = 0; i < clrl_actor::kNA; ++i) {
            p[i] = o.legal[i] ? std::exp(static_cast<double>(o.logits[i]) - mx) : 0.0;
            z += p[i];
        }
        const double u = uniform01(act.rng) * z;
        int a = clrl_actor::kNA - 1;
        double acc = 0;
        for (int i = 0; i < clrl_actor::kNA; ++i) {
            if (!o.legal[i]) continue;
            acc += p[i];
            if (u < acc) {
                a = i;
                break;
            }
        }
        const double logp = std::log(p[a] / z);
        unsigned mask = 0;
        int v92_row = v92_best < 0 ? -1 : kC;
        for (int i = 0; i < clrl_actor::kNA; ++i) mask |= o.legal[i] ? (1u << i) : 0u;
        for (int i = 0; i < kC; ++i)
            if (v92_best >= 0 && st.c_group[i] == v92_best) v92_row = i;
        for (int i = 0; i < clrl_actor::kH; ++i) act.h[i] = o.h[i];
        act.have = true;
        act.dec_round = b.round;
        debug_block({
            std::printf("CLA1 %d %d %u %d %.7f %d %u %d %s\n", b.round, b.slot, b.my_id, a, logp, reset ? 1 : 0, mask,
                        v92_row, b64(st.f, kNF).c_str());
            std::printf("CLF1 %d %u enc %llu fwd %llu left %llu\n", b.round, b.my_id,
                        static_cast<unsigned long long>(f0 - f1), static_cast<unsigned long long>(f1 - f2),
                        static_cast<unsigned long long>(f2));
        });
        return a < kC ? st.c_group[a] : -1;
    }

    // End of the body's turn (main.cpp): the target actually executed, if this turn had an actor decision.
    template <class BotT>
    static void executed(const BotT& b) {
        using namespace clrl;
        if (act.dec_round != b.round) return;
        act.dec_round = -1;
        int row = kC;  // 12 = no target or a group outside the 12 rows (same meaning as the sampled action 12)
        for (int i = 0; i < kC; ++i)
            if (b.target_group >= 0 && st.c_group[i] == b.target_group) row = i;
        debug_block({ std::printf("CLX1 %d %d %u %d\n", b.round, b.slot, b.my_id, row); });
    }
};
#endif
