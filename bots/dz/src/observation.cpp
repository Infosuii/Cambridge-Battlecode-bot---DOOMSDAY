#include "observation.h"

namespace dz {
void Observation::refresh_self(const TurnContext& tc) {
    auto& me = cambc::self();
    state = me.state();
    gold = static_cast<int>(me.gold_count());
    if (state.is_dead()) { tc.guard(); return; }
    p = me.position(); hp = me.health(); max_hp = me.max_health();
    strength = me.strength(); range = me.attack_range(); bag = static_cast<int>(me.gem_count());
    restrictions = me.restrictions();
    submitted = static_cast<int>(cambc::global_submitted_gems(cambc::team::ally));
    {
        // Objective selection prices camp fights with these. Jungle and
        // Durability multiply; Monster scales damage after stat gains.
        auto owned = me.item_count(); float jungle=0,durability=0,monster=0;
        for (auto stat:{cambc::item_stat::strength,cambc::item_stat::focus,cambc::item_stat::health}) {
            auto j=cambc::get_item_enum(cambc::item_family::jungle,stat,false);
            auto d=cambc::get_item_enum(cambc::item_family::durability,stat,false);
            auto m=cambc::get_item_enum(cambc::item_family::monster,stat,false);
            if (owned[j]) jungle=std::max(jungle,j.passive_magnitude());
            if (owned[d]) durability=std::max(durability,d.passive_magnitude());
            if (owned[m]) monster=std::max(monster,m.passive_magnitude());
        }
        camp_factor=(1-jungle)*(1-durability);
        camp_damage=1+monster;
    }
    tc.guard();
}
void Observation::read_camps(const StaticWorld& world,const TurnContext& tc) {
    camps.clear(); camps_complete=true;
    auto awake=cambc::vision::awake_camp_tiles();
    auto budget=fuel_left();
    for (const auto& g:world.groups) {
        if (g.strength<=0) continue;
        auto members=g.sdk.camps();
        for (unsigned i=0;i<members.size();++i) {
            if (g.initial_strength[i]<=0) continue;
            auto tile=g.tiles[i];
            if (p.chebyshev_distance(tile)>12) continue;
            if (!tc.allow(5000) || budget-fuel_left()>10000 || camps.size()>=32) { camps_complete=false; return; }
            // Awake masks contain visible camps only. A hidden damaging spawn in
            // attack range is uncertainty, not evidence that no camp can hit us.
            if (!cambc::vision::in_vision(tile)) {
                if (p.chebyshev_distance(tile)<=g.attack_ranges[i]) { camps_complete=false; return; }
                continue;
            }
            if (!awake.is_set(tile)) continue;
            camps.push_back({{tile.x,tile.y},members[i].strength()*camp_factor,g.attack_ranges[i]});
        }
    }
    tc.guard();
}
void Observation::read(const TurnContext& tc) {
    refresh_self(tc);
    allies.clear(); enemies.clear();
    if (state.is_dead()) return;
    occupied = cambc::vision::champion_tiles() | cambc::vision::camp_tiles() | cambc::vision::teleport_tiles();
    occupied.set(p, false);
    if (local_masks_valid) occupied_mask.load(occupied);
    for (auto side : {cambc::team::ally, cambc::team::enemy}) {
        auto& out = side == cambc::team::ally ? allies : enemies;
        for (const auto& c : cambc::vision::champions(side)) {
            if (c == cambc::self()) continue;
            out.push_back({c, c.position(), c.health(), c.max_health(), c.strength(), c.attack_range()});
        }
    }
    tc.guard();
}
}
