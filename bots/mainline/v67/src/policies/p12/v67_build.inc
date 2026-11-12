// v67 experiment: early damage and useful mixed stats instead of a long passive-item opening.
#if V67_BUILD
{
    using ct = bc::champion_type;
    const bool focus_user = t == ct::heart_of_ruin || t == ct::cassi || t == ct::stellar ||
                            t == ct::prism || t == ct::marcella;
    const bool fragile = t == ct::cassi || t == ct::stellar || t == ct::prism;
    const it main = focus_user ? it::bruiser_shard_of_focus : it::bruiser_shard_of_strength;
    std::vector<BuildStep> v67_plan;
    if (V67_BUILD == 1) {
        if (fragile) v67_plan.push_back({it::durability_shard_of_health, 5});
        else v67_plan.push_back({focus_user ? it::jungle_shard_of_focus : it::jungle_shard_of_strength, 5});
        v67_plan.push_back({main, 5});
        if (!fragile) v67_plan.push_back({it::durability_shard_of_health, 5});
    } else {
        v67_plan.push_back({main, 5});
        v67_plan.push_back({it::durability_shard_of_health, 5});
        v67_plan.push_back({focus_user ? it::jungle_shard_of_focus : it::jungle_shard_of_strength, 5});
    }
    for (int n = 10; n <= 80; n += 5) {
        v67_plan.push_back({main, n});
        if (n % 10 == 0) v67_plan.push_back({it::bruiser_shard_of_health, n / 2});
    }
    return v67_plan;
}
#endif
