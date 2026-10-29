#include "gear.h"

namespace dz {
namespace {
using F = cambc::item_family;
using S = cambc::item_stat;
struct Step { F family; S stat; };
struct Build { std::array<Step,3> emblems; S power; };
// Per-champion openers from the elite purchase ledger (ELITE_META_RESEARCH,
// 30 top-team games, 2026-10-29): Treasure- or Jungle-led development, then
// the champion's main stat. Variant B keeps Monster in the first three for
// damage dealers: Treasure-first without it slowed clears against idle
// (dz-gear-idle-01). Our clear model prices basic attacks, so Strength.
Build build_for(cambc::champion_type type) {
    using T = cambc::champion_type;
    switch (type) {
    case T::vesper_vale: return {{{{F::treasure,S::strength},{F::monster,S::strength},{F::jungle,S::strength}}},S::strength};
    case T::marcella: return {{{{F::treasure,S::strength},{F::monster,S::strength},{F::durability,S::health}}},S::strength};
    case T::heart_of_ruin: return {{{{F::jungle,S::health},{F::treasure,S::health},{F::monster,S::health}}},S::health};
    case T::ryth: return {{{{F::treasure,S::health},{F::jungle,S::health},{F::monster,S::health}}},S::health};
    case T::varg: return {{{{F::monster,S::strength},{F::treasure,S::strength},{F::jungle,S::strength}}},S::strength};
    default: return {{{{F::monster,S::strength},{F::treasure,S::strength},{F::jungle,S::strength}}},S::strength};
    }
}
}
bool fixed_shop(const TurnContext& tc, Actuator& act) {
    auto& me = cambc::self();
    const auto build = build_for(me.champion_name());
    if (!me.can_buy(cambc::get_item_enum(build.emblems.front().family, build.emblems.front().stat))) return false;
    bool changed = false;
    for (int count = 0; count < 16 && tc.allow(2000); ++count) {
        auto owned = me.item_count();
        auto selected = cambc::get_item_enum(F::power, build.power);
        for (auto step : build.emblems) {
            auto shard = cambc::get_item_enum(step.family, step.stat);
            auto result = shard.result();
            if (!result || owned[*result] == 0) { selected = shard; break; }
        }
        if (!me.can_buy(selected) || !act.buy(selected)) break;
        changed = true;
    }
    return changed;
}
}
