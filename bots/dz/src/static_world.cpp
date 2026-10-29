#include "static_world.h"

namespace dz {
Group::Group(cambc::map::camp_group g) : sdk(std::move(g)) {
    for (const auto& camp : sdk.camps()) tiles.push_back(camp.spawn_position());
    if (tiles.empty()) return;
    int x0=tiles[0].x,x1=x0,y0=tiles[0].y,y1=y0;
    for (auto t:tiles) { x0=std::min(x0,t.x); x1=std::max(x1,t.x); y0=std::min(y0,t.y); y1=std::max(y1,t.y); }
    center={(x0+x1)/2,(y0+y1)/2};
    for (auto t:tiles) radius=std::max(radius,static_cast<int>(t.chebyshev_distance(center)));
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
    if (!masks_ready_) {
        if (!tc.allow(30000)) return;
        // One export per static mask, then a one-time layout self-check.
        blocked_mask.load(blocked); spawns_mask.load(camp_spawns); bushes_mask.load(cambc::map::bushes());
        local_masks_valid = DZ_LOCAL_MASKS && blocked_mask.agrees_with(blocked) && spawns_mask.agrees_with(camp_spawns);
#if DZ_TRACE
        std::printf("DZ_MASKS valid=%d blocked=%u spawns=%u\n",local_masks_valid,blocked_mask.count(),spawns_mask.count());
#endif
        tc.guard(); masks_ready_ = true;
        return;
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
        bool open=false; altar.gates.clear(); altar.gate_members.clear();
        for (int dx = -1; dx <= 1; ++dx) for (int dy = -1; dy <= 1; ++dy) {
            vec2 p = altar.tile + vec2{dx,dy};
            if (!walkable(p)) continue;
            roots.set(p);
            const int g=group_at(p);
            if (g<0) { open=true; continue; }
            if (std::find(altar.gates.begin(),altar.gates.end(),g)==altar.gates.end()) altar.gates.push_back(g);
            const auto& tiles=groups[g].tiles;
            const int member=static_cast<int>(std::find(tiles.begin(),tiles.end(),p)-tiles.begin());
            altar.gate_members.push_back({g,member});
        }
        if (open) { altar.gates.clear(); altar.gate_members.clear(); }
        altar.near_groups.clear();
        for (unsigned g=0;g<groups.size();++g)
            for (auto t:groups[g].tiles) if (t.chebyshev_distance(altar.tile)<=3) { altar.near_groups.push_back(static_cast<int>(g)); break; }
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
const std::vector<vec2>* StaticWorld::approach_tiles(int index, const TurnContext& tc) {
    auto& group = groups[index];
    if (group.approach_ready) return &group.approach;
    // Roughly 1k fuel per member tile (nine neighbour checks). Building a
    // large vault group in one go exhausted every body on 00vault.
    if (!tc.allow(3000 + 1200 * group.tiles.size())) return nullptr;
    // Static boundary, computed once: the per-turn scan of every member's
    // neighbourhood cost ~63k fuel for large wolf packs (02the-pack).
    LocalMask seen; seen.resize();
    for (auto t : group.tiles)
        for (int dx = -1; dx <= 1; ++dx) for (int dy = -1; dy <= 1; ++dy) {
            const vec2 p = t + vec2{dx,dy};
            if (seen.test(p) || !walkable(p) || is_spawn(p)) continue;
            seen.set(p); group.approach.push_back(p);
        }
    tc.guard(); group.approach_ready = true;
    return &group.approach;
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
