#pragma once
#include "config.h"
#include "plan.h"
#include <algorithm>
#include <cstdint>
#include <exception>

namespace dz {
enum class Tier { Full, Lean, Fallback };
enum class ActionBudget { Normal, Emergency };
constexpr bool action_budget_available(std::uint64_t fuel,ActionBudget budget) {
    return fuel>(budget==ActionBudget::Emergency?1800:1500+config::reserve);
}
constexpr Tier tier_for(std::uint64_t fuel) {
    return fuel >= config::full_fuel ? Tier::Full : fuel >= config::lean_fuel ? Tier::Lean : Tier::Fallback;
}
constexpr bool requested_navigation_fits(std::uint64_t fuel,std::uint64_t cost,bool requested) {
    return fuel>cost+config::reserve+4000&&(requested||tier_for(fuel)==Tier::Full);
}
struct StaleTurn {};
struct ModuleHealth {
    unsigned failures=0;
    bool enabled() const { return failures<3; }
};
template<class Work,class OnError>
bool guarded_module(ModuleHealth& health,Work work,OnError on_error) {
    if (!health.enabled()) return false;
    try { work(); return true; }
    catch (const StaleTurn&) { throw; }
    catch (const std::exception& error) { ++health.failures; on_error(error.what()); }
    catch (...) { ++health.failures; on_error("unknown exception"); }
    return false;
}
// History records only successful actions. Engine flags remain authoritative for
// attack resets, ranged move-or-attack, stuns and other live restrictions.
struct ActionHistory {
    bool moved = false, cast = false, exclusive_cast = false;
    bool may_move(bool engine_allows, bool restricted, bool channel) const {
        return engine_allows && !restricted && !channel && !exclusive_cast;
    }
    bool may_cast(bool engine_allows, bool restricted, bool channel, bool exclusive) const {
        return engine_allows && !restricted && !channel && !cast && !(exclusive && moved);
    }
    void record_move(bool success) { moved |= success; }
    void record_cast(bool success, bool exclusive) { if (success) { cast = true; exclusive_cast = exclusive; } }
};
template<class ReadRound> void require_current(std::uint32_t round, ReadRound read) {
    if (read() != round) throw StaleTurn{};
}
struct Contract {
    int objective = -1, checked = 0, distance = 65535, capture = 65535;
    float hp = 0;
    int window = config::contract_window; // Crew jobs wait longer for allies.
    int onsite_since = -1; // First round standing on the group while its reward is available.
    void start(int g, int round, int dist, float health, int timer, int no_progress = config::contract_window) {
        *this = {g, round, dist, timer, health, no_progress};
    }
    bool progressing(int round, int dist, float health, int timer) {
        if (dist < distance || health + 0.01f < hp || timer < capture) {
            checked = round; distance = dist; hp = health; capture = timer;
        }
        return round - checked < window;
    }
};
enum class GroupState : std::uint8_t { Alive, Partial, Reward, Respawning, Unknown };
struct GroupBelief {
    GroupState state = GroupState::Alive;
    float hp = 0;
    int seen = -1, ready = 0, avoid_until = 0, capture = 65535;
    unsigned failures = 0;
#if DZ_ECONOMY_V2
    int capture_phase=-1;
#endif
    bool available(int round) const { return round >= avoid_until && (state != GroupState::Respawning || ready <= round); }
    // A respawn with a known timer, close enough to be worth walking to and waiting for.
    bool waitable(int round, int horizon) const {
        return round >= avoid_until && state == GroupState::Respawning && ready > round && ready - round <= horizon;
    }
};
inline bool bank_now(int bag, int distance, int submitted, int winning) {
    return bag > 0 && (bag >= (DZ_ON(HOARD) ? 48 : DZ_ON(BANK_BIG) ? 45 : config::bank_bag) || (distance <= 8 && bag >= (DZ_ON(BANK_NEAR_MIN) ? 15 : 1)) ||
        submitted + bag >= winning);
}
}
