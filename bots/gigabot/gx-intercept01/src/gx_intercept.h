#pragma once

#if GX_BAG_INTERCEPT > 0
bool Bot::gx_intercept() {
    if (w.enemies.empty() || w.allies.empty() || w.altars.empty() || hp < max_hp * 0.74f ||
        gems >= 20 || !rb::fits(7000, 32000) || !bc::self().can_move()) return false;
    const EnemyRec* target = nullptr;
    vec2 cut{};
    int best = 0;
    for (const auto& e : w.enemies) {
        const int here = cheb(pos, e.pos);
        if (e.gems < GX_BAG_INTERCEPT || e.hp <= 0.0f || e.tributing() || e.recalling() ||
            here <= range + 2 || here > 9 || bit(w.enemy_spawn_zone, e.pos)) continue;
        vec2 altar = w.altars.front();
        for (vec2 a : w.altars)
            if (cheb(a, e.pos) < cheb(altar, e.pos)) altar = a;
        vec2 predicted = e.pos;
        for (int t = 1; t <= 3 && cheb(predicted, altar) > 1; ++t) {
            const vec2 step{(altar.x > predicted.x) - (altar.x < predicted.x),
                            (altar.y > predicted.y) - (altar.y < predicted.y)};
            const vec2 p{predicted.x + step.x, predicted.y + step.y};
            if (bit(w.static_blocked, p) || bit(w.enemy_spawn_zone, p)) break;
            predicted = p;
            const int gap = cheb(pos, p) - range;
            if (gap <= 0 || gap > t + 1) continue;
            int friends = 0, foes = 0;
            for (const auto& a : w.allies)
                friends += a.hp >= 0.65f * a.max_hp && cheb(a.pos, p) <= a.range + 2;
            for (const auto& o : w.enemies)
                foes += o.id != e.id && o.hp > 0.0f && cheb(o.pos, p) <= o.range + 2;
            if (!friends || friends <= foes) continue;
            const int rank = std::min(e.gems, 200) - 12 * gap - 5 * t;
            if (rank > best) target = &e, cut = p, best = rank;
        }
    }
    if (!target || bc::fuel_remaining() < 30000) return false;
    bc::bitboard goal;
    goal.clear();
    goal.draw_chebyshev(cut, static_cast<float>(range));
    if (!walk_toward(goal)) return false;
    mode = "bag-intercept";
    if (melee && bc::fuel_remaining() >= 8000 && cheb(pos, target->pos) <= range)
        attack_unit(target->unit, target->pos);
    return true;
}
#endif
