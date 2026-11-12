// Fuel profiler for measurement builds (CLFP 1): where turns run out of fuel, and how much fuel turns leave unused.
// A turn that runs out is suspended and resumes in the next round, so the first marker that sees a round change
// reports the stage it ran out in: CLFP O <round started> <last marker> <this marker>. Every 250 rounds,
// CLFP U <round> <turns> <overruns> then counts of turns ending with fuel left in [0,2k) [2k,5k) [5k,10k) [10k,20k)
// [20k,40k) [40k,+). Markers: 0 turn start, 1/2 around nn_decide, 3/4 around nn_lazy_score, 5 end of play_turn,
// 6 after nn_turn_end. Default builds compile none of this.
#pragma once
#ifndef CLFP
#define CLFP 0
#endif
#if CLFP
#include <cstdio>
namespace clfp {
inline unsigned r0 = 0;
inline int last = 0;
inline bool hit = false;
inline unsigned turns = 0, overruns = 0, bucket[6] = {};
inline void start() {
    r0 = bc::round_number(), last = 0, hit = false;
}
inline void mark(int id) {
    if (!hit && bc::round_number() != r0) {
        hit = true, ++overruns;
        std::printf("CLFP O %u %d %d\n", r0, last, id);
    }
    last = id;
}
inline void end() {
    mark(7);
    ++turns;
    if (!hit) {
        const auto f = bc::fuel_remaining();
        ++bucket[f < 2000 ? 0 : f < 5000 ? 1 : f < 10000 ? 2 : f < 20000 ? 3 : f < 40000 ? 4 : 5];
    }
    if (r0 % 250 == 0) {
        std::printf("CLFP U %u %u %u %u %u %u %u %u %u\n", r0, turns, overruns, bucket[0], bucket[1], bucket[2], bucket[3],
                    bucket[4], bucket[5]);
    }
}
}  // namespace clfp
#define CLFP_MARK(id) clfp::mark(id)
#else
#define CLFP_MARK(id) ((void)0)
#endif
