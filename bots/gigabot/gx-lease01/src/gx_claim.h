#pragma once

#if GX_CLAIM_ETA > 0
// Return 1 when a visible ally can service the solo job much sooner, 0 when
// we can, or -1 when the normal seniority rule should settle the claim.
int Bot::gx_claim_priority(int gi, int distance) const {
    if (distance == kUnreach || !w.has_field(gi) || !w.enemies.empty()) return -1;
    const auto& g = w.groups[static_cast<std::size_t>(gi)];
    if (!g.harmless && g.state != GroupState::reward) return -1;
    if (target_group == gi && distance <= range && g.state != GroupState::respawning) return 0;
    bool earlier = false, uncertain = false;
    const int my_eta = std::max(distance, g.state == GroupState::respawning ? g.respawn_round - round : 0);
    for (int s = 0; s < std::min(team_size, kClaimSlots); ++s) {
        if (s == slot || s == duo_ignore_slot || claim_of(s) != gi) continue;
        if (claim_onsite(s)) return 1;
        const AllyRec* claimant = nullptr;
        for (const auto& a : w.allies)
            if (a.id == ally_handle[static_cast<std::size_t>(s)]) {
                claimant = &a;
                break;
            }
        if (!claimant) {
            uncertain = true;
            continue;
        }
        const int ally_distance = w.group_distance(gi, claimant->pos);
        if (ally_distance == kUnreach) {
            uncertain = true;
            continue;
        }
        const int ally_eta = std::max(ally_distance, g.state == GroupState::respawning ? g.respawn_round - round : 0);
        if (ally_eta + GX_CLAIM_ETA <= my_eta) return 1;
        if (my_eta + GX_CLAIM_ETA <= ally_eta) earlier = true;
        else uncertain = true;
    }
    return earlier && !uncertain ? 0 : -1;
}
#endif
