#pragma once
#include "plan.h"
#include "kernel.h"
#include "observation.h"
#include "static_world.h"
// Altar-lock denial (DZ_ALTAR_LOCK). Replays of the selected release vs v76 (dz-z14c-base-v76-01): v76 uses ~4.5
// altar locks and 8.5 teleport crystals a game, DZ none. A lock costs 10 gold, stops an opposing tribute at that
// altar and takes five basic attacks to clear (research/elite-meta-2026-10-29/META_TO_ALGORITHM.md).
namespace dz {
#if DZ_HAS(ALTAR_LOCK)
// One lock in the bag, bought at spawn (alive or dead) before gear: it costs 10 gold.
inline void buy_altar_lock(const Observation& obs, const TurnContext& tc, Actuator& act) {
    if (!tc.allow(4000)) return;
    auto& me = cambc::self();
    const auto type = cambc::consumable_type::altar_lock;
    if (me.consumables()[type].count() > 0 || !me.can_buy(type)) return;
    act.attempt([&] { me.buy(type); }, "buy altar lock");
}
// Lock an altar a visible enemy is tributing at, when it is within our lock range and not already ours.
inline bool lock_enemy_tribute(const StaticWorld& world, const Observation& obs, const TurnContext& tc, Actuator& act) {
    if (obs.enemies.empty() || !tc.allow(6000)) return false;
    auto& me = cambc::self();
    const auto type = cambc::consumable_type::altar_lock;
    if (me.consumables()[type].count() == 0) return false;
    const int range = cambc::constants::submit_gems_range;
    for (const auto& e : obs.enemies) {
        if (!e.sdk.is_submitting_gems()) continue;
        for (const auto& altar : world.altars) {
            if (static_cast<int>(e.p.chebyshev_distance(altar.tile)) > range || static_cast<int>(obs.p.chebyshev_distance(altar.tile)) > range) continue;
            bool ours = false;
            for (const auto& lock : cambc::vision::altar_locks(cambc::team::ally)) if (lock.position() == altar.tile) ours = true;
            if (ours) continue;
            const auto tile = altar.tile;
            if (act.attempt([&] { return me.consumables()[type].use(tile); }, "altar lock")) return true;
        }
    }
    return false;
}
#endif
}
