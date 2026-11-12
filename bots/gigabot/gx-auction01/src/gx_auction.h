#pragma once

#if GX_TWO_ASSIGN > 0
int Bot::gx_two_assign(const RouteCand* top, int n, int best) const {
    if (n < 2 || !w.enemies.empty() || !rb::fits(5000, 30000)) return -1;
    const AllyRec* partner = nullptr;
    int near = 8;
    for (const auto& a : w.allies) {
        const int d = cheb(a.pos, pos);
        if (d >= near || a.hp < a.max_hp * 0.65f) continue;
        int s = 0;
        while (s < std::min(team_size,kClaimSlots) && ally_handle[static_cast<std::size_t>(s)] != a.id) ++s;
        if (s == std::min(team_size,kClaimSlots)) continue;
        const int claim = claim_of(s);
        if (claim == static_cast<int>(kClaimCodeDead) || (claim >= 0 && claim < static_cast<int>(w.groups.size()))) {
            if (claim != best || claim_onsite(s)) continue; // partner already has its own work
        }
        near = d;
        partner = &a;
    }
    if (!partner) return -1;

    float other[8]{};
    int own = -1;
    for (int i = 0; i < n; ++i) {
        const auto& c = top[i];
        const auto& g = w.groups[static_cast<std::size_t>(c.gi)];
        if (c.need != 1 || (!g.harmless && g.state != GroupState::reward) || !w.has_field(c.gi)) continue;
        const int d = w.group_distance(c.gi, partner->pos);
        if (d > 14) continue;
        const bool capture = g.state == GroupState::reward;
        const int walk = std::max(0, d - (capture ? 0 : partner->range));
        const int wait = g.state == GroupState::respawning ? std::max(0, g.respawn_round - round - walk) : 0;
        const float clear = g.hp_left(w.camps) / std::max(1.0f, partner->strength);
        other[i] = c.value / (static_cast<float>(walk + wait + capture_time + 4) + clear);
        if (c.gi == best) own = i;
    }
    if (own < 0) return -1;
    auto partner_best = [&](int omit) {
        float rate = 0.0f;
        for (int i = 0; i < n; ++i) if (i != omit) rate = std::max(rate, other[i]);
        return rate;
    };
    const float starting = partner_best(own);
    int pick = -1;
    float best_gain = 0.0f;
    for (int i = 0; i < n; ++i) {
        if (i == own || other[i] <= 0.0f || top[i].score < top[own].score * (GX_TWO_ASSIGN * 0.01f)) continue;
        const float own_loss = std::max(0.0f, top[own].score - top[i].score);
        const float gain = partner_best(i) - starting - 1.4f * own_loss;
        if (gain > best_gain) pick = i, best_gain = gain;
    }
    return pick;
}
#endif
