#pragma once
#include "static_world.h"

namespace dz {
struct SeenChampion {
    cambc::champion sdk;
    vec2 p;
    float hp, max_hp, strength;
    int range;
};
struct Observation {
    cambc::champion_state state;
    cambc::buff_restrictions restrictions;
    vec2 p;
    float hp = 0, max_hp = 1, strength = 0;
    int range = 1, bag = 0, gold = 0, submitted = 0;
    cambc::bitboard occupied;
    std::vector<SeenChampion> allies, enemies;
    void read(const TurnContext&);
    bool channel() const {
        return state.contains(cambc::champion_state::recalling) || state.contains(cambc::champion_state::submitting_gems) ||
               state.contains(cambc::champion_state::teleporting);
    }
};
}
