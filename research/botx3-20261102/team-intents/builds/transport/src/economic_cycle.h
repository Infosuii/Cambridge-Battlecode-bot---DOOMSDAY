#pragma once
#include <algorithm>
#include <cmath>

// Map-independent one-job delivery model. Distances and service estimates come
// from the executor's legal view; this module never queries hidden state.
namespace economic_cycle {
inline float delivery_cost(float collection_cost, float reward_gems,
                           float reward_gold_value, int bank_distance) {
    if (reward_gems <= 0 || bank_distance < 0) return collection_cost;
    // Amortize a return trip against the gem part of a mixed economic job.
    // Gold remains useful immediately for progression; gems require delivery.
    const float share = reward_gems / std::max(1.0f, reward_gems + reward_gold_value);
    return collection_cost + share * (bank_distance + std::ceil(reward_gems / 10.0f));
}
inline bool plan_active(int round, int start, int end) {
    return start >= 0 && round >= start && (end <= 0 || round < end);
}
}
