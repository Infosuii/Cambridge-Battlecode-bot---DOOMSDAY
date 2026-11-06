#include <cambc.h>
#include <algorithm>
#include <cstdio>
#include <variant>
namespace bc = cambc;

static void metadata() {
    const auto start = bc::fuel_remaining();
    for (int i = 0; i < 13; ++i) {
        bc::champion design{static_cast<bc::champion_type>(i)};
        const auto abilities = design.abilities();
        for (int slot = 0; slot < 2; ++slot) {
            const auto& info = abilities[slot].info();
            if (!info) continue;
            std::visit([&](const auto& a) {
                using A = std::decay_t<decltype(a)>;
                float range = 0, radius = 0, modifier = 0;
                if constexpr (requires { a.range; }) range = a.range;
                if constexpr (requires { a.radius; }) radius = a.radius;
                if constexpr (requires { a.modifier; }) modifier = a.modifier;
                std::printf("ABILITY %d %d %u %.9g %.9g %.9g %d %d %d %d %d\n", i, slot,
                    static_cast<unsigned>(A::kind), range, radius, modifier,
                    a.valid_targets.contains(bc::ability_target_mask::camps),
                    a.valid_targets.contains(bc::ability_target_mask::ground),
                    a.valid_targets.contains(bc::ability_target_mask::enemies),
                    a.exclusive_with_movement, a.max_cooldown);
            }, *info);
        }
    }
    std::printf("ABILITY_COST %llu\n", static_cast<unsigned long long>(start - bc::fuel_remaining()));
}

int main() {
    bool printed = false;
    for (;;) {
        if (!bc::is_draft()) bc::resign();
        if (!printed) { metadata(); printed = true; }
        const auto selected = bc::draft::current_draft(bc::team::ally);
        for (int i = 0; i < 11; ++i) {
            const auto pick = static_cast<bc::champion_draft>(i);
            if (std::find(selected.begin(), selected.end(), pick) == selected.end()) {
                bc::draft::pick(pick);
                break;
            }
        }
        bc::end_turn();
    }
}
