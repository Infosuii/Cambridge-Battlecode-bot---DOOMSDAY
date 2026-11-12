#include "opening_cache.h"
namespace dz {
#if DZ_ECONOMY_V2 && DZ_LIFECYCLE
const opening_catalog::Catalog& opening_cache() {
    static opening_catalog::Catalog catalog;static bool loaded=false;
    if(!loaded){catalog.load({cambc::draft_memory.data(),cambc::draft_memory.size()},cambc::map::width(),cambc::map::height());loaded=true;}
    return catalog;
}
opening_catalog::Design camp_design(const cambc::camp& camp) {
    static std::array<std::optional<opening_catalog::Design>,16> designs;
    // SDK4 already stores kind and spawn position in the camp wrapper.
    const unsigned kind=static_cast<unsigned>(camp.kind());
    if(kind<designs.size()&&designs[kind])return *designs[kind];
    if(const auto design=opening_cache().design(kind)){designs[kind]=*design;return *design;}
    const auto stats=camp.base_stats();opening_catalog::Design design{stats.base_health,stats.base_strength,stats.base_attack_range,kind};
    if(kind<designs.size())designs[kind]=design;return design;
}
void publish_opening_cache(const TurnContext& tc,Actuator& act) {
    static bool written=false;if(written||!tc.allow(30000))return;
    std::array<bool,16> known{};std::vector<opening_catalog::Design> designs;
    for(const auto& group:cambc::map::camp_groups())for(const auto& camp:group.camps()) {
        if(!tc.allow(10000))return;
        const auto kind=static_cast<unsigned>(camp.kind());if(kind>=known.size())return;
        if(!known[kind]){const auto stats=camp.base_stats();designs.push_back({stats.base_health,stats.base_strength,stats.base_attack_range,kind});known[kind]=true;}
    }
    const auto bytes=opening_catalog::encode(cambc::map::width(),cambc::map::height(),designs,{},cambc::constants::draft_memory_bytes);
    if(!bytes.empty())written=act.draft_bytes(bytes);
}
#endif
}
