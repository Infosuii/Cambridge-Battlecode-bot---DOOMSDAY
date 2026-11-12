// Local fully charged metadata probe for the official release engine.
#include <cambc.h>
#include <algorithm>
#include <cstdio>

namespace bc = cambc;

static void print_metadata() {
    for (int i = 0; i < 13; ++i) {
        bc::detail::champion_design design{};
        bc::detail::check(bc::detail::sdk_champion_design(i, &design));
        const auto& stats = design.base_stats;
        std::printf("BALANCE_CHAMP %d %.9g %.9g %.9g %.9g %.9g %.9g\n", i,
                    stats.base_health, stats.base_strength, stats.base_focus,
                    stats.health_growth, stats.strength_growth, stats.focus_growth);
    }
    for (const auto item : {bc::item_type::skirmish_emblem_of_strength,
                            bc::item_type::greed_emblem_of_strength,
                            bc::item_type::greed_emblem_of_focus,
                            bc::item_type::greed_emblem_of_health}) {
        const auto info = item.info();
        std::printf("BALANCE_ITEM %u %d %d %d %.9g\n", static_cast<unsigned>(static_cast<bc::item_type::enum_type>(item)),
                    info.health_points, info.strength_points, info.focus_points, info.passive_magnitude);
    }
}

int main() {
    bool printed = false;
    while (true) {
        if (bc::is_draft()) {
            if (!printed) {
                print_metadata();
                printed = true;
            }
            const auto picked = bc::draft::current_draft(bc::team::ally);
            for (int i = 0; i < 11; ++i) {
                const auto candidate = static_cast<bc::champion_draft>(i);
                if (std::find(picked.begin(), picked.end(), candidate) == picked.end()) {
                    bc::draft::pick(candidate);
                    break;
                }
            }
        }
        bc::end_turn();
    }
}
