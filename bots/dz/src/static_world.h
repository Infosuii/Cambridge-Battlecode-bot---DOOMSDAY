#pragma once
#include "kernel.h"
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
    std::unique_ptr<cambc::distance_field> field;
    explicit Group(cambc::map::camp_group g);
    void init_stats();
};
struct Altar { vec2 tile; std::unique_ptr<cambc::distance_field> field; };
class StaticWorld {
    bool loaded_ = false;
    std::size_t fields_cursor_ = 0;
    std::size_t stats_cursor_ = 0;
    bool home_ready_ = false;
    std::size_t tile_group_cursor_=0,tile_member_cursor_=0;
public:
    cambc::bitboard blocked, visited, roots, camp_spawns;
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
    int distance(int g, vec2 p) const;
    int altar_distance(unsigned a, vec2 p) const;
    std::uint64_t field_budget() const {
        // CT-1: ~30k on the measured 100x100 case; provisional conservative
        // envelope, still checked by release fuel traces over the whole pool.
        return 3000 + 4 * cambc::map::width() * cambc::map::height();
    }
    bool walkable(vec2 p) const { return cambc::map::is_in_bounds(p) && !blocked.is_set(p); }
    int group_at(vec2 p) const {
        return cambc::map::is_in_bounds(p) && !tile_groups.empty() ? tile_groups[p.y*cambc::map::width()+p.x] : -1;
    }
};
}
