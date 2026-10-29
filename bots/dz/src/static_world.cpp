#include "static_world.h"

namespace dz {
Group::Group(cambc::map::camp_group g) : sdk(std::move(g)) {
    for (const auto& camp : sdk.camps()) tiles.push_back(camp.spawn_position());
}
void Group::init_stats() {
    max_hp = 0; strength = 0; cluster = true; initial_hp.clear(); initial_strength.clear(); attack_ranges.clear();
    for (const auto& camp : sdk.camps()) {
        const auto stats = camp.base_stats();
        initial_hp.push_back(stats.base_health);
        initial_strength.push_back(stats.base_strength);
        attack_ranges.push_back(stats.base_attack_range);
        max_hp += stats.base_health;
        strength += stats.base_strength;
        cluster &= camp.is_gem_cluster() || camp.is_gold_cluster();
    }
}
void StaticWorld::load_roster(const TurnContext& tc) {
    if (!allies.empty()) return;
    auto roster=cambc::champions(cambc::team::ally);
    std::sort(roster.begin(),roster.end(),[](const auto& a,const auto& b) {
        return static_cast<std::uint32_t>(static_cast<cambc::handle_champion_t>(a)) <
            static_cast<std::uint32_t>(static_cast<cambc::handle_champion_t>(b));
    });
    unsigned own=0;
    while (own<roster.size()&&roster[own]!=cambc::self()) ++own;
    if (own==roster.size()) throw std::logic_error("self missing from allied roster");
    tc.guard(); allies=std::move(roster); slot=own;
}
void StaticWorld::boot(const TurnContext& tc) {
    if (ready) return;
    load_roster(tc);
    if (!loaded_) {
        blocked = cambc::map::walls() | cambc::map::holes() | cambc::map::altars() | cambc::map::spawn_region(cambc::team::enemy);
        auto source = cambc::map::camp_groups();
        groups.clear(); groups.reserve(source.size());
        for (auto& g : source) groups.emplace_back(std::move(g));
        tile_groups.assign(cambc::map::width()*cambc::map::height(),-1);
        altars.clear();
        for (auto p : cambc::map::altars().positions()) altars.push_back({p, nullptr});
        loaded_ = true;
        tc.guard();
        return; // Budget metadata, home, designs and altar fields on separate turns.
    }
    while (tile_group_cursor_<groups.size()) {
        const auto& tiles=groups[tile_group_cursor_].tiles;
        while (tile_member_cursor_<tiles.size()) {
            if (!tc.allow(2000)||tc.fuel0-cambc::fuel_remaining()>25000) return;
            auto p=tiles[tile_member_cursor_++];
            tile_groups[p.y*cambc::map::width()+p.x]=static_cast<int>(tile_group_cursor_);
            camp_spawns.set(p);
        }
        ++tile_group_cursor_; tile_member_cursor_=0;
    }
    if (!home_ready_) {
        if (!tc.allow(field_budget())) return;
        home.compute(blocked, cambc::map::spawn_region(cambc::team::ally), visited);
        tc.guard(); home_ready_ = true;
        return;
    }
    while (stats_cursor_ < groups.size()) {
        if (tc.fuel0 - cambc::fuel_remaining() > 25000) return;
        if (!tc.allow(3000 + groups[stats_cursor_].tiles.size() * 500)) return;
        groups[stats_cursor_].init_stats();
        tc.guard(); ++stats_cursor_;
    }
    // Transactional field publication: no partially computed cache becomes usable.
    for (auto& altar : altars) {
        if (altar.field) continue;
        if (!tc.allow(field_budget())) return;
        roots.clear();
        for (int dx = -1; dx <= 1; ++dx) for (int dy = -1; dy <= 1; ++dy) {
            vec2 p = altar.tile + vec2{dx,dy};
            if (walkable(p)) roots.set(p);
        }
        auto field = std::make_unique<cambc::distance_field>();
        field->compute(blocked, roots, visited);
        tc.guard(); altar.field = std::move(field);
    }
    ready = true;
}
void StaticWorld::build_one_field(const TurnContext& tc, int preferred) {
    if (!tc.allow(field_budget()) || tier_for(cambc::fuel_remaining()) != Tier::Full || groups.empty()) return;
    int selected = -1;
    if (preferred >= 0 && preferred < static_cast<int>(groups.size()) && !groups[preferred].field) selected = preferred;
    else {
        for (std::size_t i = 0; i < groups.size(); ++i) {
            const auto index = (fields_cursor_ + i) % groups.size();
            if (!groups[index].field) { selected = static_cast<int>(index); fields_cursor_ = index + 1; break; }
        }
    }
    if (selected < 0) return;
    roots.clear();
    for (auto p : groups[selected].tiles) {
        if (!tc.allow(field_budget()+3000)) return;
        if (walkable(p)) roots.set(p);
    }
    auto field = std::make_unique<cambc::distance_field>();
    field->compute(blocked, roots, visited);
    tc.guard(); groups[selected].field = std::move(field);
}
int StaticWorld::distance(int g, vec2 p) const {
    const auto& group = groups[g];
    if (group.field) return group.field->get(p);
    int result = 65535;
    for (auto tile : group.tiles) result = std::min(result, static_cast<int>(p.chebyshev_distance(tile)));
    return (result * 13 + 9) / 10;
}
int StaticWorld::altar_distance(unsigned a, vec2 p) const {
    return altars[a].field ? altars[a].field->get(p) : 65535;
}
}
