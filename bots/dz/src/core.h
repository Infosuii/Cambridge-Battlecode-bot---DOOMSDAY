#pragma once
#include "config.h"
#include <algorithm>
#include <cstdint>

namespace dz {
enum class Tier { Full, Lean, Fallback };
constexpr Tier tier_for(std::uint64_t fuel) {
    return fuel >= config::full_fuel ? Tier::Full : fuel >= config::lean_fuel ? Tier::Lean : Tier::Fallback;
}
struct StaleTurn {};
template<class ReadRound> void require_current(std::uint32_t round, ReadRound read) {
    if (read() != round) throw StaleTurn{};
}
struct Contract {
    int objective = -1, checked = 0, distance = 65535, capture = 65535;
    float hp = 0;
    void start(int g, int round, int dist, float health, int timer) {
        *this = {g, round, dist, timer, health};
    }
    bool progressing(int round, int dist, float health, int timer) {
        if (dist < distance || health + 0.01f < hp || timer < capture) {
            checked = round; distance = dist; hp = health; capture = timer;
        }
        return round - checked < config::contract_window;
    }
};
enum class GroupState : std::uint8_t { Alive, Partial, Reward, Respawning, Unknown };
struct GroupBelief {
    GroupState state = GroupState::Alive;
    float hp = 0;
    int seen = -1, ready = 0, avoid_until = 0, capture = 65535;
    unsigned failures = 0;
    bool available(int round) const { return round >= avoid_until && (state != GroupState::Respawning || ready <= round); }
};
inline bool bank_now(int bag, int distance, int submitted, int winning) {
    return bag > 0 && (bag >= config::bank_bag || distance <= 8 || submitted + bag >= winning);
}
}
