#include "observation.h"

namespace dz {
void Observation::read(const TurnContext& tc) {
    auto& me = cambc::self();
    state = me.state();
    gold = static_cast<int>(me.gold_count());
    allies.clear(); enemies.clear();
    if (state.is_dead()) { tc.guard(); return; }
    p = me.position(); hp = me.health(); max_hp = me.max_health();
    strength = me.strength(); range = me.attack_range(); bag = static_cast<int>(me.gem_count());
    restrictions = me.restrictions();
    submitted = static_cast<int>(cambc::global_submitted_gems(cambc::team::ally));
    occupied = cambc::vision::champion_tiles() | cambc::vision::camp_tiles() | cambc::vision::teleport_tiles();
    occupied.set(p, false);
    for (auto side : {cambc::team::ally, cambc::team::enemy}) {
        auto& out = side == cambc::team::ally ? allies : enemies;
        for (const auto& c : cambc::vision::champions(side)) {
            if (c == me) continue;
            out.push_back({c, c.position(), c.health(), c.max_health(), c.strength(), c.attack_range()});
        }
    }
    tc.guard();
}
}
