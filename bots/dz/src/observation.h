#pragma once
#include "static_world.h"
#include "camp_threat.h"
#include "failed_moves.h"

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
    float camp_factor = 1, camp_damage = 1; // incoming / outgoing camp multipliers
    bool camps_complete = false;
    std::vector<CampThreat> camps;
    cambc::bitboard occupied;
    LocalMask occupied_mask; // In-Wasm copy of `occupied`.
    FailedMoves failed_moves;
    FailureStreak retry_streak;
    void remember_blocked(vec2 q,int round) {
        const int tile=q.y*cambc::map::width()+q.x;
        // Ordinary collision retries are part of active traffic/crew motion.
        // Intervene only in persistent, stationary travel, before the 30-turn
        // stuck alarm. Key the streak by origin, even if attempted tiles vary.
        if (!failed_moves.persistent_failure(p.y*cambc::map::width()+p.x,round)) return;
        failed_moves.remember(tile,round,DZ_SHORT_BLOCK_MEMORY?2:6);
        occupied.set(q); if(local_masks_valid) occupied_mask.set(q);
    }
    bool is_occupied(vec2 q) const { return local_masks_valid ? occupied_mask.test(q) : occupied.is_set(q); }
    std::vector<SeenChampion> allies, enemies;
    void refresh_self(const TurnContext&);
    void read_camps(const StaticWorld&, const TurnContext&);
    void read(const TurnContext&);
    bool channel() const {
        return state.contains(cambc::champion_state::recalling) || state.contains(cambc::champion_state::submitting_gems) ||
               state.contains(cambc::champion_state::teleporting);
    }
};
}
