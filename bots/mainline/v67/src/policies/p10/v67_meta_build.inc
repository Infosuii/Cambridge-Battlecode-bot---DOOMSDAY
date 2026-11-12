#if V67_META >= 0
{
    const auto& team = v67meta::selected();
    const proxy::Items* items = nullptr;
    for (int i = 0; i < team.n_items; ++i) if (team.items[i].hero == t) items = &team.items[i];
    if (!items)
        for (int i = 0; i < proxy::kTeams[0].n_items; ++i) if (proxy::kTeams[0].items[i].hero == t) items = &proxy::kTeams[0].items[i];
    if (items) {
        std::vector<BuildStep> meta_plan;
        int main = 0, health = 0;
        for (int i = 0; i < items->n_open; ++i) {
            const auto& step = items->open[i];
            meta_plan.push_back({step.item, step.total});
            if (step.item == items->main) main = std::max(main, step.total);
            if (step.item == items->health) health = std::max(health, step.total);
        }
        for (int i = 1; i <= 20; ++i) {
            meta_plan.push_back({items->main, main + 5 * i});
            if (items->per_health > 0 && i % items->per_health == 0)
                meta_plan.push_back({items->health, health + 5 * (i / items->per_health)});
        }
        return meta_plan;
    }
}
#endif
