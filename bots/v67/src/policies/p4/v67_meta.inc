#include "common.h"
#include "v67_meta.h"

namespace v67meta {
const proxy::Team& selected() {
    return proxy::kTeams[std::clamp(V67_META, 0, 12)];
}

bool draft(std::uint32_t size) {
    std::uint32_t hash = 2166136261u;
    auto mix = [&](std::int64_t value) {
        for (int b = 0; b < 4; ++b) {
            hash ^= static_cast<std::uint32_t>((value >> (8 * b)) & 255);
            hash *= 16777619u;
        }
    };
    namespace d = cambc::detail;
    mix(bc::map::width()); mix(bc::map::height()); mix(size);
    std::uint32_t n = 0;
    if (d::sdk_map_num_camp_groups(&n) || n > 512) return false;
    std::vector<std::uint32_t> groups(n);
    if (d::sdk_map_camp_groups(groups.data(), n, &n)) return false;
    mix(n);
    for (const auto g : groups) {
        d::camp_group_info info{};
        if (!d::sdk_map_camp_group(g, &info)) { mix(info.gold); mix(info.gems); }
        std::uint32_t count = 0;
        if (d::sdk_map_camp_group_num_camps(g, &count)) continue;
        std::vector<std::uint32_t> camps(count);
        if (d::sdk_map_camp_group_camps(g, camps.data(), count, &count)) continue;
        for (const auto c : camps) {
            d::camp_info spec{};
            if (!d::sdk_map_camp_info(c, &spec)) { mix(spec.x); mix(spec.y); mix(spec.type); }
        }
    }
    const auto& team = selected();
    const bc::champion_draft* order = team.fallback;
    int count = team.n_fallback;
    for (int i = 0; i < team.n_maps; ++i)
        if (team.maps[i].key == hash) { order = team.maps[i].picks; count = team.maps[i].n; break; }
    const auto chosen = bc::draft::current_draft(bc::team::ally);
    for (int i = 0; i < count; ++i)
        if (std::find(chosen.begin(), chosen.end(), order[i]) == chosen.end()) {
            bc::draft::pick(order[i]);
            return true;
        }
    for (int i = 0; i < team.n_fallback; ++i)
        if (std::find(chosen.begin(), chosen.end(), team.fallback[i]) == chosen.end()) {
            bc::draft::pick(team.fallback[i]);
            return true;
        }
    return false;
}
}
