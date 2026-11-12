// Read the existing map classifier once during the fully charged draft phase.
#include "world.h"
#include "x1_atlas.h"
#include "x1_categories.h"
#include <algorithm>
#include <cstdio>

int main() {
    World world;
    bool printed = false;
    while (true) {
        if (bc::is_draft()) {
            if (!printed) {
                world.init();
                // The frozen atlas uses Vendetta's initial mobility model.
                world.enable_bridges();
                const auto features = x1_atlas::compute(world, static_cast<int>(bc::draft::team_size()));
                x1_atlas::print(features, bc::detail::sdk_my_team());
                std::printf("CODEX_CATEGORY %d\n", x1_categories::classify(features) + 1);
                printed = true;
            }
            const auto picked = bc::draft::current_draft(team::ally);
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
