// Draft: the imitated team's lineup for this map (team_tables.h), else its overall pick order, else any free pick.
#include <algorithm>
#include <cstring>
#include <vector>

#include "common.h"
#include "draft.h"
#include "team_tables.h"
#include "weights.h"

namespace bc = cambc;

const proxy::Team& imitated_team() {
    if (MIMIC_TEAM >= 0 && MIMIC_TEAM < mc::kNumTeams)
        for (const auto& t : proxy::kTeams)
            if (std::strcmp(t.name, mc::kTeamNames[MIMIC_TEAM]) == 0) return t;
    return proxy::kTeams[0]; // "top": all top teams pooled
}

namespace {

// The map's key in team_tables.h: FNV-1a over size, draft size and the camp layout (identical to the function the
// tables were keyed with, bots/proxy/src/draft.cpp proxy_map_key).
std::uint32_t map_key(std::uint32_t size) {
    std::uint32_t h = 2166136261u;
    auto mix = [&h](std::int64_t v) {
        for (int b = 0; b < 4; ++b) {
            h ^= static_cast<std::uint32_t>((v >> (8 * b)) & 0xFF);
            h *= 16777619u;
        }
    };
    namespace api = bc::detail;
    mix(bc::map::width());
    mix(bc::map::height());
    mix(size);
    std::uint32_t n = 0;
    if (api::sdk_map_num_camp_groups(&n) != 0 || n == 0 || n > 512) return h;
    std::vector<std::uint32_t> groups(n);
    if (api::sdk_map_camp_groups(groups.data(), n, &n) != 0) return h;
    mix(n);
    for (std::uint32_t g : groups) {
        api::camp_group_info info{};
        if (api::sdk_map_camp_group(g, &info) == 0) mix(info.gold), mix(info.gems);
        std::uint32_t m = 0;
        if (api::sdk_map_camp_group_num_camps(g, &m) != 0 || m == 0) continue;
        std::vector<std::uint32_t> camps(m);
        if (api::sdk_map_camp_group_camps(g, camps.data(), m, &m) != 0) continue;
        for (std::uint32_t c : camps) {
            api::camp_info spec{};
            if (api::sdk_map_camp_info(c, &spec) == 0) mix(spec.x), mix(spec.y), mix(spec.type);
        }
    }
    return h;
}

constexpr bc::champion_draft kAll[] = {
    bc::champion_draft::vesper_vale, bc::champion_draft::heart_of_ruin, bc::champion_draft::vendetta,
    bc::champion_draft::marcella, bc::champion_draft::ryth, bc::champion_draft::prism, bc::champion_draft::varg,
    bc::champion_draft::ren, bc::champion_draft::cassi_and_issac, bc::champion_draft::tavi,
    bc::champion_draft::stellar, bc::champion_draft::willow};

} // namespace

void play_draft() {
    const auto chosen = bc::draft::current_draft(bc::team::ally);
    std::uint32_t size = 0;
    try {
        size = bc::draft::team_size();
    } catch (...) {
    }
    const proxy::Team& t = imitated_team();
    const bc::champion_draft* list = t.fallback;
    int n = t.n_fallback;
    if (MIMIC_DRAFT) {
        const std::uint32_t key = map_key(size);
        for (int i = 0; i < t.n_maps; ++i)
            if (t.maps[i].key == key) {
                list = t.maps[i].picks;
                n = t.maps[i].n;
                break;
            }
    }
    auto free = [&](bc::champion_draft c) { return std::find(chosen.begin(), chosen.end(), c) == chosen.end(); };
    for (int i = 0; i < n; ++i)
        if (free(list[i])) {
            bc::draft::pick(list[i]);
            return;
        }
    for (int i = 0; i < t.n_fallback; ++i)
        if (free(t.fallback[i])) {
            bc::draft::pick(t.fallback[i]);
            return;
        }
    for (auto c : kAll)
        if (free(c)) {
            bc::draft::pick(c);
            return;
        }
}
