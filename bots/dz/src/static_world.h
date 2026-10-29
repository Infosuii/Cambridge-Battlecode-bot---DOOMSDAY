#pragma once
#include "kernel.h"
#include "local_mask.h"
#include <memory>

namespace dz {
using cambc::vec2;
struct Group {
    cambc::map::camp_group sdk;
    std::vector<vec2> tiles;
    std::vector<float> initial_hp;
    std::vector<float> initial_strength;
    std::vector<int> attack_ranges;
    float max_hp = 0, strength = 0;
    bool cluster = true;
    vec2 center{}; int radius = 0; // Chebyshev bound of the spawn tiles.
    std::vector<vec2> approach; bool approach_ready = false; // Walkable non-spawn tiles touching the group.
    std::unique_ptr<cambc::distance_field> field;
    explicit Group(cambc::map::camp_group g);
    void init_stats();
};
struct Altar {
    vec2 tile; std::unique_ptr<cambc::distance_field> field;
    // When every walkable neighbour is a camp spawn tile: the groups and the
    // (group, member) on each neighbour. One dead member opens the altar.
    std::vector<int> gates;
    std::vector<std::pair<int,int>> gate_members;
    std::vector<int> near_groups; // Groups with a tile within 3 of the altar.
};
class StaticWorld {
    bool loaded_ = false;
    std::size_t fields_cursor_ = 0;
    std::size_t stats_cursor_ = 0;
    bool home_ready_ = false, masks_ready_ = false;
    std::size_t tile_group_cursor_=0,tile_member_cursor_=0;
public:
    cambc::bitboard blocked, visited, roots, camp_spawns;
    LocalMask blocked_mask, spawns_mask, bushes_mask, enemy_spawn_mask; // In-Wasm copies (see local_mask.h).
    std::vector<int> tile_groups;
    cambc::distance_field home;
    std::vector<Group> groups;
    std::vector<Altar> altars;
    std::vector<cambc::champion> allies;
    unsigned slot = 0;
    bool ready = false;
    void load_roster(const TurnContext&);
    void boot(const TurnContext&);
    void build_one_field(const TurnContext&, int preferred = -1);
    // Null until it can be built within the remaining budget.
    const std::vector<vec2>* approach_tiles(int g, const TurnContext& tc);
    int distance(int g, vec2 p) const;
    // Never above distance(): a cheap bound for pruning candidates.
    int distance_floor(int g, vec2 p) const {
        const auto& group = groups[g];
        return std::max(0, static_cast<int>(p.chebyshev_distance(group.center)) - group.radius);
    }
    int altar_distance(unsigned a, vec2 p) const;
    std::uint64_t field_budget() const {
        // CT-1: ~30k on the measured 100x100 case; provisional conservative
        // envelope, still checked by release fuel traces over the whole pool.
        return 3000 + 4 * cambc::map::width() * cambc::map::height();
    }
    bool walkable(vec2 p) const {
        if (local_masks_valid) return blocked_mask.in_bounds(p) && !blocked_mask.test(p);
        return cambc::map::is_in_bounds(p) && !blocked.is_set(p);
    }
    bool is_spawn(vec2 p) const { return local_masks_valid ? spawns_mask.test(p) : camp_spawns.is_set(p); }
    // A champion inside its own spawn is fully healed every turn: attacking it
    // only burns our attack (and a ranged body's move). 00reverse-spiral: a
    // Vesper dealt 100,935 damage to an idle Varg healed 102,135, all game.
    bool in_enemy_spawn(vec2 p) const {
        return local_masks_valid ? enemy_spawn_mask.test(p) : cambc::map::spawn_region(cambc::team::enemy).is_set(p);
    }
    bool is_bush(vec2 p) const { return local_masks_valid ? bushes_mask.test(p) : cambc::map::bushes().is_set(p); }
    int group_at(vec2 p) const {
        return cambc::map::is_in_bounds(p) && !tile_groups.empty() ? tile_groups[p.y*cambc::map::width()+p.x] : -1;
    }
};
}
