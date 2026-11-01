#include "static_world.h"

namespace dz {
Group::Group(cambc::map::camp_group g) : sdk(std::move(g)) {
#if DZ_ECONOMY_V2
    const auto raw=sdk.camps();ordered_members.assign(raw.begin(),raw.end());
    std::sort(ordered_members.begin(),ordered_members.end(),[](const auto& a,const auto& b){
        return static_cast<unsigned>(static_cast<cambc::handle_camp_t>(a))<static_cast<unsigned>(static_cast<cambc::handle_camp_t>(b));
    });
#endif
    for (const auto& camp : members()) tiles.push_back(camp.spawn_position());
    if (tiles.empty()) return;
    int x0=tiles[0].x,x1=x0,y0=tiles[0].y,y1=y0;
    for (auto t:tiles) { x0=std::min(x0,t.x); x1=std::max(x1,t.x); y0=std::min(y0,t.y); y1=std::max(y1,t.y); }
    center={(x0+x1)/2,(y0+y1)/2};
    for (auto t:tiles) radius=std::max(radius,static_cast<int>(t.chebyshev_distance(center)));
}
void Group::init_stats() {
#if DZ_ECONOMY_V2
    reward_gems=sdk.gem_value();reward_gold=sdk.gold_value();
#endif
    max_hp = 0; strength = 0; cluster = true; initial_hp.clear(); initial_strength.clear(); attack_ranges.clear();
    for (const auto& camp : members()) {
        const auto stats = camp.base_stats();
        initial_hp.push_back(stats.base_health);
        initial_strength.push_back(stats.base_strength);
        attack_ranges.push_back(stats.base_attack_range);
        max_hp += stats.base_health;
        strength += stats.base_strength;
        cluster &= camp.is_gem_cluster() || camp.is_gold_cluster();
    }
}
#if DZ_ECONOMY_V2
bool Group::init_stats_step(const TurnContext& tc) {
    const auto started=fuel_left();
    if(!stats_started) {
        if(!tc.allow(4000+tiles.size()*20))return false;
        initial_hp.resize(tiles.size());initial_strength.resize(tiles.size());attack_ranges.resize(tiles.size());
        reward_gems=sdk.gem_value();reward_gold=sdk.gold_value();
        max_hp=0;strength=0;cluster=true;stats_read=0;stats_started=true;
    }
    const auto camps=members();
    while(stats_read<camps.size()) {
        if(!tc.allow(2500)||started-fuel_left()>18000)return false;
        const auto stats=camps[stats_read].base_stats();
        const bool resource=camps[stats_read].is_gem_cluster()||camps[stats_read].is_gold_cluster();
        tc.guard();
        initial_hp[stats_read]=stats.base_health;initial_strength[stats_read]=stats.base_strength;
        attack_ranges[stats_read]=stats.base_attack_range;
        max_hp+=stats.base_health;strength+=stats.base_strength;cluster&=resource;++stats_read;
    }
    return true;
}
#endif
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
#if DZ_ECONOMY_V2
    const auto boot_start=fuel_left();
#endif
    load_roster(tc);
    if (!loaded_) {
#if DZ_ECONOMY_V2
        if(!metadata_started_) {
            if(!tc.allow(35000))return;
            blocked=cambc::map::walls()|cambc::map::holes()|cambc::map::altars()|cambc::map::spawn_region(cambc::team::enemy);
            auto source=cambc::map::camp_groups();
            std::sort(source.begin(),source.end(),[](const auto& a,const auto& b){return
                static_cast<unsigned>(static_cast<cambc::handle_camp_group_t>(a))<static_cast<unsigned>(static_cast<cambc::handle_camp_group_t>(b));});
            tc.guard();metadata_groups_=std::move(source);groups.reserve(metadata_groups_.size());metadata_started_=true;
            return;
        }
        while(metadata_cursor_<metadata_groups_.size()) {
            if(!tc.allow(16000)||boot_start-fuel_left()>25000)return;
            groups.emplace_back(std::move(metadata_groups_[metadata_cursor_]));++metadata_cursor_;
        }
        if(!tc.allow(20000)||boot_start-fuel_left()>15000)return;
        tile_groups.assign(cambc::map::width()*cambc::map::height(),-1);tile_members.assign(tile_groups.size(),-1);
        for(auto p:cambc::map::altars().positions())altars.push_back({p,nullptr});
        tc.guard();metadata_groups_.clear();loaded_=true;return;
#else
        blocked = cambc::map::walls() | cambc::map::holes() | cambc::map::altars() | cambc::map::spawn_region(cambc::team::enemy);
        auto source = cambc::map::camp_groups();
        groups.clear(); groups.reserve(source.size());
        for (auto& g : source) groups.emplace_back(std::move(g));
        tile_groups.assign(cambc::map::width()*cambc::map::height(),-1);
#if DZ_SIEGE
        tile_members.assign(tile_groups.size(),-1);
#endif
        altars.clear();
        for (auto p : cambc::map::altars().positions()) altars.push_back({p, nullptr});
        loaded_ = true;
        tc.guard();
        return; // Budget metadata, home, designs and altar fields on separate turns.
#endif
    }
    while (tile_group_cursor_<groups.size()) {
        const auto& tiles=groups[tile_group_cursor_].tiles;
        while (tile_member_cursor_<tiles.size()) {
#if DZ_ECONOMY_V2
            if (!tc.allow(2000)||boot_start-fuel_left()>25000) return;
#else
            if (!tc.allow(2000)||tc.fuel0-fuel_left()>25000) return;
#endif
            auto p=tiles[tile_member_cursor_++];
            tile_groups[p.y*cambc::map::width()+p.x]=static_cast<int>(tile_group_cursor_);
#if DZ_SIEGE || DZ_ECONOMY_V2
            tile_members[p.y*cambc::map::width()+p.x]=static_cast<int>(tile_member_cursor_-1);
#endif
            camp_spawns.set(p);
        }
        ++tile_group_cursor_; tile_member_cursor_=0;
    }
    if (!masks_ready_) {
        if (!tc.allow(30000)) return;
        // One export per static mask, then a one-time layout self-check.
        blocked_mask.load(blocked); spawns_mask.load(camp_spawns); bushes_mask.load(cambc::map::bushes());
        enemy_spawn_mask.load(cambc::map::spawn_region(cambc::team::enemy));
#if DZ_ECONOMY_V2
        terrain_mask.load(cambc::map::walls()|cambc::map::holes()|cambc::map::altars());
#endif
        local_masks_valid = DZ_LOCAL_MASKS && blocked_mask.agrees_with(blocked) && spawns_mask.agrees_with(camp_spawns);
#if DZ_TRACE
        { ::dz::TraceScope dz_trace_scope;
        ::dz::trace("DZ_MASKS valid=%d blocked=%u spawns=%u\n",local_masks_valid,blocked_mask.count(),spawns_mask.count());
        }
#endif
        tc.guard(); masks_ready_ = true;
        return;
    }
    if (!home_ready_) {
        if (!tc.allow(field_budget())) return;
        home.compute(blocked, cambc::map::spawn_region(cambc::team::ally), visited);
#if DZ_ECONOMY_V2
        home_distances=home.export_linear_buffer();
#endif
        tc.guard(); home_ready_ = true;
        return;
    }
    while (stats_cursor_ < groups.size()) {
#if DZ_ECONOMY_V2
        if (boot_start - fuel_left() > 25000) return;
        if(!groups[stats_cursor_].init_stats_step(tc))return;
#else
        if (tc.fuel0 - fuel_left() > 25000) return;
        if (!tc.allow(3000 + groups[stats_cursor_].tiles.size() * 500)) return;
        groups[stats_cursor_].init_stats();
#endif
#if DZ_JOB_GEAR
        auto& group=groups[stats_cursor_];group.home_distance=65535;group.home_reachable=true;
        for(auto tile:group.tiles){const int distance=home.get(tile);group.home_distance=std::min(group.home_distance,distance);group.home_reachable&=distance<cambc::distance_field::unreachable;}
#endif
#if DZ_ECONOMY_V2
        for(auto range:groups[stats_cursor_].attack_ranges)maximum_camp_range=std::max(maximum_camp_range,range);
#endif
        tc.guard(); ++stats_cursor_;
    }
#if DZ_ECONOMY_V2
    // All camp designs, terrain, occupancy indices and home navigation are now
    // complete. A singleton can execute income while optional altar indexing
    // continues AFTER its action; channels still require their own admission.
    income_ready=true;
    // Static spatial filtering belongs in resumable boot work. Recomputing the
    // global range and scanning every group per bank forecast could exceed the
    // forecast slice before even finding its first local threat.
    for(auto& altar:altars) {
        if(altar.bank_members_ready)continue;
        while(altar.bank_group<groups.size()) {
            const auto& group=groups[altar.bank_group];
            while(altar.bank_member<group.tiles.size()) {
                if(!tc.allow(6000)||boot_start-fuel_left()>25000)return;
                const unsigned k=altar.bank_member++;
                if(group.tiles[k].chebyshev_distance(altar.tile)<=group.attack_ranges[k]+2*maximum_camp_range+2+cambc::constants::submit_gems_range) {
                    altar.bank_members.emplace_back(altar.bank_group,k);
                    if(group.initial_strength[k]>0)altar.bank_damage_members.emplace_back(altar.bank_group,k);
                }
            }
            ++altar.bank_group;altar.bank_member=0;
        }
        altar.bank_members_ready=true;
    }
#endif
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
#if DZ_SIEGE || DZ_ECONOMY_V2
        altar.distances=altar.field->export_linear_buffer();
#endif
    }
#if DZ_HAS(RING_GATES) || DZ_ECONOMY_V2 || DZ_SIEGE
    // Resumable over turns: one pocket field per altar, then a budgeted group scan.
    const auto ring_start=fuel_left();
    for (auto& altar : altars) {
        if (altar.ring_checked) continue;
        if (!(DZ_ON(RING_GATES) || DZ_ECONOMY_V2 || DZ_SIEGE) || !altar.gates.empty()) { altar.ring_checked=true; continue; }
        if (!altar.pocket) {
            if (!tc.allow(field_budget()+5000)) return;
            roots.clear();
            for (int dx = -1; dx <= 1; ++dx) for (int dy = -1; dy <= 1; ++dy) {
                vec2 q = altar.tile + vec2{dx,dy};
                if (walkable(q)) roots.set(q);
            }
            auto pocket=std::make_unique<cambc::distance_field>();
            pocket->compute(blocked|camp_spawns, roots, visited);
            bool reached=false;
            for (auto s:cambc::map::spawn_region(cambc::team::ally).positions())
                if (pocket->get(s)<cambc::distance_field::unreachable) { reached=true; break; }
            tc.guard();
            if (reached) { altar.ring_checked=true; continue; }
            altar.pocket=std::move(pocket); altar.ring_cursor=0;altar.ring_member_cursor=0;
            return; // Scan on later turns.
        }
        std::vector<std::pair<int,int>> found;
        while (altar.ring_cursor<groups.size()) {
            const auto& tiles=groups[altar.ring_cursor].tiles;
            // A whole large group can exceed an ordinary turn's allowance.
            // Resume at the MEMBER, so size never makes boot impossible.
            while(altar.ring_member_cursor<tiles.size()) {
                if(!tc.allow(5000)||ring_start-fuel_left()>25000)return;
                const auto k=altar.ring_member_cursor;
                bool borders=false;
                for (int dx=-1;dx<=1&&!borders;++dx) for (int dy=-1;dy<=1;++dy) {
                    const vec2 n=tiles[k]+vec2{dx,dy};
                    if (n.x<0||n.y<0||n.x>=cambc::map::width()||n.y>=cambc::map::height()) continue;
                    if (altar.pocket->get(n)<cambc::distance_field::unreachable) { borders=true; break; }
                }
                if (borders) altar.ring_members.push_back({static_cast<int>(altar.ring_cursor),static_cast<int>(k)});
                tc.guard();++altar.ring_member_cursor;
            }
            tc.guard(); ++altar.ring_cursor;altar.ring_member_cursor=0;
        }
        // Publish only a complete gate set.
        for (auto [g,k]:altar.ring_members) {
            if (std::find(altar.gates.begin(),altar.gates.end(),g)==altar.gates.end()) altar.gates.push_back(g);
            altar.gate_members.push_back({g,k});
        }
        altar.pocket.reset(); altar.ring_checked=true;
    }
#endif
#if DZ_ECONOMY_V2
    if(!spawn_exit) {
        if(!tc.allow(field_budget()+5000))return;
        auto field=std::make_unique<cambc::distance_field>();
        field->compute(blocked,~(blocked|camp_spawns),visited);
        tc.guard();spawn_exit=std::move(field);return;
    }
#endif
    ready = true;
#if DZ_TRACE && DZ_ECONOMY_V2
    for(unsigned g=0;g<std::min<std::size_t>(groups.size(),2);++g) {
        TraceScope scope;trace("DZ_GROUP_ID slot=%u group=%u handle=%u center=%d,%d first=%u\n",slot,g,
            static_cast<unsigned>(static_cast<cambc::handle_camp_group_t>(groups[g].sdk)),groups[g].center.x,groups[g].center.y,
            groups[g].members().empty()?~0u:static_cast<unsigned>(static_cast<cambc::handle_camp_t>(groups[g].members()[0])));
    }
#endif
}
void StaticWorld::build_one_field(const TurnContext& tc, int preferred) {
#if DZ_ECONOMY_V2
    if(!requested_navigation_fits(fuel_left(),field_budget(),preferred>=0)||groups.empty())return;
#else
    if (!tc.allow(field_budget()) || tier_for(fuel_left()) != Tier::Full || groups.empty()) return;
#endif
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
#if DZ_BANK_AWARE_RATE
int StaticWorld::delivery_distance(unsigned index,unsigned altar,const TurnContext& tc) {
    auto& g=groups[index];
    if(g.delivery_distances.size()!=altars.size())g.delivery_distances.assign(altars.size(),-1);
    auto& cached=g.delivery_distances[altar];
    if(cached>=0)return cached;
    if(!tc.allow(4000+200*g.tiles.size()))return -1;
    int nearest=cambc::distance_field::unreachable;
    for(auto tile:g.tiles)nearest=std::min(nearest,altar_distance(altar,tile));
    tc.guard();cached=nearest;return cached;
}
#endif
}
