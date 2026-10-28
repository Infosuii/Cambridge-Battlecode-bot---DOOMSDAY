#pragma once
#include "kernel.h"
#include <memory>

namespace dz {
using cambc::vec2;
struct Group {
    cambc::map::camp_group sdk;
    std::vector<vec2> tiles;
    std::vector<float> initial_hp;
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
public:
    cambc::bitboard blocked, visited, roots;
    cambc::distance_field home;
    std::vector<Group> groups;
    std::vector<Altar> altars;
    std::vector<cambc::champion> allies;
    unsigned slot = 0;
    bool ready = false;
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
};
}
