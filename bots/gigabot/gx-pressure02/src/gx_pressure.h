#pragma once

#if GX_PRESSURE_ITEMS > 0
// When a healthy economy build meets a real fight deficit, retain its opening
// emblems and bring a full combat milestone forward while pressure is recent.
void Bot::gx_update_pressure() {
    if (round < 50 || w.enemies.empty() ||
        bc::fuel_remaining() < 36000) return;
    int close = 0;
    float enemy_items = 0.0f;
    for (const auto& e : w.enemies) {
        if (e.hp <= 0.0f || cheb(pos, e.pos) > e.range + 3) continue;
        ++close;
        enemy_items = std::max(enemy_items, items_of(e.type, e.max_hp, e.strength, e.focus));
    }
    if (!close) return;
    const float own = my_items();
    const bool hurt = hp < max_hp * 0.72f && prev_hp - hp > max_hp * 0.10f;
    if (enemy_items > own + 3.0f && (close >= 2 || hurt))
        gx_pressure_round = round;
}

namespace gx {
template <typename Inventory>
inline void add_pressure_emblem(std::vector<BuildStep>& plan, bc::champion_type type, const Inventory& counts, int gold) {
    if (mobility_farming_map || plan.empty()) return;
    using ct = bc::champion_type;
    using it = bc::item_type;
    const bool caster = type == ct::cassi || type == ct::stellar || type == ct::prism ||
        type == ct::willow || type == ct::marcella || type == ct::heart_of_ruin;
    const auto item = type == ct::ryth ? it::bruiser_shard_of_health :
        caster ? it::power_shard_of_focus : it::power_shard_of_strength;
    auto owned = [&](it shard) {
        int have = static_cast<int>(counts[shard]);
        if (const auto result = shard.result()) have += static_cast<int>(counts[*result] * shard.combine_count());
        return have;
    };
    const auto place = plan.begin() + std::min<std::size_t>(plan.size(), GX_PRESSURE_ITEMS);
    for (auto at = plan.begin(); at != place; ++at)
        if (owned(at->item) < at->total) return;
    const int next = static_cast<int>(item.combine_count()) - owned(item);
    if (next <= 0 || gold < next * static_cast<int>(item.cost()) + 20) return;
    auto already = std::find_if(plan.begin(), plan.end(), [&](const BuildStep& s) { return s.item == item; });
    if (already < place) return;
    plan.insert(place, {item, static_cast<int>(item.combine_count())});
}
} // namespace gx
#endif
