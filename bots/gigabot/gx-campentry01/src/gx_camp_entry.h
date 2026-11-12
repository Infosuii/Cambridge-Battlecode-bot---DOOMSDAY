#pragma once

#if GX_CAMP_ENTRY > 0
namespace {
volatile unsigned gx_entry_action = 1000u + GX_ENTRY_ACT;
}

[[gnu::noinline]] bool Bot::gx_entry_angle(const GroupRec& g, const bc::bitboard& goal) {
    if (g.harmless || g.camps.size() < 2 || g.camps.size() > 32 ||
        bit(goal,pos) || !w.enemies.empty() || w.bridges_on ||
        !rb::fits(1500 + 450 * g.camps.size(),22000)) return false;
    vec2 old = pos, best = pos;
    float old_soak = 0.0f, best_soak = 1e30f;
    int old_order = 3, best_order = 3;
    for (const auto dir : kDirs) {
        const auto at = pos + dir;
        if (!in_bounds(at,w.width,w.height) || !bit(goal,at) ||
            bit(w.static_blocked,at) || bit(w.unit_tiles,at)) continue;
        bool shot = false;
        float soak = 0.0f;
        for (const int i : g.camps) {
            const auto& c = w.camps[static_cast<std::size_t>(i)];
            if (c.dead) continue;
            const int dist = cheb(c.pos,at);
            if (dist <= c.range) soak += c.strength;
            if (dist <= range && bit(w.visible,c.pos)) shot = true;
        }
        const int order = dir.x && dir.y ? 0 : 1;
        if (order < old_order) old = at, old_soak = soak, old_order = order;
        if (shot && (soak < best_soak || (soak == best_soak && order < best_order)))
            best = at, best_soak = soak, best_order = order;
    }
    if (old == pos || best == pos || old == best || old_soak <= 0 || best_soak > old_soak * 0.72f ||
        !bc::self().can_move()) return false;
    if (gx_entry_action == 1000u) return false;
    try {
        if (bc::self().move_absolute(best)) {
            pos = best;
            walked = true;
            walk_unreachable = walk_boxed = false;
            return true;
        }
    } catch (const std::exception&) {
        // Movement can reveal a hidden blocker; let the normal path decide.
    }
    return false;
}
#endif
