#pragma once

#if GX_FIRST_JOB > 0
// Opening-only fallback when the group distance fields have not been built.
bool Bot::gx_first_job() {
    if (field_calls != 0 || round != 1 || !w.enemies.empty() ||
        !rb::fits(6000 + w.groups.size() * 200, 42000)) return false;
    int best = -1;
    float best_rate = 0.0f;
    for (std::size_t i = 0; i < w.groups.size(); ++i) {
        const auto& g = w.groups[i];
        if (!g.harmless || g.state != GroupState::alive || g.camps.empty() || g.camps.size() > 6 ||
            claim_count(static_cast<int>(i)) > 0) continue;
        const auto& c = w.camps[static_cast<std::size_t>(g.camps.front())];
        const int walk = std::max<int>(cheb(c.pos, pos), fdist(w.spawn_field, c.pos));
        if (walk > GX_FIRST_JOB) continue;
        const float value = static_cast<float>(g.gold) + 3.0f * static_cast<float>(g.gems);
        const float turns = static_cast<float>(walk + capture_time + 4) + g.max_hp / std::max(1.0f, strength);
        const float rate = value / turns;
        if (rate > best_rate) best = static_cast<int>(i), best_rate = rate;
    }
    if (best < 0 || bc::fuel_remaining() < 40000) return false;
    target_group = best;
    my_claim_since = round;
    write_claim(best);
    return fight_camps(w.groups[static_cast<std::size_t>(best)], 1);
}
#endif
