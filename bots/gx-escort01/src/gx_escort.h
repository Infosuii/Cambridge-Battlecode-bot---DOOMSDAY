#pragma once

#if GX_ESCORT > 0
// Called after the normal fight and banking decisions. This move reinforces a
// threatened carrier near us, while leaving the original farm target intact.
bool Bot::gx_escort() {
    if (gems >= 15 || hp < 0.65f * max_hp || w.enemies.empty() || w.allies.empty() ||
        bc::fuel_remaining() < 28000 || !bc::self().can_move()) return false;
    if (target_group >= 0 && target_group < static_cast<int>(w.groups.size())) {
        const auto& g = w.groups[static_cast<std::size_t>(target_group)];
        if (g.state == GroupState::reward && bit(g.tiles, pos)) return false;
    }

    const AllyRec* carrier = nullptr;
    const EnemyRec* pursuer = nullptr;
    int best = 0;
    for (const auto& a : w.allies) {
        const int travel = cheb(pos, a.pos);
        if (travel <= 2 || travel > 6 || a.hp <= 0.0f) continue;
        const EnemyRec* threat = nullptr;
        int nearest = 99, foes = 0;
        for (const auto& e : w.enemies) {
            if (e.hp <= 0.0f || e.tributing() || e.recalling()) continue;
            const int d = cheb(a.pos, e.pos);
            if (d <= 4) ++foes;
            if (d < nearest) nearest = d, threat = &e;
        }
        if (foes == 0) continue;
        int guards = 0;
        bool closer = false;
        for (const auto& b : w.allies) {
            if (b.id == a.id || b.hp < 0.65f * b.max_hp) continue;
            const int d = cheb(a.pos, b.pos);
            guards += d <= 3;
            closer |= d < travel || (d == travel && b.id < my_id);
        }
        if (foes > guards + 2 || guards >= foes || closer) continue;
        std::uint32_t bag = 0;
        if (d::sdk_champion_gems(a.id, &bag) != 0 || bag < GX_ESCORT) continue;
        const int rank = static_cast<int>(std::min(bag, 150u)) - 5 * travel - 4 * nearest;
        if (rank > best || (rank == best && carrier && a.id < carrier->id)) {
            best = rank;
            carrier = &a;
            pursuer = threat;
        }
    }
    if (!carrier) return false;

    bc::bitboard goal;
    goal.clear();
    const int enemy_d = cheb(carrier->pos, pursuer->pos);
    for (int dy = -2; dy <= 2; ++dy)
        for (int dx = -2; dx <= 2; ++dx) {
            if (dx == 0 && dy == 0) continue;
            const vec2 p{carrier->pos.x + dx, carrier->pos.y + dy};
            if (p.x < 0 || p.y < 0 || p.x >= w.width || p.y >= w.height) continue;
            const int d = cheb(p, pursuer->pos);
            if (d <= enemy_d && d + 1 >= enemy_d) set_bit(goal, p);
        }
    if (goal.is_empty() || !walk_toward(goal)) return false;
    mode = "carrier-cover";
    return true;
}
#endif
