#include "gear.h"

namespace dz {
void fixed_shop(const TurnContext& tc, Actuator& act) {
    auto& me = cambc::self();
    // Fixed SafeMode build. The marginal-value gear model is not yet validated.
    const auto type = me.champion_name();
    const bool runner = type == cambc::champion_type::vesper_vale || type == cambc::champion_type::tavi;
    const auto stat = type == cambc::champion_type::heart_of_ruin || type == cambc::champion_type::ryth ?
        cambc::item_stat::health : cambc::item_stat::strength;
    const std::array<cambc::item_family, 5> build = runner ?
        std::array{cambc::item_family::capture, cambc::item_family::prospector, cambc::item_family::jungle, cambc::item_family::monster, cambc::item_family::durability} :
        std::array{cambc::item_family::monster, cambc::item_family::jungle, cambc::item_family::durability, cambc::item_family::capture, cambc::item_family::home};
    for (int count = 0; count < 16 && tc.allow(2000); ++count) {
        auto owned = me.item_count();
        auto selected = cambc::get_item_enum(cambc::item_family::power, stat);
        for (auto family : build) {
            auto shard = cambc::get_item_enum(family, stat);
            auto result = shard.result();
            if (!result || owned[*result] == 0) { selected = shard; break; }
        }
        if (!me.can_buy(selected) || !act.buy(selected)) break;
    }
}
}
