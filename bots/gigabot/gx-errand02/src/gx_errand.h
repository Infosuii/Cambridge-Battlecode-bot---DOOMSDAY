#pragma once

#if GX_WAIT_JOB > 0
#if GX_WAIT_PERSIST > 0
bool Bot::gx_finish_errand() {
    if (gx_errand_id < 0) return false;
    auto& g = w.groups[static_cast<std::size_t>(gx_errand_id)];
    const bool active = round < gx_errand_until && g.state != GroupState::respawning &&
        w.enemies.empty() && hp >= max_hp * 0.6f && bc::fuel_remaining() >= 25000 &&
        !group_capture_covered(g);
    if (!active) {
        if (gx_back_id >= 0 && avoid_until[static_cast<std::size_t>(gx_back_id)] <= gx_errand_until)
            avoid_until[static_cast<std::size_t>(gx_back_id)] = round;
        gx_errand_id = gx_back_id = -1;
        return false;
    }
    if (g.state == GroupState::reward) {
        mode = "wait-capture";
        if (bit(g.tiles,pos) || walk_toward(g.tiles)) return true;
    } else if (fight_camps(g,1)) {
        mode = "wait-clear";
        return true;
    }
    gx_errand_id = gx_back_id = -1;
    return false;
}
#endif

bool Bot::gx_wait_job(int incumbent, int wait) {
    if (wait < GX_WAIT_JOB + 7 || hp < max_hp * 0.7f || !w.enemies.empty() ||
        gems >= tune::kTributeCarry || !w.has_field(incumbent) ||
        !rb::fits(6500 + 160 * w.groups.size(), 36000)) return false;
    int best = -1, duration = 0;
    float best_rate = 0.0f;
    for (std::size_t i = 0; i < w.groups.size(); ++i) {
        const int gi = static_cast<int>(i);
        if (gi == incumbent || !w.has_field(gi) || avoid_until[i] > round) continue;
        const auto& g = w.groups[i];
        if (!g.harmless || g.state == GroupState::respawning || g.camps.empty() || g.camps.size() > 6) continue;
#if GX_WAIT_PERSIST > 0
        if ((GX_WAIT_PERSIST >= 2 && g.state != GroupState::reward) || (g.gems < 5 && g.gold < 45)) continue;
#endif
        const int there = w.group_distance(gi, pos);
        if (there > 5 || claim_count(gi) > 0 || group_capture_covered(g)) continue;
        const vec2 endpoint = w.camps[static_cast<std::size_t>(g.camps.front())].pos;
        const int back = w.group_distance(incumbent, endpoint);
        if (back > 10) continue;
        const int kill = static_cast<int>(g.hp_left(w.camps) / std::max(1.0f, my_dps(&g)) + 1.0f);
        const int time = there + kill + capture_time + 3;
        if (time + back + GX_WAIT_JOB > wait) continue;
        const float value = static_cast<float>(g.gems) + gold_weight() * static_cast<float>(g.gold);
        if (value / static_cast<float>(time) > best_rate) {
            best = gi;
            duration = time;
            best_rate = value / static_cast<float>(time);
        }
    }
    if (best < 0 || bc::fuel_remaining() < 34000) return false;
    target_group = best;
    staging_since = staging_walk_since = -1;
    my_claim_since = round;
    write_claim(best);
    avoid_until[static_cast<std::size_t>(incumbent)] = round + std::min(duration, 8);
#if GX_WAIT_PERSIST > 0
    gx_errand_id = best;
    gx_back_id = incumbent;
    gx_errand_until = round + duration + 2;
#endif
    auto& g = w.groups[static_cast<std::size_t>(best)];
    if (g.state == GroupState::reward) {
        mode = "wait-capture";
        if (!bit(g.tiles, pos)) walk_toward(g.tiles);
        return true;
    }
    mode = "wait-clear";
    return fight_camps(g, 1);
}
#endif
