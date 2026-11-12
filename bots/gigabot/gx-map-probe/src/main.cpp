#include <algorithm>
#include <cambc.h>
#include <cstdio>
#include <vector>

namespace bc = cambc;
namespace d = cambc::detail;

void record_map() {
    std::uint32_t n = 0;
    d::check(d::sdk_map_num_camp_groups(&n));
    std::vector<std::uint32_t> groups(n);
    d::check(d::sdk_map_camp_groups(groups.data(), n, &n));
    std::printf("GXMAP %u %u %u\n", bc::map::width(), bc::map::height(), n);
    for (std::uint32_t handle : groups) {
        d::camp_group_info g{};
        d::check(d::sdk_map_camp_group(handle, &g));
        std::uint32_t k = 0;
        d::check(d::sdk_map_camp_group_num_camps(handle, &k));
        std::vector<std::uint32_t> camps(k);
        if (k > 0) d::check(d::sdk_map_camp_group_camps(handle, camps.data(), k, &k));
        std::printf("GXGROUP %u %u %u %u", handle, g.gems, g.gold, k);
        for (std::uint32_t id : camps) {
            d::camp_info c{};
            d::check(d::sdk_map_camp_info(id, &c));
            std::printf(" %d,%d", c.x, c.y);
        }
        std::putchar('\n');
    }
    std::fflush(stdout);
}

int main() {
    bool recorded = false;
    while (true) {
        if (bc::is_draft()) {
            if (!recorded) record_map(), recorded = true;
            const auto picks = bc::draft::current_draft(bc::team::ally);
            for (int i = 0; i < 11; ++i) {
                const auto pick = static_cast<bc::champion_draft>(i);
                if (std::find(picks.begin(), picks.end(), pick) == picks.end()) {
                    bc::draft::pick(pick);
                    break;
                }
            }
        }
        bc::end_turn();
    }
}
